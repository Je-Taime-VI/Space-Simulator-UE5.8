"""Project-bound client for Epic's bundled Python Remote Execution protocol."""
import json
import os
from pathlib import Path
import sys
import time

PROJECT = Path(__file__).resolve().parents[1]
ENGINE = Path(os.environ.get("UE_ENGINE_ROOT", "E:/Epic Games/UE_5.8"))


def run(request):
    remote_path = ENGINE / "Engine/Plugins/Experimental/PythonScriptPlugin/Content/Python"
    sys.path.insert(0, str(remote_path))
    import remote_execution

    config = remote_execution.RemoteExecutionConfig()
    config.multicast_bind_address = "127.0.0.1"
    config.multicast_ttl = 0
    config.command_endpoint = ("127.0.0.1", 6778)
    remote = remote_execution.RemoteExecution(config)
    try:
        remote.start()
        deadline = time.monotonic() + 8
        matches = []
        while time.monotonic() < deadline:
            matches = [n for n in remote.remote_nodes
                       if n.get("project_root") and Path(n["project_root"]).resolve() == PROJECT]
            if matches:
                break
            time.sleep(0.2)
        if not matches:
            raise RuntimeError("BigWorld editor not found. Open BigWorld.uproject and wait for Python initialization.")
        if len(matches) != 1:
            raise RuntimeError("Multiple BigWorld editors are open. Close duplicate instances before connecting.")
        node = matches[0]
        remote.open_command_connection(node["node_id"])
        # Epic's client otherwise waits forever when the editor stalls.
        remote._command_connection._command_channel_socket.settimeout(90)
        result = remote.run_command(request["code"], unattended=True,
                                    exec_mode=request.get("mode", "ExecuteFile"))
        result["project_name"] = node.get("project_name")
        return result
    finally:
        remote.stop()


if __name__ == "__main__":
    try:
        # Windows PowerShell may prepend a UTF-8 BOM when piping JSON.
        result = run(json.loads(sys.stdin.buffer.read().decode("utf-8-sig")))
    except Exception as error:
        result = {"success": False, "error": str(error)}
    print(json.dumps(result, ensure_ascii=True))
