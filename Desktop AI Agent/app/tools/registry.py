"""Central Tool Registry for agent capabilities."""

import inspect
import json
from typing import Any, Callable, Dict, List, Optional


class ToolRegistry:
    """Registry managing available agent tools and their schemas."""

    def __init__(self):
        self._tools: Dict[str, Callable] = {}
        self._schemas: Dict[str, Dict[str, Any]] = {}
        self._descriptions: Dict[str, str] = {}

    def register(
        self,
        name: str,
        func: Callable,
        description: str,
        parameters_schema: Dict[str, Any],
    ) -> None:
        """Register a tool with its execution function, description and parameters schema."""
        self._tools[name] = func
        self._descriptions[name] = description
        self._schemas[name] = {
            "type": "function",
            "function": {
                "name": name,
                "description": description,
                "parameters": parameters_schema,
            },
        }

    def get_tool(self, name: str) -> Optional[Callable]:
        """Get registered callable by name."""
        return self._tools.get(name)

    def has_tool(self, name: str) -> bool:
        """Check if tool name is registered."""
        return name in self._tools

    def get_ollama_tools(self) -> List[Dict[str, Any]]:
        """Return list of tool definitions formatted for Ollama / OpenAI API."""
        return list(self._schemas.values())

    def get_tool_descriptions(self) -> str:
        """Return a formatted text summary of all registered tools."""
        lines = []
        for name, desc in self._descriptions.items():
            schema = self._schemas[name]["function"]["parameters"]
            props = schema.get("properties", {})
            params = ", ".join(f"{k}: {v.get('type', 'any')}" for k, v in props.items())
            lines.append(f"- {name}({params}): {desc}")
        return "\n".join(lines)

    def execute(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute tool with given argument dictionary.
        Returns a standardized response dictionary.
        """
        if name not in self._tools:
            return {
                "success": False,
                "tool": name,
                "output": None,
                "error": f"Unknown tool '{name}'. Available tools: {list(self._tools.keys())}",
            }

        func = self._tools[name]
        try:
            # Match parameters with function signature
            sig = inspect.signature(func)
            bound_args = {}
            for param_name, param in sig.parameters.items():
                if param_name in arguments:
                    bound_args[param_name] = arguments[param_name]
                elif param.default is not inspect.Parameter.empty:
                    bound_args[param_name] = param.default
                else:
                    return {
                        "success": False,
                        "tool": name,
                        "output": None,
                        "error": f"Missing required parameter '{param_name}' for tool '{name}'",
                    }

            result = func(**bound_args)
            if isinstance(result, dict) and "success" in result:
                result["tool"] = name
                return result
            return {
                "success": True,
                "tool": name,
                "output": result,
                "error": None,
            }
        except Exception as e:
            return {
                "success": False,
                "tool": name,
                "output": None,
                "error": f"Error executing tool '{name}': {str(e)}",
            }
