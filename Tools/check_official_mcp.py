"""Read-only inspection of UE's official MCP server (not the Python bridge)."""
import argparse
import asyncio
from datetime import datetime, timezone
import json
from pathlib import Path
import httpx

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client


async def inspect(args):
    report = {"checked_at_utc": datetime.now(timezone.utc).isoformat(), "url": args.url}
    def local_http_client(headers=None, timeout=None, auth=None):
        # The local editor must not be routed through Windows' internet proxy.
        return httpx.AsyncClient(headers=headers, timeout=timeout, auth=auth, trust_env=False)

    async with streamablehttp_client(args.url, timeout=15, sse_read_timeout=30,
                                     httpx_client_factory=local_http_client) as (read, write, _):
        async with ClientSession(read, write) as session:
            initialized = await session.initialize()
            report["initialize"] = initialized.model_dump(mode="json")
            tools = await session.list_tools()
            report["tools"] = [tool.model_dump(mode="json") for tool in tools.tools]
            arguments = json.loads(args.arguments)
            if args.toolset:
                arguments["toolset_name"] = args.toolset
            if args.call_tool:
                arguments["tool_name"] = args.call_tool
            result = await session.call_tool(args.tool, arguments)
            report["call"] = {"name": args.tool, "result": result.model_dump(mode="json")}
            report["success"] = not result.isError
    root = Path(__file__).resolve().parents[1]
    target = root / "Saved/Logs" / args.output
    target.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=True))
    if not report["success"]:
        raise SystemExit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://127.0.0.1:8000/mcp")
    parser.add_argument("--tool", default="list_toolsets")
    parser.add_argument("--arguments", default="{}")
    parser.add_argument("--toolset")
    parser.add_argument("--call-tool")
    parser.add_argument("--output", default="OfficialMCPVerification.json")
    asyncio.run(inspect(parser.parse_args()))
