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
    """Google Gemini implementation (free tier via AI Studio key)."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        from google import genai
        self.api_key = api_key or config.gemini_api_key
        self.model = model or config.gemini_model
        if not self.api_key or self.api_key.startswith("your_"):
            raise ValueError("Valid GEMINI_API_KEY is required in .env")
        self._client = genai.Client(
            api_key=self.api_key,
            http_options={"api_version": "v1beta"}
        )
        # Persistent chat session keeps conversation context across turns
        self._chat = self._client.chats.create(
            model=self.model,
            config={"system_instruction": config.system_prompt},
        )
        logger.info(f"Gemini LLM initialised with model '{self.model}'.")

    def generate_reply(self, history: List[Dict[str, str]], prompt: str) -> str:
        start = time.perf_counter()
        response = self._chat.send_message(prompt)
        elapsed = time.perf_counter() - start
        content = response.text.strip()
        logger.info(f"Gemini reply in {elapsed:.2f}s: \"{content}\"")
        return content


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
