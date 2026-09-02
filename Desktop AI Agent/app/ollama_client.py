"""Ollama API Client for Local Qwen Model."""

import json
import urllib.request
import urllib.error
from typing import Any, Dict, List, Optional, Tuple


class OllamaClient:
    """Client for local Ollama server API."""

    def __init__(self, base_url: str = "http://localhost:11434", default_model: str = "qwen2.5:3b"):
        self.base_url = base_url.rstrip("/")
        self.default_model = default_model

    def check_health(self) -> Tuple[bool, str, List[str]]:
        """
        Check if Ollama server is running and get list of available models.
        Returns:
            (is_healthy: bool, message: str, models: list[str])
        """
        url = f"{self.base_url}/api/tags"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Desktop-AI-Agent"})
            with urllib.request.urlopen(req, timeout=4) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode("utf-8"))
                    models = [m.get("name", "") for m in data.get("models", []) if m.get("name")]
                    return True, "Ollama is running", models
                return False, f"Ollama returned HTTP status {response.status}", []
        except urllib.error.URLError as e:
            return False, f"Cannot connect to Ollama at {self.base_url}: {e.reason}", []
        except Exception as e:
            return False, f"Ollama health check error: {str(e)}", []

    def is_model_available(self, model_name: Optional[str] = None) -> bool:
        """Check if a specific model or default model is pulled in Ollama."""
        target = model_name or self.default_model
        healthy, _, models = self.check_health()
        if not healthy:
            return False
        
        # Check exact or prefix match (e.g. qwen2.5:3b vs qwen2.5:3b-instruct)
        for m in models:
            if m == target or m.split(":")[0] == target.split(":")[0]:
                return True
        return False

    def chat(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        model: Optional[str] = None,
        temperature: float = 0.2,
        context_length: int = 8192,
    ) -> Dict[str, Any]:
        """
        Send chat completion request to Ollama /api/chat.
        Returns dict with keys: 'content', 'tool_calls', 'raw_response'.
        """
        model_name = model or self.default_model
        url = f"{self.base_url}/api/chat"

        payload: Dict[str, Any] = {
            "model": model_name,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_ctx": context_length,
            },
        }

        if tools:
            payload["tools"] = tools

        req_data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=req_data,
            headers={"Content-Type": "application/json", "User-Agent": "Desktop-AI-Agent"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=120) as response:
                if response.status != 200:
                    raise RuntimeError(f"Ollama returned HTTP {response.status}: {response.read().decode('utf-8')}")
                
                raw = json.loads(response.read().decode("utf-8"))
                message = raw.get("message", {})
                content = message.get("content", "")
                tool_calls = message.get("tool_calls", [])

                return {
                    "role": "assistant",
                    "content": content,
                    "tool_calls": tool_calls,
                    "raw_response": raw,
                }
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Ollama HTTP Error {e.code}: {err_body}")
        except urllib.error.URLError as e:
            raise RuntimeError(f"Failed to reach Ollama at {self.base_url}: {e.reason}")
        except Exception as e:
            raise RuntimeError(f"Chat request failed: {str(e)}")
