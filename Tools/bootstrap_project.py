"""Run once inside Unreal; creates project maps only if they do not exist."""
import json
from pathlib import Path
import unreal

ROOT = Path(unreal.Paths.project_dir()).resolve()
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
registry = unreal.AssetRegistryHelpers.get_asset_registry()
registry.wait_for_completion()
ws_class = unreal.load_class(None, "/Script/WorldScapeCore.WorldScapeRoot")
assert ws_class is not None, "WorldScapeRoot failed to load"

blank = "/Game/Maps/Blank"
test_map = "/Game/Maps/WorldScape_Test"
if not unreal.EditorAssetLibrary.does_asset_exist(blank):
    assert levels.new_level(blank), "Unable to create blank map"
    assert levels.save_current_level()

if not unreal.EditorAssetLibrary.does_asset_exist(test_map):
    assert levels.new_level(test_map), "Unable to create WorldScape test map"
    terrain = actors.spawn_actor_from_class(ws_class, unreal.Vector(0, 0, 0))
    assert terrain is not None
    terrain.set_actor_label("WorldScape_TestTerrain")
    for name, value in {
        "generation_type": unreal.WorldScapeType.FLAT,
        "max_lod": 4, "lod_resolution": 32, "triangle_size": 200.0,
        "noise_intensity": 10000.0, "noise_scale": 800.0, "seed": 10,
        "generate_foliages": False, "ocean": False,
        "generate_collision": True, "generate_world_scape": True,
    }.items():
        terrain.set_editor_property(name, value)
    material = terrain.get_editor_property("terrain_material")
    material.set_editor_property("default_material", unreal.load_asset("/Engine/BasicShapes/BasicShapeMaterial"))
    terrain.set_editor_property("terrain_material", material)
    sun = actors.spawn_actor_from_class(unreal.DirectionalLight, unreal.Vector(0, 0, 10000), unreal.Rotator(-45, -30, 0))
    sun.set_actor_label("Sun")
    actors.spawn_actor_from_class(unreal.SkyAtmosphere, unreal.Vector(0, 0, 0))
    actors.spawn_actor_from_class(unreal.SkyLight, unreal.Vector(0, 0, 0))
    actors.spawn_actor_from_class(unreal.PlayerStart, unreal.Vector(0, 0, 20000))
    unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).set_level_viewport_camera_info(
        unreal.Vector(-20000, -20000, 25000), unreal.Rotator(-30, 45, 0))
    assert levels.save_current_level()

assert levels.load_level(blank)
report = {
    "engine": unreal.SystemLibrary.get_engine_version(),
    "worldscape_class": ws_class.get_path_name(),
    "worldscape_assets": len(registry.get_assets_by_path("/WorldScape", recursive=True)),
    "blank_map": blank,
    "test_map": test_map,
}
(ROOT / "Saved/Logs/BootstrapReport.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
unreal.log("BIGWORLD_BOOTSTRAP_OK " + json.dumps(report))
