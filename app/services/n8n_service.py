from typing import Any, Optional

import httpx


class N8NServiceError(Exception):
    pass


class N8NService:
    def __init__(
        self,
        base_url: str,
        api_key: Optional[str] = None,
        timeout_seconds: float = 20.0
    ):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout_seconds = timeout_seconds

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["X-N8N-API-KEY"] = self.api_key
        return headers

    async def trigger_webhook(
        self,
        webhook_path_or_url: str,
        payload: dict[str, Any]
    ) -> dict[str, Any]:
        url = webhook_path_or_url
        if not url.startswith(("http://", "https://")):
            url = f"{self.base_url}/{webhook_path_or_url.lstrip('/')}"

        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.post(url, json=payload, headers=self._headers())
                response.raise_for_status()
                if not response.content:
                    return {}
                return response.json()
        except httpx.HTTPError as exc:
            raise N8NServiceError(f"Failed to trigger n8n webhook: {exc}") from exc
