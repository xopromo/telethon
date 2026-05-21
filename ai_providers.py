"""AI provider implementations with failover support"""
import logging
from abc import ABC, abstractmethod
import requests

logger = logging.getLogger(__name__)

# Store last working provider
_last_working_provider = None


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
            raise  # Re-raise so AIProviderChain switches to next provider


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
            raise  # Re-raise so AIProviderChain switches to next provider


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


class AIProviderChain:
    """Multi-provider with automatic failover"""

    def __init__(self, providers_config: list, system_prompt: str):
        """
        providers_config: list of tuples (provider_name, api_key)
        Example: [('mistral', 'key1'), ('gemini', 'key2'), ('cerebras', 'key3')]
        """
        self.providers = []
        self.system_prompt = system_prompt

        for provider_name, api_key in providers_config:
            if api_key and api_key != 'None':
                try:
                    provider = get_ai_provider(provider_name, api_key, system_prompt)
                    self.providers.append((provider_name, provider))
                    logger.info(f"✅ Loaded {provider_name} provider")
                except Exception as e:
                    logger.warning(f"⚠️  Failed to load {provider_name}: {e}")

        if not self.providers:
            raise ValueError("No valid AI providers configured!")

        logger.info(f"📋 Provider chain: {[p[0] for p in self.providers]}")

    async def get_response(self, user_message: str, conversation_history: list) -> str:
        """Try providers in order, fallback to next on failure"""
        last_error = None

        for provider_name, provider in self.providers:
            try:
                logger.info(f"🤖 Trying {provider_name}...")
                response = await provider.get_response(user_message, conversation_history)
                logger.info(f"✅ {provider_name} succeeded")
                return response
            except Exception as e:
                logger.warning(f"❌ {provider_name} failed: {e}")
                last_error = e
                continue

        # All providers failed
        error_msg = f"All providers failed. Last error: {str(last_error)}"
        logger.error(error_msg)
        return f"Sorry, all AI providers are unavailable: {str(last_error)}"
