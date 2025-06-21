import os, json, httpx

from typing import Any, Dict, Optional
from httpx import ConnectError, HTTPStatusError, RequestError

from dotenv import load_dotenv
load_dotenv()

LOCAL_MCP_SERVER_URL = os.getenv("LOCAL_MCP_SERVER_URL")

async def json_rpc_client(
    method: str,
    params: Optional[Dict[str, Any]] = None,
    url: str = LOCAL_MCP_SERVER_URL,
    request_id: int = 1,
    # timeout: int = 1000
) -> Any:
    try:
        # async with httpx.AsyncClient(verify=False, timeout=timeout) as client:
        async with httpx.AsyncClient(verify=False) as client:
            resp = await client.post(url, json={
                "jsonrpc": "2.0",
                "method": method,
                "params": params or {},
                "id": request_id
            })
            resp.raise_for_status()

            data = resp.json()
            if "error" in data:
                raise RuntimeError(f"MCP Error: {data['error']}")
            return data.get("result")

    except ConnectError:
        raise RuntimeError(f"Could not connect to MCP server at {url}.")
    except HTTPStatusError as e:
        raise RuntimeError(f"HTTP error: {e.response.status_code} {e.response.text}")
    except RequestError as e:
        raise RuntimeError(f"Request failed: {e}")
    except Exception as e:
        raise RuntimeError(f"Unexpected error during MCP request: {e}")
