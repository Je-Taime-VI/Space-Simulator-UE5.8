"""短时记录正常输入状态下的地表静止位置；存在按键输入时不作静止结论。"""
import json
import math
import time
from pathlib import Path
import unreal as u


class CameraProbe:
    def __init__(self):
        self.world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_game_world()
        self.system=u.GameplayStatics.get_all_actors_of_class(self.world,u.SolarSystemActor)[0]
        self.pawn=u.GameplayStatics.get_player_pawn(self.world,0)
        self.pc=u.GameplayStatics.get_player_controller(self.world,0)
        self.system.focus_body(3)
        self.system.set_time_scale(1)
        self.system.visit_surface(25,0,35)
        self.pawn.set_actor_tick_enabled(True)
        self.keys=[]
        for name in ['W','S','A','D','E','Q','SpaceBar','LeftControl','LeftShift']:
            k=u.Key(); k.set_editor_property('key_name',name); self.keys.append(k)
        self.started=time.monotonic()
        self.rows=[]
        self.handle=u.register_slate_post_tick_callback(self.tick)

    def tick(self,dt):
        elapsed=time.monotonic()-self.started
        p=self.pawn.get_actor_location()
        self.rows.append({'t':elapsed,'position_cm':p.to_tuple(),'movement_input':any(self.pc.is_input_key_down(k) for k in self.keys)})
        if elapsed<6: return
        u.unregister_slate_post_tick_callback(self.handle)
        moved=any(r['movement_input'] for r in self.rows)
        displacement=math.dist(self.rows[0]['position_cm'],self.rows[-1]['position_cm'])
        result={'success':not moved and displacement<.01,'movement_input_detected':moved,'duration_seconds':elapsed,'idle_displacement_cm':displacement,'time_scale':self.system.time_scale,'rows':self.rows}
        target=Path(u.Paths.project_saved_dir())/'SolarCameraValidation.json'
        target.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
        self.system.focus_body(3)
        self.world=self.system=self.pawn=self.pc=None
        print('SOLAR_CAMERA_DONE',result['success'],displacement,moved)


camera_probe=CameraProbe()
