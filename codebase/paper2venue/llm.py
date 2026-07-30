from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass
class ToolCall:
    name: str
    args: dict[str, Any]


@dataclass
class ModelResponse:
    text: str | None = None
    tool_calls: list[ToolCall] = field(default_factory=list)
    raw: Any | None = None


class Provider(Protocol):
    default_model: str

    def complete(
        self,
        messages: list[dict[str, str]],
        tools: list[dict[str, Any]] | None = None,
        *,
        model: str | None = None,
        temperature: float = 0.0,
        tool_choice: Any | None = None,
    ) -> ModelResponse:
        ...


class OpenAICompatibleProvider:
    def __init__(
        self,
        *,
        api_key_env: str,
        default_model: str,
        base_url: str | None = None,
    ) -> None:
        self.api_key_env = api_key_env
        self.default_model = default_model
        self.base_url = base_url

    def complete(
        self,
        messages: list[dict[str, str]],
        tools: list[dict[str, Any]] | None = None,
        *,
        model: str | None = None,
        temperature: float = 0.0,
        tool_choice: Any | None = None,
    ) -> ModelResponse:
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise RuntimeError("Install dependencies: python -m pip install -r requirements.txt") from exc

        api_key = os.getenv(self.api_key_env)
        if not api_key:
            raise RuntimeError(f"Missing API key: {self.api_key_env}")

        client = OpenAI(api_key=api_key, base_url=self.base_url)
        kwargs: dict[str, Any] = {
            "model": model or self.default_model,
            "messages": messages,
            "temperature": temperature,
        }
        if tools:
            kwargs["tools"] = tools
        if tool_choice is not None:
            kwargs["tool_choice"] = tool_choice

        response = client.chat.completions.create(**kwargs)
        message = response.choices[0].message
        calls = [
            ToolCall(
                name=call.function.name,
                args=json.loads(call.function.arguments or "{}"),
            )
            for call in (message.tool_calls or [])
        ]
        return ModelResponse(text=message.content, tool_calls=calls, raw=response)


def make_provider(name: str) -> Provider:
    if name == "openai":
        return OpenAICompatibleProvider(
            api_key_env="OPENAI_API_KEY",
            default_model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        )
    if name == "openrouter":
        return OpenAICompatibleProvider(
            api_key_env="OPENROUTER_API_KEY",
            base_url=os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
            default_model=os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini"),
        )
    raise ValueError("provider must be 'openai' or 'openrouter'")


def function_tool(name: str, description: str, parameters: dict[str, Any]) -> dict[str, Any]:
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": parameters,
        },
    }


def required_tool_choice(name: str) -> dict[str, Any]:
    return {"type": "function", "function": {"name": name}}


def tool_payload(response: ModelResponse, expected_name: str) -> dict[str, Any]:
    for call in response.tool_calls:
        if call.name == expected_name:
            return call.args
    if response.text:
        try:
            value = json.loads(response.text)
        except json.JSONDecodeError:
            value = None
        if isinstance(value, dict):
            return value
    raise ValueError(f"Model did not return required structured result: {expected_name}")

