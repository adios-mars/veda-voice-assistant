"""Language Model (LLM) orchestration interface."""
from abc import ABC, abstractmethod
import time
from typing import List, Dict, Optional

import openai
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
        self.api_key = api_key or config.openai_api_key
        self.model = model or config.openai_model
        if not self.api_key or self.api_key.startswith("your_"):
            raise ValueError("Valid OPENAI_API_KEY is required in .env")
        self.client = openai.Client(api_key=self.api_key)

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


class EchoFallbackLLM(BaseLLM):
    """Simulated smart response provider when no external LLM API key is present."""

    def generate_reply(self, history: List[Dict[str, str]], prompt: str) -> str:
        logger.warning("Using Fallback LLM (no OpenAI API key configured).")
        p = prompt.lower()
        if "hello" in p or "hi" in p:
            return "Good day! All systems online and operational. How can I assist you, sir?"
        elif "who are you" in p:
            return "I am JARVIS, your personal voice-activated artificial intelligence."
        elif "time" in p:
            return f"The current system time is {time.strftime('%I:%M %p')}."
        return f"Understood, sir. You said: '{prompt}'. Standing by for your command."


def get_llm_service() -> BaseLLM:
    """Factory creating the appropriate LLM service instance."""
    if config.openai_api_key and not config.openai_api_key.startswith("your_"):
        try:
            return OpenAILLM()
        except Exception as e:
            logger.warning(f"Could not initialize OpenAI ({e}), using Fallback.")
    return EchoFallbackLLM()
