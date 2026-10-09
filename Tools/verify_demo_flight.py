"""Run inside Unreal Python with a demo PIE session already running.

Checks possession and movement input; does not simulate physical key presses.
Only moves the transient PIE pawn, never saves or edits a level.
"""
import json
import math
import time
from pathlib import Path

import unreal


class FlightProbe:
    def __init__(self):
        self.world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
        assert self.world is not None, "Start a demo in Play mode first."
        self.pawn = unreal.GameplayStatics.get_player_pawn(self.world, 0)
        assert self.pawn.get_class().get_name() == "FlyWorldScape_C"
        self.controller = unreal.GameplayStatics.get_player_controller(self.world, 0)
        self.start = time.monotonic()
        self.phase = 0
        self.samples = []
        self.record("start")
        self.handle = unreal.register_slate_post_tick_callback(self.tick)

    def record(self, label):
        v = self.pawn.get_actor_location()
        self.samples.append({"phase": label, "location_cm": [v.x, v.y, v.z]})

    def tick(self, delta):
        try:
            phase = min(int((time.monotonic() - self.start) / 2.0), 3)
            if phase != self.phase:
                self.record(["baseline_end", "forward_end", "right_end"][self.phase])
                self.phase = phase
            if phase == 1:
                self.pawn.add_movement_input(self.pawn.get_actor_forward_vector(), 1.0, False)
            elif phase == 2:
                self.pawn.add_movement_input(self.pawn.get_actor_right_vector(), 1.0, False)
            elif phase == 3:
                unreal.unregister_slate_post_tick_callback(self.handle)
                distances = [math.dist(a["location_cm"], b["location_cm"])
                             for a, b in zip(self.samples, self.samples[1:])]
                report = {
                    "map": self.world.get_path_name(),
                    "game_mode": unreal.GameplayStatics.get_game_mode(self.world).get_class().get_name(),
                    "pawn": self.pawn.get_class().get_name(),
                    "possessed": self.controller.get_controlled_pawn() == self.pawn,
                    "view_target_is_pawn": self.controller.get_view_target() == self.pawn,
                    "vsm": unreal.SystemLibrary.get_console_variable_int_value("r.Shadow.Virtual.Enable"),
                    "samples": self.samples,
                    "baseline_forward_right_cm": distances,
                    "success": len(distances) == 3 and distances[1] > 10 and distances[2] > 10,
                    "verification": "Pawn movement input over frames; physical keyboard not automated.",
                }
                path = Path(unreal.Paths.project_saved_dir(), "Logs", "DemoFlyMovementVerification.json")
                path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
                print("FLIGHT_PROBE_COMPLETE", json.dumps(report))
        except Exception:
            unreal.unregister_slate_post_tick_callback(self.handle)
            raise


flight_probe = FlightProbe()
print("FLIGHT_PROBE_STARTED")
