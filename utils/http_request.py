import httpx
from typing import Any, Dict, Optional

async def http_request(
    url: str,
    method: str = "GET",
    headers: Optional[Dict[str, str]] = None,
    params: Optional[Dict[str, Any]] = None,
    json: Optional[Dict[str, Any]] = None,
    # timeout: Optional[float] = 10.0,
) -> httpx.Response:
    # async with httpx.AsyncClient(verify=False, timeout=timeout) as client:
    async with httpx.AsyncClient(verify=False) as client:
        try:
            response = await client.request(
                method=method.upper(),
                url=url,
                headers=headers,
                params=params,
                json=json,
            )
            response.raise_for_status()
            return response
        except httpx.RequestError as e:
            raise RuntimeError(f"Request failed: {e}")
