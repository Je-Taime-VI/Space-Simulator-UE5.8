"""In-editor regression probe for non-finite terrain noise and generated LODs."""
import json
import math
from pathlib import Path

import unreal


def verify_planet_noise(label="EarthNoiseAfter", sample_count=512):
    subsystem = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
    world = subsystem.get_game_world() or subsystem.get_editor_world()
    report = {"world": world.get_path_name(), "sample_count": sample_count, "planets": []}
    for actor in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.WorldScapeRoot):
        radius = actor.get_editor_property("planet_scale")
        row = {"label": actor.get_actor_label(), "noise": str(actor.get_editor_property("world_scape_noise")),
               "invalid_noise_samples": 0, "negative_heights": 0, "samples": [], "lods": []}
        for i in range(sample_count):
            z = 1 - 2 * (i + 0.5) / sample_count
            angle = i * 2.399963229728653
            position = unreal.Vector(math.sqrt(1-z*z)*math.cos(angle), math.sqrt(1-z*z)*math.sin(angle), z) * radius
            noise = actor.get_ground_noise(position)
            sample = {name: noise.get_editor_property(name) for name in ["height", "height_normalize", "temperature", "humidity"]}
            row["invalid_noise_samples"] += not all(math.isfinite(v) for v in sample.values())
            row["negative_heights"] += sample["height"] < 0
            sample["position"] = position.to_tuple()
            row["samples"].append(sample)
        for kind in ["world_scape_lod", "world_scape_lod_ocean"]:
            for lod in actor.get_editor_property(kind):
                vertices = lod.get_editor_property("vertices")
                bounds = unreal.SystemLibrary.get_component_bounds(lod.get_editor_property("mesh"))
                row["lods"].append({"type": kind, "lod": lod.get_editor_property("lod"),
                                    "vertices": len(vertices),
                                    "invalid_vertices": sum(not all(math.isfinite(x) for x in v.to_tuple()) for v in vertices),
                                    "invalid_bounds": not all(math.isfinite(x) for x in (*bounds[0].to_tuple(), *bounds[1].to_tuple(), bounds[2]))})
        report["planets"].append(row)
    target = Path(unreal.Paths.project_dir()).resolve() / "Saved/Logs" / (label + ".json")
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    summaries = [{"label": p["label"], "noise_samples": len(p["samples"]),
                  "invalid_noise": p["invalid_noise_samples"], "negative_heights": p["negative_heights"],
                  "lods": len(p["lods"]), "invalid_vertices": sum(l["invalid_vertices"] for l in p["lods"]),
                  "invalid_bounds": sum(l["invalid_bounds"] for l in p["lods"])} for p in report["planets"]]
    print(json.dumps(summaries, ensure_ascii=False))
    return report
