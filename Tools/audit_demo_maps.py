"""Run inside Unreal Python: inspect demo defaults, optionally apply shared fixes."""
import json
import shutil
from pathlib import Path

import unreal


def audit_demo_maps(apply=False):
    root = Path(unreal.Paths.project_dir()).resolve()
    backup = root / "Saved/Backups/EarthDiagnostics_20261008/Maps"
    report = []
    registry = unreal.AssetRegistryHelpers.get_asset_registry()
    assets = registry.get_assets_by_path("/WorldScape/Levels", recursive=True)
    for asset in sorted(assets, key=lambda a: str(a.package_name)):
        name = str(asset.package_name)
        if str(asset.asset_class_path.asset_name) != "World":
            continue
        world = unreal.load_asset(name)
        settings = world.get_world_settings()
        planets = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.WorldScapeRoot)
        mode = settings.get_editor_property("default_game_mode")
        row = {
            "map": name, "is_demonstration": name.rsplit("/", 1)[-1].startswith("Demonstration_"),
            "game_mode_override": mode.get_path_name() if mode else None,
            "world_bounds_before": settings.get_editor_property("enable_world_bounds_checks"),
            "kill_z": settings.get_editor_property("kill_z"),
            "planets": [{"label": a.get_actor_label(),
                         "generation_type": str(a.get_editor_property("generation_type")),
                         "radius_cm": a.get_editor_property("planet_scale"),
                         "ocean": a.get_editor_property("ocean"),
                         "noise": str(a.get_editor_property("world_scape_noise"))}
                        for a in planets],
        }
        # Every supplied demonstration is a free-flight inspection scene. The
        # engine's planar KillZ push is incompatible with exploring its underside.
        if apply and row["is_demonstration"]:
            relative = Path(name.removeprefix("/WorldScape/") + ".umap")
            disk = root / "Plugins/WorldScape/Content" / relative
            target = backup / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            if not target.exists():
                shutil.copy2(disk, target)
            settings.set_editor_property("enable_world_bounds_checks", False)
            # Explicit WorldSettings overrides take precedence over map prefixes.
            # Standardize the supplied demonstrations on the project fly mode.
            desired_mode = unreal.load_class(None, "/Game/Blueprints/BP_WorldScapeDemoGameMode.BP_WorldScapeDemoGameMode_C")
            if desired_mode is None:
                raise RuntimeError("Project fly GameMode could not be loaded")
            settings.set_editor_property("default_game_mode", desired_mode)
            row["game_mode_after"] = desired_mode.get_path_name()
            if name.endswith("/Demonstration_EarthLikePlanet"):
                for volume in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.PostProcessVolume):
                    if volume.get_editor_property("unbound"):
                        pp = volume.get_editor_property("settings")
                        pp.set_editor_property("override_auto_exposure_min_brightness", True)
                        pp.set_editor_property("override_auto_exposure_max_brightness", True)
                        pp.set_editor_property("auto_exposure_min_brightness", 1.0)
                        pp.set_editor_property("auto_exposure_max_brightness", 1.0)
                        volume.set_editor_property("settings", pp)
                        row["fixed_exposure_brightness"] = 1.0
            row["saved"] = unreal.EditorLoadingAndSavingUtils.save_map(world, name)
            if not row["saved"]:
                raise RuntimeError("Map save failed: " + name)
        row["world_bounds_after"] = settings.get_editor_property("enable_world_bounds_checks")
        report.append(row)
    target = root / ("Saved/Logs/DemoMapFixReport.json" if apply else "Saved/Logs/DemoMapAuditBefore.json")
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))
    return report
