"""AI provider implementations"""
import logging
from abc import ABC, abstractmethod
import requests

logger = logging.getLogger(__name__)


class AIProvider(ABC):
    """Abstract base class for AI providers"""

    @abstractmethod
    async def get_response(self, user_message: str, conversation_history: list) -> str:
        """Get response from AI provider"""
        pass


class GeminiProvider(AIProvider):
    """Google Gemini AI Provider"""

    def __init__(self, api_key: str, system_prompt: str):
        self.api_key = api_key
        self.system_prompt = system_prompt
        self.model = "gemini-1.5-flash"

    async def get_response(self, user_message: str, conversation_history: list) -> str:
        """Get response from Gemini"""
        try:
            import google.generativeai as genai

            genai.configure(api_key=self.api_key)
            model = genai.GenerativeModel(self.model)

            # Build messages with system prompt context
            chat_history = [
                {
                    "role": "user" if msg["role"] == "user" else "model",
                    "parts": [msg["content"]]
                }
                for msg in conversation_history[-10:]
            ]

            chat = model.start_chat(history=chat_history)
            response = chat.send_message(user_message, stream=False)

            logger.info(f"✅ Gemini response generated")
            return response.text

        except Exception as e:
            logger.error(f"Gemini error: {e}")
            return f"Error: {str(e)}"


class MistralProvider(AIProvider):
    """Mistral AI Provider"""

    def __init__(self, api_key: str, system_prompt: str):
        self.api_key = api_key
        self.system_prompt = system_prompt
        self.model = "mistral-small-latest"
        self.api_url = "https://api.mistral.ai/v1/chat/completions"

    async def get_response(self, user_message: str, conversation_history: list) -> str:
        """Get response from Mistral"""
        try:
            messages = [
                {"role": "system", "content": self.system_prompt},
                *conversation_history[-10:],
                {"role": "user", "content": user_message}
            ]

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            payload = {
                "model": self.model,
                "messages": messages,
                "max_tokens": 1024,
                "temperature": 0.7
            }

            response = requests.post(self.api_url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()

            result = response.json()
            assistant_message = result["choices"][0]["message"]["content"]

            logger.info(f"✅ Mistral response generated")
            return assistant_message

        except Exception as e:
            logger.error(f"Mistral error: {e}")
            return f"Error: {str(e)}"


class CerebrasProvider(AIProvider):
    """Cerebras AI Provider"""

    def __init__(self, api_key: str, system_prompt: str):
        self.api_key = api_key
        self.system_prompt = system_prompt
        self.model = "llama-3.1-8b"
        self.api_url = "https://api.cerebras.ai/v1/chat/completions"

    async def get_response(self, user_message: str, conversation_history: list) -> str:
        """Get response from Cerebras"""
        try:
            messages = [
                {"role": "system", "content": self.system_prompt},
                *conversation_history[-10:],
                {"role": "user", "content": user_message}
            ]

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            payload = {
                "model": self.model,
                "messages": messages,
                "max_tokens": 1024,
                "temperature": 0.7
            }

            response = requests.post(self.api_url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()

            result = response.json()
            assistant_message = result["choices"][0]["message"]["content"]

            logger.info(f"✅ Cerebras response generated")
            return assistant_message

        except Exception as e:
            logger.error(f"Cerebras error: {e}")
            return f"Error: {str(e)}"


def get_ai_provider(provider_name: str, api_key: str, system_prompt: str) -> AIProvider:
    """Factory function to get AI provider"""
    provider_name = provider_name.lower()

    if provider_name == "gemini":
        return GeminiProvider(api_key, system_prompt)
    elif provider_name == "mistral":
        return MistralProvider(api_key, system_prompt)
    elif provider_name == "cerebras":
        return CerebrasProvider(api_key, system_prompt)
    else:
        raise ValueError(f"Unknown AI provider: {provider_name}")
