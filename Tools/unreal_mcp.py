"""Local stdio MCP bridge; Unreal operations run on the editor's Python thread."""
import json
from pathlib import Path
import subprocess
import sys
import threading

from mcp.server.fastmcp import FastMCP

ROOT = Path(__file__).resolve().parents[1]
LOCK = threading.Lock()
mcp = FastMCP("BigWorld UE 5.8.2")


def execute(code: str, mode: str = "ExecuteFile") -> dict:
    with LOCK:
        try:
            completed = subprocess.run(
                [sys.executable, str(ROOT / "Tools/ue_bridge.py")],
                input=json.dumps({"code": code, "mode": mode}),
                capture_output=True, text=True, encoding="utf-8", timeout=135,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            if completed.returncode:
                return {"success": False, "error": completed.stderr[-4000:]}
            return json.loads(completed.stdout)
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Editor request timed out; inspect the editor before retrying a mutation."}
        except (OSError, ValueError) as error:
            return {"success": False, "error": str(error)}


@mcp.tool(annotations={"readOnlyHint": True})
def editor_status() -> dict:
    """Check this project's live editor, engine version, map, and WorldScape class."""
    return execute("import unreal, json\nprint(json.dumps({"
                   "'engine': unreal.SystemLibrary.get_engine_version(),"
                   "'project': unreal.Paths.get_project_file_path(),"
                   "'map': unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world().get_path_name(),"
                   "'worldscape': unreal.load_class(None, '/Script/WorldScapeCore.WorldScapeRoot') is not None}))")


@mcp.tool(annotations={"readOnlyHint": True})
def list_level_actors(limit: int = 100) -> dict:
    """List actors in the current editor level. Returns at most 500 entries."""
    limit = max(1, min(limit, 500))
    return execute("import unreal, json\n"
                   "actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()\n"
                   f"print(json.dumps([{{'label': a.get_actor_label(), 'path': a.get_path_name(), 'class': a.get_class().get_name()}} for a in actors[:{limit}]]))")


@mcp.tool(annotations={"readOnlyHint": True})
def list_assets(path: str = "/WorldScape", limit: int = 100) -> dict:
    """List asset paths under /Game or /WorldScape without loading the assets."""
    if not any(path == p or path.startswith(p + "/") for p in ("/Game", "/WorldScape")) or ".." in path:
        raise ValueError("Path must be within /Game or /WorldScape")
    limit = max(1, min(limit, 500))
    return execute("import unreal, json\n"
                   f"assets = unreal.AssetRegistryHelpers.get_asset_registry().get_assets_by_path({path!r}, recursive=True)\n"
                   f"print(json.dumps({{'total': len(assets), 'assets': [str(a.package_name) for a in assets[:{limit}]]}}))")


@mcp.tool(annotations={"readOnlyHint": False, "destructiveHint": True})
def execute_python(code: str) -> dict:
    """Execute Python in the BigWorld editor. Can edit actors/assets and save maps.

    Use only for user-authorized project work. Runs with editor privileges; inspect
    success and output before continuing. Never retry a timed-out mutation blindly.
    """
    return execute(code)


if __name__ == "__main__":
    mcp.run(transport="stdio")
