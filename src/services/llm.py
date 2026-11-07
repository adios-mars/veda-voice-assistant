"""Language Model (LLM) orchestration interface."""
from abc import ABC, abstractmethod
import time
from typing import List, Dict, Optional

from src.config import config
from src.logger import get_logger

logger = get_logger("LLM")


class BaseLLM(ABC):
    """Abstract interface for LLM providers."""

    @abstractmethod
    def generate_reply(self, history: List[Dict[str, str]], prompt: str) -> str:
        """Generates conversational response given conversation history and current prompt."""
        pass


class OpenAILLM(BaseLLM):
    """OpenAI GPT implementation."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        import openai as _openai
        self.api_key = api_key or config.openai_api_key
        self.model = model or config.openai_model
        if not self.api_key or self.api_key.startswith("your_"):
            raise ValueError("Valid OPENAI_API_KEY is required in .env")
        self.client = _openai.Client(api_key=self.api_key)

    def generate_reply(self, history: List[Dict[str, str]], prompt: str) -> str:
        messages = [{"role": "system", "content": config.system_prompt}]
        messages.extend(history)
        messages.append({"role": "user", "content": prompt})

        start = time.perf_counter()
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=150,
            temperature=0.7,
        )
        elapsed = time.perf_counter() - start
        content = response.choices[0].message.content or ""
        logger.info(f"Generated reply via {self.model} in {elapsed:.2f}s: \"{content}\"")
        return content.strip()


class GeminiLLM(BaseLLM):
    """Google Gemini implementation with automatic multi-model failover across quota tiers."""

    FALLBACK_MODELS = [
        "gemini-3.5-flash-lite",
        "gemini-3.1-flash-lite",
        "gemma-4-26b-a4b-it",
        "gemini-2.5-flash",
    ]

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        from google import genai
        self.api_key = api_key or config.gemini_api_key
        initial_model = model or config.gemini_model
        if not self.api_key or self.api_key.startswith("your_"):
            raise ValueError("Valid GEMINI_API_KEY is required in .env")
        self._client = genai.Client(
            api_key=self.api_key,
            http_options={"api_version": "v1beta"}
        )
        # Order model list prioritizing initial_model
        self._models = [initial_model] + [m for m in self.FALLBACK_MODELS if m != initial_model]
        self._current_model_idx = 0
        self._chat = None
        self._current_model = None
        self._init_chat(self._models[0])

    def _init_chat(self, model_name: str):
        try:
            self._chat = self._client.chats.create(
                model=model_name,
                config={"system_instruction": config.system_prompt},
            )
            self._current_model = model_name
            logger.info(f"Gemini LLM active with model '{model_name}'.")
        except Exception as e:
            logger.warning(f"Could not initialize chat on {model_name}: {e}")
            self._chat = None

    def generate_reply(self, history: List[Dict[str, str]], prompt: str) -> str:
        import re
        start = time.perf_counter()

        for offset in range(len(self._models)):
            idx = (self._current_model_idx + offset) % len(self._models)
            model_name = self._models[idx]

            try:
                if self._current_model != model_name or self._chat is None:
                    self._init_chat(model_name)
                    if self._chat is None:
                        continue

                response = self._chat.send_message(prompt)
                raw = response.text or ""
                # Strip markdown symbols so speech synthesis is clean and natural
                content = re.sub(r"[\*#_`]", "", raw).strip()
                elapsed = time.perf_counter() - start
                logger.info(f"Gemini reply via {model_name} in {elapsed:.2f}s: \"{content}\"")
                # Remember working model index
                self._current_model_idx = idx
                return content
            except Exception as e:
                err_msg = str(e)
                if any(code in err_msg for code in ["429", "503", "RESOURCE_EXHAUSTED", "UNAVAILABLE"]):
                    logger.warning(f"Model '{model_name}' hit quota/busy spike ({err_msg[:60]}...). Switching to next model...")
                    continue
                else:
                    logger.error(f"Gemini error with {model_name}: {e}")
                    continue

        return "I apologize, sir. I experienced a momentary communication disruption."


class EchoFallbackLLM(BaseLLM):
    """Simulated smart response provider when no external LLM API key is present."""

    def generate_reply(self, history: List[Dict[str, str]], prompt: str) -> str:
        logger.warning("No LLM API key configured — add GEMINI_API_KEY to .env for real AI responses.")
        p = prompt.lower()
        if "hello" in p or "hi" in p:
            return "Good day! All systems online and operational. How can I assist you, sir?"
        elif "who are you" in p:
            return "I am JARVIS, your personal voice-activated artificial intelligence."
        elif "time" in p:
            return f"The current system time is {time.strftime('%I:%M %p')}."
        return f"Understood, sir. You said: '{prompt}'. Standing by for your command."


def _is_placeholder(key: str) -> bool:
    """Returns True if the key looks like a template placeholder, not a real credential."""
    return not key or key.startswith("your_") or key.endswith("...") or key == "sk-proj-..."


def get_llm_service() -> BaseLLM:
    """Factory: Gemini (free) → OpenAI → Echo fallback."""
    # 1. Try Google Gemini (free tier)
    if not _is_placeholder(config.gemini_api_key):
        try:
            return GeminiLLM()
        except Exception as e:
            logger.warning(f"Gemini init failed ({e}), trying OpenAI...")

    # 2. Try OpenAI
    if not _is_placeholder(config.openai_api_key):
        try:
            return OpenAILLM()
        except Exception as e:
            logger.warning(f"OpenAI init failed ({e}), falling back to echo.")

    # 3. Echo fallback (no real AI)
    return EchoFallbackLLM()
