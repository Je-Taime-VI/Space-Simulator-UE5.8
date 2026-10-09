"""UE PIE 中短程前后飞行、静止与 LOD 检查；结束后恢复相机，仅读写瞬时 Pawn。"""
import json
import math
import time
from pathlib import Path

import unreal


class DemoQualityProbe:
    def __init__(self):
        self.world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
        assert self.world, "需要已运行的 PIE"
        self.pawn = unreal.GameplayStatics.get_player_pawn(self.world, 0)
        self.controller = unreal.GameplayStatics.get_player_controller(self.world, 0)
        self.planets = unreal.GameplayStatics.get_all_actors_of_class(self.world, unreal.WorldScapeRoot)
        self.position = self.pawn.get_actor_location()
        self.rotation = self.controller.get_control_rotation()
        self.direction = unreal.MathLibrary.get_forward_vector(self.rotation)
        self.movement = self.pawn.get_movement_component()
        self.movement.stop_movement_immediately()
        self.controller.set_ignore_move_input(True)
        self.started = time.monotonic()
        self.rows = []
        self.done = False
        self.handle = unreal.register_slate_post_tick_callback(self.tick)

    def finish(self, error=None):
        if self.done:
            return
        self.done = True
        unreal.unregister_slate_post_tick_callback(self.handle)
        self.movement.stop_movement_immediately()
        self.pawn.set_actor_location(self.position, False, True)
        self.controller.set_control_rotation(self.rotation)
        self.controller.set_ignore_move_input(False)
        idle = [r for r in self.rows if r["seconds"] < 3]
        output = {"world": self.world.get_path_name(), "error": error,
                  "auto_exposure": unreal.SystemLibrary.get_console_variable_int_value("r.DefaultFeature.AutoExposure"),
                  "world_bounds": self.world.get_world_settings().get_editor_property("enable_world_bounds_checks"),
                  "idle_displacement_cm": math.dist(idle[0]["position"], idle[-1]["position"]) if len(idle)>1 else None,
                  "max_distance_from_start_cm": max((math.dist(self.position.to_tuple(), r["position"]) for r in self.rows),default=0),
                  "invalid_bounds_frames": sum(r["invalid_bounds"]>0 for r in self.rows),
                  "rows": self.rows, "verification": "注入与 W 相同的控制器前向移动输入，不模拟物理按键；恢复原位置。"}
        target = Path(unreal.Paths.project_saved_dir()) / "Logs/IceQualityRuntime.json"
        target.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
        print("DEMO_QUALITY_DONE", json.dumps({k:v for k,v in output.items() if k!="rows"},ensure_ascii=False))

    def tick(self, delta):
        try:
            elapsed = time.monotonic() - self.started
            if elapsed >= 11:
                self.finish()
                return
            if 3 <= elapsed < 6:
                self.pawn.add_movement_input(self.direction, 1.0, True)
            elif 6 <= elapsed < 9:
                self.pawn.add_movement_input(self.direction, -1.0, True)
            invalid = 0
            lod_counts = []
            for planet in self.planets:
                lods = planet.get_editor_property("world_scape_lod")
                lod_counts.append(len(lods))
                for lod in lods:
                    origin, extent, radius = unreal.SystemLibrary.get_component_bounds(lod.get_editor_property("mesh"))
                    invalid += not all(math.isfinite(x) for x in (*origin.to_tuple(),*extent.to_tuple(),radius))
            self.rows.append({"seconds": elapsed, "position": self.pawn.get_actor_location().to_tuple(),
                              "velocity": self.pawn.get_velocity().to_tuple(), "lod_counts": lod_counts,
                              "invalid_bounds": invalid,
                              "height_cm": self.planets[0].get_pawn_distance_from_ground(self.pawn.get_actor_location())})
        except Exception as exc:
            self.finish(str(exc))
            raise


demo_quality_probe = DemoQualityProbe()
print("DEMO_QUALITY_STARTED")
