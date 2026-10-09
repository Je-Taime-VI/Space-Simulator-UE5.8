"""Exercise the real MCP stdio handshake and optionally the live UE connection."""
import argparse
import asyncio
import json
from pathlib import Path
import sys
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main(live):
    root = Path(__file__).resolve().parents[1]
    server = StdioServerParameters(command=sys.executable, args=[str(root / "Tools/unreal_mcp.py")])
    async with stdio_client(server) as (read, write):
        async with ClientSession(read, write) as session:
            initialized = await session.initialize()
            tools = await session.list_tools()
            report = {"server": initialized.serverInfo.model_dump(), "tools": [t.name for t in tools.tools]}
            assert set(report["tools"]) == {"editor_status", "list_level_actors", "list_assets", "execute_python"}
            if live:
                for name, args in [("editor_status", {}), ("list_level_actors", {}), ("list_assets", {"limit": 3}),
                                   ("execute_python", {"code": "print('BIGWORLD_MCP_EXECUTION_OK')"})]:
                    result = await session.call_tool(name, args)
                    assert not result.isError, result
                    content = json.loads(next(c.text for c in result.content if c.type == "text"))
                    assert content.get("success"), content
                    report[name] = content
            output = root / "Saved/Logs" / ("MCPVerification.json" if live else "MCPHandshake.json")
            output.write_text(json.dumps(report, indent=2), encoding="utf-8")
            print(json.dumps(report, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", action="store_true")
    asyncio.run(main(parser.parse_args().live))
