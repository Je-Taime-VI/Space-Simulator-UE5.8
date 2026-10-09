"""In-editor: verify an idle fly pawn near both hemispheres below default KillZ."""
import json
import math
import time
from pathlib import Path

import unreal


class PlanetIdleProbe:
    def __init__(self):
        self.world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
        self.pawn = unreal.GameplayStatics.get_player_pawn(self.world, 0)
        self.controller = unreal.GameplayStatics.get_player_controller(self.world, 0)
        self.position = self.pawn.get_actor_location()
        self.rotation = self.controller.get_control_rotation()
        self.planets = unreal.GameplayStatics.get_all_actors_of_class(self.world, unreal.WorldScapeRoot)
        self.rows = []
        self.phase = -1
        self.started = time.monotonic()
        self.done = False
        self.controller.set_ignore_move_input(True)
        self.handle = unreal.register_slate_post_tick_callback(self.tick)

    def finish(self):
        if self.done:
            return
        self.done = True
        unreal.unregister_slate_post_tick_callback(self.handle)
        self.pawn.get_movement_component().stop_movement_immediately()
        self.pawn.set_actor_location(self.position, False, True)
        self.controller.set_control_rotation(self.rotation)
        self.controller.set_ignore_move_input(False)
        output = {"world": self.world.get_path_name(),
                  "world_bounds": self.world.get_world_settings().get_editor_property("enable_world_bounds_checks"),
                  "samples": self.rows, "summary": []}
        for phase in range(len(self.planets)):
            rows = [r for r in self.rows if r["phase"] == phase and r["phase_seconds"] >= 2]
            if len(rows) > 1:
                output["summary"].append({"planet": rows[0]["planet"], "seconds": rows[-1]["phase_seconds"]-rows[0]["phase_seconds"],
                                          "displacement_cm": math.dist(rows[0]["position"], rows[-1]["position"]),
                                          "max_speed_cm_s": max(math.sqrt(sum(v*v for v in r["velocity"])) for r in rows),
                                          "min_height_cm": min(r["height_cm"] for r in rows),
                                          "z_cm": rows[0]["position"][2]})
        path = Path(unreal.Paths.project_saved_dir()) / "Logs/PlanetIdleVerification.json"
        path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
        print("PLANET_IDLE_DONE", json.dumps(output["summary"]))

    def tick(self, delta):
        try:
            elapsed = time.monotonic() - self.started
            phase = int(elapsed // 8)
            if phase >= len(self.planets):
                self.finish()
                return
            planet = self.planets[phase]
            if phase != self.phase:
                self.phase = phase
                direction = unreal.Vector(0, 0, -1)
                surface = planet.get_actor_location() + direction * planet.get_editor_property("planet_scale")
                height = planet.get_ground_height(surface)
                assert math.isfinite(height), "Invalid surface height"
                position = surface + direction * (height + 1500)
                self.pawn.get_movement_component().stop_movement_immediately()
                self.pawn.set_actor_location(position, False, True)
            rotation = planet.get_actor_rotation()
            self.rows.append({"phase": phase, "phase_seconds": elapsed - phase*8,
                              "planet": planet.get_actor_label(), "position": self.pawn.get_actor_location().to_tuple(),
                              "velocity": self.pawn.get_velocity().to_tuple(),
                              "height_cm": planet.get_pawn_distance_from_ground(self.pawn.get_actor_location()),
                              "planet_location": planet.get_actor_location().to_tuple(),
                              "planet_rotation": [rotation.pitch, rotation.yaw, rotation.roll]})
        except Exception:
            self.finish()
            raise


planet_idle_probe = PlanetIdleProbe()
print("PLANET_IDLE_STARTED")
