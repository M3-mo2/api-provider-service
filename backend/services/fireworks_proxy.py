"""
Fireworks API Proxy Service
Handles requests to Fireworks.ai with streaming support
"""

import httpx
import json
import time
from typing import AsyncGenerator, Dict, Any, Optional
from backend.config import config


class FireworksProxy:
    """Proxy service for Fireworks.ai API"""

    def __init__(self):
        self.base_url = config.get(
            "fireworks.base_url", "https://api.fireworks.ai/inference/v1"
        )
        self.timeout = config.get("fireworks.timeout", 300)
        self.max_retries = config.get("fireworks.max_retries", 3)

    async def chat_completion(
        self, api_key: str, data: Dict[str, Any], stream: bool = False
    ) -> tuple[Optional[Dict], Optional[AsyncGenerator], int, Optional[str]]:
        """
        Send chat completion request to Fireworks
        Returns: (response_data, stream_generator, status_code, error_message)
        """
        url = f"{self.base_url}/chat/completions"

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                if stream:
                    # Streaming response
                    response = await client.post(url, json=data, headers=headers)

                    if response.status_code != 200:
                        error_text = response.text
                        return None, None, response.status_code, error_text

                    async def stream_generator():
                        async for line in response.aiter_lines():
                            if line.strip():
                                if line.startswith("data: "):
                                    yield line + "\n\n"

                    return None, stream_generator(), response.status_code, None
                else:
                    # Non-streaming response
                    response = await client.post(url, json=data, headers=headers)

                    if response.status_code == 200:
                        return response.json(), None, response.status_code, None
                    else:
                        return None, None, response.status_code, response.text

        except httpx.TimeoutException:
            return None, None, 504, "Request timeout"
        except Exception as e:
            return None, None, 500, str(e)

    async def completion(
        self, api_key: str, data: Dict[str, Any], stream: bool = False
    ) -> tuple[Optional[Dict], Optional[AsyncGenerator], int, Optional[str]]:
        """
        Send completion request to Fireworks
        Returns: (response_data, stream_generator, status_code, error_message)
        """
        url = f"{self.base_url}/completions"

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                if stream:
                    response = await client.post(url, json=data, headers=headers)

                    if response.status_code != 200:
                        return None, None, response.status_code, response.text

                    async def stream_generator():
                        async for line in response.aiter_lines():
                            if line.strip():
                                if line.startswith("data: "):
                                    yield line + "\n\n"

                    return None, stream_generator(), response.status_code, None
                else:
                    response = await client.post(url, json=data, headers=headers)

                    if response.status_code == 200:
                        return response.json(), None, response.status_code, None
                    else:
                        return None, None, response.status_code, response.text

        except httpx.TimeoutException:
            return None, None, 504, "Request timeout"
        except Exception as e:
            return None, None, 500, str(e)

    async def anthropic_messages(
        self, api_key: str, data: Dict[str, Any], stream: bool = False
    ) -> tuple[Optional[Dict], Optional[AsyncGenerator], int, Optional[str]]:
        """
        Send Anthropic-compatible messages request to Fireworks
        Returns: (response_data, stream_generator, status_code, error_message)
        """
        # Fireworks uses /inference/v1/messages for Anthropic compatibility
        url = "https://api.fireworks.ai/inference/v1/messages"

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                if stream:
                    response = await client.post(url, json=data, headers=headers)

                    if response.status_code != 200:
                        return None, None, response.status_code, response.text

                    async def stream_generator():
                        async for line in response.aiter_lines():
                            if line.strip():
                                yield line + "\n\n"

                    return None, stream_generator(), response.status_code, None
                else:
                    response = await client.post(url, json=data, headers=headers)

                    if response.status_code == 200:
                        return response.json(), None, response.status_code, None
                    else:
                        return None, None, response.status_code, response.text

        except httpx.TimeoutException:
            return None, None, 504, "Request timeout"
        except Exception as e:
            return None, None, 500, str(e)

    def extract_token_usage(
        self, response_data: Dict[str, Any]
    ) -> tuple[int, int, int]:
        """
        Extract token usage from response
        Returns: (input_tokens, output_tokens, total_tokens)
        """
        if not response_data:
            return 0, 0, 0

        usage = response_data.get("usage", {})

        # OpenAI format
        if "prompt_tokens" in usage:
            input_tokens = usage.get("prompt_tokens", 0)
            output_tokens = usage.get("completion_tokens", 0)
            total_tokens = usage.get("total_tokens", input_tokens + output_tokens)
            return input_tokens, output_tokens, total_tokens

        # Anthropic format
        if "input_tokens" in usage:
            input_tokens = usage.get("input_tokens", 0)
            output_tokens = usage.get("output_tokens", 0)
            total_tokens = input_tokens + output_tokens
            return input_tokens, output_tokens, total_tokens

        return 0, 0, 0


# Global proxy instance
proxy = FireworksProxy()
