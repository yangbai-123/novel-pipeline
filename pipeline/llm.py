"""LLM 客户端：任何 OpenAI 兼容接口都能用。

设计要点：
- 只依赖 httpx，不引 openai SDK（减少依赖、方便换后端）
- tenacity 做指数退避重试（429/5xx 自动重试）
- 支持同步调用（流水线是串行的，不需要异步）
"""
from __future__ import annotations

import json
from typing import Any

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)


class LLMError(RuntimeError):
    """LLM 调用失败（重试耗尽后抛出）。"""


class LLMClient:
    """极简 OpenAI 兼容客户端。"""

    def __init__(
        self,
        base_url: str,
        api_key: str,
        model: str,
        temperature: float = 0.8,
        max_tokens: int = 4000,
        timeout: int = 120,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout

    @retry(
        retry=retry_if_exception_type((httpx.HTTPError, LLMError)),
        stop=stop_after_attempt(4),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        reraise=True,
    )
    def complete(self, system: str, user: str, *, temperature: float | None = None) -> str:
        """发一次对话补全，返回纯文本。"""
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": self.temperature if temperature is None else temperature,
            "max_tokens": self.max_tokens,
            "stream": False,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        url = f"{self.base_url}/chat/completions"

        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.post(url, headers=headers, json=payload)
                resp.raise_for_status()
                data = resp.json()
        except httpx.HTTPStatusError as exc:
            body = exc.response.text[:300] if exc.response is not None else ""
            raise LLMError(f"HTTP {exc.response.status_code}: {body}") from exc
        except httpx.HTTPError as exc:
            raise LLMError(f"网络错误: {exc}") from exc

        try:
            return data["choices"][0]["message"]["content"].strip()
        except (KeyError, IndexError, TypeError) as exc:
            raise LLMError(f"响应格式异常: {json.dumps(data, ensure_ascii=False)[:300]}") from exc

    def complete_json(self, system: str, user: str) -> Any:
        """要求模型返回 JSON，并宽容地解析（去 markdown 围栏）。"""
        text = self.complete(system, user, temperature=0.3)
        cleaned = text.strip()
        # 去掉 ```json ... ``` 围栏
        if cleaned.startswith("```"):
            lines = cleaned.splitlines()
            if lines and lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip().startswith("```"):
                lines = lines[:-1]
            cleaned = "\n".join(lines).strip()
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as exc:
            raise LLMError(f"JSON 解析失败: {cleaned[:300]}") from exc
