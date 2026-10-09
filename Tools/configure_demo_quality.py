"""在 UE Python 中运行；默认只读，apply=True 才备份并保存演示地图。"""
import json
import math
import shutil
from pathlib import Path

import unreal


def configure_demo_quality(apply=False, sample_count=256):
    root = Path(unreal.Paths.project_dir()).resolve()
    backup = root / "Saved/Backups/DemoQuality_20261008/Maps"
    registry = unreal.AssetRegistryHelpers.get_asset_registry()
    report = []
    for asset in sorted(registry.get_assets_by_path("/WorldScape/Levels", recursive=True),
                        key=lambda a: str(a.package_name)):
        name = str(asset.package_name)
        if (str(asset.asset_class_path.asset_name) != "World" or
                not name.rsplit("/", 1)[-1].startswith("Demonstration_")):
            continue
        world = unreal.load_asset(name)
        if apply:
            relative = Path(name.removeprefix("/WorldScape/") + ".umap")
            destination = backup / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            if not destination.exists():
                shutil.copy2(root / "Plugins/WorldScape/Content" / relative, destination)
        row = {"map": name, "world_bounds": world.get_world_settings().get_editor_property(
            "enable_world_bounds_checks"), "planets": [], "exposure": []}
        changed = False
        for actor in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.WorldScapeRoot):
            radius = actor.get_editor_property("planet_scale")
            flat = actor.get_editor_property("generation_type") == unreal.WorldScapeType.FLAT
            noise_asset = actor.get_editor_property("world_scape_noise")
            noise_class = noise_asset.get_class().get_name() if noise_asset else "None"
            before = actor.get_editor_property("max_lod")
            # 厂商 FAQ 建议 10–12。大星球/普通平面采用 12；微型球体和 CubeNoise 保留。
            eligible = (flat or radius >= 1000000.0) and noise_class != "CubeNoise"
            desired = max(before, 12) if eligible else before
            if apply and before != desired:
                actor.set_editor_property("max_lod", desired)
                changed = True
            body = {"label": actor.get_actor_label(), "noise_class": noise_class,
                    "flat": flat, "radius_cm": radius, "max_lod_before": before,
                    "max_lod_target": desired, "max_lod_readback": actor.get_editor_property("max_lod"),
                    "lod_resolution": actor.get_editor_property("lod_resolution"),
                    "triangle_size": actor.get_editor_property("triangle_size"),
                    "height_anchor": actor.get_editor_property("height_anchor"),
                    "noise_sample_count": sample_count, "invalid_noise_samples": 0,
                    "height_range_cm": [None, None]}
            heights = []
            # 球面用 Fibonacci 均匀分布；平面在中心 20 km 区域作 16×16 网格抽检。
            for i in range(sample_count):
                if flat:
                    side = math.ceil(math.sqrt(sample_count))
                    point = unreal.Vector(((i % side) / max(1, side - 1) - 0.5) * 2000000,
                                          ((i // side) / max(1, side - 1) - 0.5) * 2000000, 0)
                else:
                    z = 1 - 2 * (i + 0.5) / sample_count
                    theta = i * 2.399963229728653
                    point = unreal.Vector(math.sqrt(1-z*z)*math.cos(theta),
                                          math.sqrt(1-z*z)*math.sin(theta), z) * radius
                data = actor.get_ground_noise(point)
                values = [data.get_editor_property(k) for k in
                          ["height", "height_normalize", "temperature", "humidity"]]
                body["invalid_noise_samples"] += not all(math.isfinite(v) for v in values)
                if math.isfinite(values[0]):
                    heights.append(values[0])
            if heights:
                body["height_range_cm"] = [min(heights), max(heights)]
            row["planets"].append(body)
        for volume in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.PostProcessVolume):
            if not volume.get_editor_property("unbound"):
                continue
            settings = volume.get_editor_property("settings")
            keys = ["override_auto_exposure_min_brightness", "override_auto_exposure_max_brightness",
                    "auto_exposure_min_brightness", "auto_exposure_max_brightness"]
            previous = {k: settings.get_editor_property(k) for k in keys}
            if apply:
                for key, value in zip(keys, [True, True, 1.0, 1.0]):
                    if previous[key] != value:
                        changed = True
                    settings.set_editor_property(key, value)
                volume.set_editor_property("settings", settings)
            row["exposure"].append({"label": volume.get_actor_label(), "before": previous,
                                    "after": {k: settings.get_editor_property(k) for k in keys}})
        row["changed"] = changed
        if apply and changed:
            row["saved"] = unreal.EditorLoadingAndSavingUtils.save_map(world, name)
            if not row["saved"]:
                raise RuntimeError("Map save failed: " + name)
        report.append(row)
    output = root / "Saved/Logs" / ("DemoQualityApplied.json" if apply else "DemoQualityVerified.json")
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"report": str(output), "maps": len(report),
                      "changed": sum(r["changed"] for r in report),
                      "bodies": sum(len(r["planets"]) for r in report),
                      "invalid_noise_samples": sum(p["invalid_noise_samples"] for r in report for p in r["planets"]),
                      "lod_changes": [{"map": r["map"], "body": p["label"],
                                       "before": p["max_lod_before"], "after": p["max_lod_target"]}
                                      for r in report for p in r["planets"]
                                      if p["max_lod_before"] != p["max_lod_target"]]}, ensure_ascii=False))
    return report
