"""Save an unmodified frame from Epic's local editor MCP."""
import argparse
import asyncio
import base64
from pathlib import Path

import httpx
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

from capture_flicker_probe import image_data


async def capture(target):
    def client(headers=None, timeout=None, auth=None):
        return httpx.AsyncClient(headers=headers, timeout=timeout, auth=auth, trust_env=False)

    async with streamablehttp_client("http://127.0.0.1:8000/mcp", httpx_client_factory=client) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool("call_tool", {
                "toolset_name": "EditorToolset.EditorAppToolset",
                "tool_name": "CaptureEditorImage", "arguments": {},
            })
            data = image_data(result.model_dump(mode="json"))
            if result.isError or not data:
                raise RuntimeError("Editor screenshot did not return an image")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(base64.b64decode(data))
            print(target)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    asyncio.run(capture(args.output.resolve()))
