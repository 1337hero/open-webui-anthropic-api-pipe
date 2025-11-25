"""
title: Anthropic Claude API
author: 1337Hero (Mike Key)
version: 2.1.0
license: MIT
required_open_webui_version: 0.5.0
requirements: requests>=2.31.0

A clean, simple Anthropic Claude integration that does exactly what's needed.
Security by default, not security theater.

Features:
- Dynamic model list: Fetches available models from Anthropic's /v1/models API
- Auto-refresh: Configurable refresh interval (default: 1 hour)
- Graceful fallback: Uses cached/fallback models if API is unavailable

Environment Variables:
- ANTHROPIC_API_KEY (required): Your Anthropic API key

Configuration:
- MODEL_REFRESH_INTERVAL: Seconds between model list refreshes (default: 3600, 0 to disable)
"""

import os
import json
import logging
import time
from typing import Generator, Union, Dict, Any, List, Optional
from urllib.parse import urlparse
from ipaddress import ip_address, ip_network

import requests
from pydantic import BaseModel, Field
from open_webui.utils.misc import pop_system_message


class Pipe:
    """Clean Anthropic Claude API integration."""

    # Security: Block private networks for URL images (actual SSRF protection)
    PRIVATE_NETWORKS = [
        ip_network("127.0.0.0/8"),
        ip_network("10.0.0.0/8"),
        ip_network("172.16.0.0/12"),
        ip_network("192.168.0.0/16"),
        ip_network("169.254.0.0/16"),
        ip_network("::1/128"),
        ip_network("fc00::/7"),
    ]

    class Valves(BaseModel):
        """Simple configuration - just the essentials."""
        ANTHROPIC_API_KEY: str = Field(
            default="",
            description="Your Anthropic API key"
        )
        MODEL_REFRESH_INTERVAL: int = Field(
            default=3600,
            description="How often to refresh model list from API (seconds). Set to 0 to disable auto-refresh."
        )

    # Fallback models when API is unavailable
    FALLBACK_MODELS = [
        {"id": "claude-sonnet-4-5-20250929", "name": "Claude Sonnet 4.5"},
        {"id": "claude-haiku-4-5-20251001", "name": "Claude Haiku 4.5"},
        {"id": "claude-opus-4-1-20250805", "name": "Claude Opus 4.1"},
        {"id": "claude-3-7-sonnet-20250219", "name": "Claude 3.7 Sonnet"},
        {"id": "claude-3-5-sonnet-20241022", "name": "Claude 3.5 Sonnet"},
        {"id": "claude-3-5-haiku-20241022", "name": "Claude 3.5 Haiku"},
        {"id": "claude-3-opus-20240229", "name": "Claude 3 Opus"},
        {"id": "claude-3-sonnet-20240229", "name": "Claude 3 Sonnet"},
        {"id": "claude-3-haiku-20240307", "name": "Claude 3 Haiku"},
    ]

    def __init__(self):
        self.name = "Anthropic Claude"
        self.valves = self.Valves(
            **{"ANTHROPIC_API_KEY": os.getenv("ANTHROPIC_API_KEY", "")}
        )
        self.timeout = 60
        self.logger = logging.getLogger(__name__)

        # Model cache
        self._cached_models: Optional[List[Dict[str, str]]] = None
        self._cache_timestamp: float = 0

    def pipes(self) -> List[Dict[str, str]]:
        """Return available Claude models, fetched dynamically from Anthropic API."""
        # Check if cache is valid
        if self._is_cache_valid():
            return self._cached_models

        # Try to fetch fresh models
        models = self._fetch_models_from_api()

        if models:
            self._cached_models = models
            self._cache_timestamp = time.time()
            return models

        # Return cached models if available, otherwise fallback
        if self._cached_models:
            self.logger.warning("Using stale cached models (API unavailable)")
            return self._cached_models

        self.logger.warning("Using fallback models (API unavailable)")
        return self.FALLBACK_MODELS

    def _is_cache_valid(self) -> bool:
        """Check if the model cache is still valid."""
        if not self._cached_models:
            return False

        refresh_interval = self.valves.MODEL_REFRESH_INTERVAL
        if refresh_interval <= 0:
            # Auto-refresh disabled, cache never expires
            return True

        age = time.time() - self._cache_timestamp
        return age < refresh_interval

    def _fetch_models_from_api(self) -> Optional[List[Dict[str, str]]]:
        """Fetch available models from Anthropic's API."""
        if not self.valves.ANTHROPIC_API_KEY:
            return None

        try:
            response = requests.get(
                "https://api.anthropic.com/v1/models",
                headers={
                    "x-api-key": self.valves.ANTHROPIC_API_KEY,
                    "anthropic-version": "2023-06-01",
                },
                timeout=10
            )
            response.raise_for_status()
            data = response.json()

            models = []
            for model in data.get("data", []):
                model_id = model.get("id", "")
                display_name = model.get("display_name", model_id)

                # Skip non-Claude models if any
                if not model_id.startswith("claude"):
                    continue

                models.append({
                    "id": model_id,
                    "name": display_name
                })

            if models:
                self.logger.info(f"Fetched {len(models)} models from Anthropic API")
                return models

        except requests.exceptions.RequestException as e:
            self.logger.warning(f"Failed to fetch models from API: {e}")
        except (KeyError, ValueError) as e:
            self.logger.warning(f"Failed to parse models response: {e}")

        return None

    def pipe(self, body: Dict[str, Any]) -> Union[str, Generator[str, None, None]]:
        """Process request and return Claude's response."""
        try:
            # Validate we have an API key
            if not self.valves.ANTHROPIC_API_KEY:
                return "Error: ANTHROPIC_API_KEY not configured. Add your API key in the pipeline settings."

            # Extract model ID (handle Open WebUI's prefix)
            model_id = self._extract_model_id(body.get("model", ""))

            # Get messages and extract system prompt
            messages = body.get("messages", [])
            system_message, user_messages = pop_system_message(messages)

            # Process messages (handles images securely)
            processed_messages = self._process_messages(user_messages)

            # Build request payload
            payload = {
                "model": model_id,
                "messages": processed_messages,
                "max_tokens": body.get("max_tokens", 4096),
                "stream": body.get("stream", False),
            }

            # Add system message if present
            if system_message:
                payload["system"] = str(system_message)

            # Add optional parameters (only if present)
            for param in ["temperature", "top_p", "top_k"]:
                if param in body:
                    payload[param] = body[param]

            # Make API request
            response = self._call_api(payload)

            # Return streaming or complete response
            if body.get("stream", False):
                return self._stream_response(response)
            else:
                return self._parse_response(response)

        except requests.exceptions.RequestException as e:
            error_msg = self._safe_error_message(e)
            self.logger.error(f"API request failed: {e}")
            return f"Error: {error_msg}"

        except ValueError as e:
            # User-facing validation errors
            self.logger.info(f"Validation error: {e}")
            return f"Error: {str(e)}"

        except Exception as e:
            # Unexpected errors - log details but don't expose them
            self.logger.error(f"Unexpected error: {type(e).__name__}: {e}", exc_info=True)
            return "Error: Something went wrong. Please try again."

    def _extract_model_id(self, full_model_id: str) -> str:
        """Extract Claude model ID from Open WebUI's prefixed format."""
        if "." in full_model_id:
            # Format: pipe_name.claude-sonnet-4-5-20250929
            return full_model_id.split(".", 1)[-1]
        elif "/" in full_model_id:
            # Format: pipe_name/claude-sonnet-4-5-20250929
            return full_model_id.split("/", 1)[-1]
        return full_model_id

    def _process_messages(self, messages: List[Dict]) -> List[Dict]:
        """Process messages and handle multimodal content securely."""
        processed = []

        for message in messages:
            content = message.get("content", "")

            # Simple text message
            if isinstance(content, str):
                processed.append({
                    "role": message["role"],
                    "content": content
                })

            # Multimodal message (text + images)
            elif isinstance(content, list):
                processed_content = []

                for item in content:
                    if item.get("type") == "text":
                        processed_content.append({
                            "type": "text",
                            "text": item.get("text", "")
                        })

                    elif item.get("type") == "image_url":
                        # Process image with security validation
                        image = self._process_image(item)
                        if image:
                            processed_content.append(image)

                if processed_content:
                    processed.append({
                        "role": message["role"],
                        "content": processed_content
                    })

        return processed

    def _process_image(self, image_data: Dict) -> Dict:
        """Process image with basic security validation."""
        url = image_data.get("image_url", {}).get("url", "")

        # Handle base64 images (safe - no network request)
        if url.startswith("data:image"):
            try:
                mime_type, base64_data = url.split(",", 1)
                media_type = mime_type.split(":")[1].split(";")[0]

                # Basic size check (5MB limit from Anthropic)
                size_mb = len(base64_data) * 3 / 4 / (1024 * 1024)
                if size_mb > 5:
                    raise ValueError(f"Image too large: {size_mb:.1f}MB (max 5MB)")

                return {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": media_type,
                        "data": base64_data
                    }
                }
            except Exception as e:
                self.logger.warning(f"Failed to process base64 image: {e}")
                return None

        # Handle URL images (requires SSRF validation)
        elif url.startswith("http"):
            if self._is_safe_url(url):
                return {
                    "type": "image",
                    "source": {
                        "type": "url",
                        "url": url
                    }
                }
            else:
                self.logger.warning(f"Blocked potentially unsafe URL: {url}")
                raise ValueError("Image URL blocked for security reasons")

        return None

    def _is_safe_url(self, url: str) -> bool:
        """Validate URL to prevent SSRF attacks."""
        try:
            parsed = urlparse(url)

            # Only HTTPS allowed
            if parsed.scheme != "https":
                return False

            # Block localhost and metadata endpoints
            hostname = parsed.hostname
            if not hostname:
                return False

            blocked_hosts = ["localhost", "metadata.google.internal", "169.254.169.254"]
            if any(blocked in hostname.lower() for blocked in blocked_hosts):
                return False

            # Check if it's an IP address and block private ranges
            try:
                ip = ip_address(hostname)
                for network in self.PRIVATE_NETWORKS:
                    if ip in network:
                        return False
            except ValueError:
                # Not an IP, it's a domain - that's fine
                pass

            return True

        except Exception:
            return False

    def _call_api(self, payload: Dict) -> requests.Response:
        """Make request to Anthropic API with retry logic."""
        headers = {
            "x-api-key": self.valves.ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }

        # Simple retry logic for transient failures
        for attempt in range(3):
            try:
                response = requests.post(
                    "https://api.anthropic.com/v1/messages",
                    headers=headers,
                    json=payload,
                    timeout=self.timeout,
                    stream=payload.get("stream", False)
                )

                # Let non-retryable errors through immediately
                if response.status_code in [400, 401, 403]:
                    response.raise_for_status()

                # Retry on rate limits and server errors
                if response.status_code in [429, 500, 502, 503, 504]:
                    if attempt < 2:  # Don't sleep on last attempt
                        import time
                        time.sleep(2 ** attempt)  # Exponential backoff
                        continue

                response.raise_for_status()
                return response

            except requests.exceptions.Timeout:
                if attempt < 2:
                    continue
                raise

        # If we get here, all retries failed
        raise requests.exceptions.RequestException("Max retries exceeded")

    def _stream_response(self, response: requests.Response) -> Generator[str, None, None]:
        """Stream response from Anthropic API."""
        try:
            for line in response.iter_lines():
                if line:
                    line_text = line.decode("utf-8")

                    if line_text.startswith("data: "):
                        data_str = line_text[6:]

                        if data_str == "[DONE]":
                            break

                        try:
                            data = json.loads(data_str)

                            # Extract text from content deltas
                            if data.get("type") == "content_block_delta":
                                delta = data.get("delta", {})
                                if delta.get("type") == "text_delta":
                                    yield delta.get("text", "")

                            # Stop on message completion
                            elif data.get("type") == "message_stop":
                                break

                        except json.JSONDecodeError:
                            continue

        except Exception as e:
            self.logger.error(f"Streaming error: {e}")
            yield "\n\nError: Stream interrupted."

    def _parse_response(self, response: requests.Response) -> str:
        """Parse non-streaming response."""
        data = response.json()

        # Extract text content
        content_blocks = data.get("content", [])
        text_blocks = [
            block.get("text", "")
            for block in content_blocks
            if block.get("type") == "text"
        ]

        return "".join(text_blocks) if text_blocks else "No response generated"

    def _safe_error_message(self, error: Exception) -> str:
        """Convert exception to safe user-facing error message."""
        if isinstance(error, requests.exceptions.Timeout):
            return "Request timed out. Please try again."

        if isinstance(error, requests.exceptions.HTTPError):
            status = error.response.status_code
            if status == 401:
                return "Invalid API key. Check your ANTHROPIC_API_KEY."
            elif status == 429:
                return "Rate limit exceeded. Please wait a moment."
            elif status >= 500:
                return "Anthropic API is temporarily unavailable."
            else:
                return "API request failed."

        if isinstance(error, requests.exceptions.ConnectionError):
            return "Cannot connect to Anthropic API."

        return "Request failed. Please try again."
