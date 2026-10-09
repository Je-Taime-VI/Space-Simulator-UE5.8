"""Capture a short, reversible PIE movement probe through the local editor MCP."""
import argparse
import asyncio
import base64
import json
from pathlib import Path

import httpx
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

from ue_bridge import run


def image_data(value):
    if isinstance(value, dict):
        if value.get("type") == "image" or value.get("mimeType") == "image/png":
            return value.get("data")
        for child in value.values():
            found = image_data(child)
            if found:
                return found
    elif isinstance(value, list):
        for child in value:
            found = image_data(child)
            if found:
                return found
    elif isinstance(value, str) and value.startswith("{"):
        try:
            return image_data(json.loads(value))
        except ValueError:
            pass


async def main(args):
    target = Path(__file__).resolve().parents[1] / "Saved/Diagnostics" / args.label
    target.mkdir(parents=True, exist_ok=True)
    code = '''
import unreal, time, json
from pathlib import Path
class FlickerMotionProbe:
 def __init__(self):
  self.world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
  assert self.world is not None
  self.pawn=unreal.GameplayStatics.get_player_pawn(self.world,0)
  self.terrain=unreal.GameplayStatics.get_all_actors_of_class(self.world,unreal.WorldScapeRoot)[0]
  self.position=self.pawn.get_actor_location()
  self.movement=self.pawn.get_movement_component()
  self.speed=self.movement.get_editor_property('max_speed')
  self.freeze=self.terrain.get_editor_property('freeze_generation')
  self.start=time.monotonic(); self.samples=[]; self.done=False
  self.movement.set_editor_property('max_speed',2000.0)
  self.handle=unreal.register_slate_post_tick_callback(self.tick)
 def finish(self):
  if self.done: return
  self.done=True
  unreal.unregister_slate_post_tick_callback(self.handle)
  self.movement.stop_movement_immediately()
  self.movement.set_editor_property('max_speed',self.speed)
  self.terrain.set_editor_property('freeze_generation',self.freeze)
  self.pawn.set_actor_location(self.position,False,True)
  Path(REPORT_PATH).write_text(json.dumps(self.samples,indent=2),encoding='utf-8')
 def tick(self,dt):
  try:
   elapsed=time.monotonic()-self.start
   if elapsed>=40: self.finish(); return
   frozen=elapsed>=20
   self.terrain.set_editor_property('freeze_generation',frozen)
   self.pawn.add_movement_input(self.pawn.get_actor_right_vector(),1.0 if int(elapsed/2)%2==0 else -1.0,False)
   v=self.pawn.get_actor_location()
   self.samples.append({'seconds':elapsed,'frozen':frozen,'height_cm':self.terrain.get_pawn_distance_from_ground(v),'position':[v.x,v.y,v.z]})
  except Exception:
   self.finish(); raise
flicker_motion_probe=FlickerMotionProbe()
print('FLICKER_PROBE_STARTED')
'''.replace("REPORT_PATH", repr(str(target / "motion.json")))
    started = await asyncio.to_thread(run, {"code": code})
    if not started.get("success"):
        raise RuntimeError(started)

    def local_client(headers=None, timeout=None, auth=None):
        return httpx.AsyncClient(headers=headers, timeout=timeout, auth=auth, trust_env=False)

    try:
        async with streamablehttp_client("http://127.0.0.1:8000/mcp", httpx_client_factory=local_client) as (read, write, _):
            async with ClientSession(read, write) as session:
                await session.initialize()
                for i in range(args.count):
                    result = await session.call_tool("call_tool", {
                        "toolset_name": "EditorToolset.EditorAppToolset",
                        "tool_name": "CaptureEditorImage", "arguments": {},
                    })
                    data = image_data(result.model_dump(mode="json"))
                    if not data:
                        raise RuntimeError(str(result)[:1000])
                    (target / f"frame_{i:02d}.png").write_bytes(base64.b64decode(data))
                    print(f"Captured {i+1}/{args.count}", flush=True)
                    await asyncio.sleep(1.5)
    finally:
        stopped = await asyncio.to_thread(run, {"code": "flicker_motion_probe.finish(); print('FLICKER_PROBE_FINISHED')"})
        print("Restored:", stopped.get("success"), "Output:", target)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--label", default="FlickerRebased")
    parser.add_argument("--count", type=int, default=18)
    asyncio.run(main(parser.parse_args()))
