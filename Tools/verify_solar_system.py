"""在 PIE 中逐天体验证并截图，结束后恢复地球轨道巡视和正常输入。"""
import json
import math
import time
from pathlib import Path
import unreal as u


class SolarProbe:
    def __init__(self):
        self.world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_game_world()
        assert self.world, '需要运行 SolarSystem 关卡'
        self.system = u.GameplayStatics.get_all_actors_of_class(self.world,u.SolarSystemActor)[0]
        self.pawn = u.GameplayStatics.get_player_pawn(self.world,0)
        self.pawn.set_actor_tick_enabled(False)
        self.system.set_time_scale(0)
        self.system.set_simulation_time(0)
        self.steps = [('orbit',i) for i in range(10)] + [('surface',i) for i in [1,2,3,4,5]]
        self.index = -1
        self.rows = []
        self.image_dir = Path(u.Paths.project_dir()).resolve()/'Images/2026-10-09'
        self.image_dir.mkdir(parents=True,exist_ok=True)
        self.started = time.monotonic()
        self.busy = True
        self.done = False
        self.handle = u.register_slate_post_tick_callback(self.tick)
        self.next_step()
        self.busy = False

    def next_step(self):
        self.index += 1
        if self.index >= len(self.steps):
            self.finish()
            return
        mode, index = self.steps[self.index]
        self.system.focus_body(index)
        if mode == 'surface':
            assert self.system.visit_surface(25,0,35)
        self.deadline = time.monotonic() + (12 if mode == 'surface' else 4)
        self.captured = False

    def tick(self,delta):
        # Asset loading and screenshots can pump Slate recursively.
        if self.busy or self.done:
            return
        self.busy = True
        try:
            if time.monotonic() < self.deadline:
                return
            if self.captured:
                self.next_step()
                return
            mode, index = self.steps[self.index]
            d=json.loads(self.system.get_diagnostics())
            row={k:d[k] for k in ['focus','surface_mode','trees','grass','atmosphere']}
            row['key']=d['bodies'][index]['key']; row['mode']=mode
            row['camera_cm']=self.pawn.get_actor_location().to_tuple()
            row['camera_finite']=all(math.isfinite(v) for v in row['camera_cm'])
            row['world_bounds']=self.world.get_world_settings().get_editor_property('enable_world_bounds_checks')
            if mode == 'surface':
                terrain=self.system.active_terrain
                lods=terrain.get_editor_property('world_scape_lod')
                row['lod_count']=len(lods)
                row['invalid_bounds']=0
                for lod in lods:
                    mesh=lod.get_editor_property('mesh')
                    o,e,r=u.SystemLibrary.get_component_bounds(mesh)
                    row['invalid_bounds']+=not all(math.isfinite(v) for v in (*o.to_tuple(),*e.to_tuple(),r))
                row['ground_height_cm']=terrain.get_ground_height(self.pawn.get_actor_location())
                row['surface_clearance_m']=(self.pawn.get_actor_location().length()-terrain.planet_scale-row['ground_height_cm'])/100
            self.rows.append(row)
            filename=self.image_dir/(row['key'].lower()+'-'+mode+'-after.png')
            u.AutomationLibrary.take_high_res_screenshot(1280,720,str(filename))
            self.captured=True
            self.deadline=time.monotonic()+2
        except Exception as exc:
            self.finish(str(exc))
            raise
        finally:
            self.busy = False

    def finish(self,error=None):
        if self.done:
            return
        self.done = True
        u.unregister_slate_post_tick_callback(self.handle)
        model=json.loads(self.system.validate_model())
        failures=[]
        if error: failures.append(error)
        for r in self.rows:
            if not r['camera_finite'] or r['world_bounds']: failures.append(r['key']+': camera / world bounds')
            if r['mode']=='surface':
                if r['lod_count']<10 or r['invalid_bounds'] or not math.isfinite(r['ground_height_cm']): failures.append(r['key']+': terrain')
                if r['key']=='Earth' and (r['trees']==0 or r['grass']==0): failures.append('Earth: vegetation')
                if r['key'] in ['Moon','Mercury'] and r['atmosphere']: failures.append(r['key']+': unexpected atmosphere')
        if len(self.rows)!=15: failures.append('Not all 15 cases completed')
        report={'success':not failures and model['success'],'failures':failures,'model':model,'rows':self.rows,'duration_seconds':time.monotonic()-self.started,'scope':'逐天体切换、五个岩质天体地表、数值和网格包围盒检查；相机输入暂时冻结，未模拟物理按键，未测试航天器物理。'}
        target=Path(u.Paths.project_saved_dir())/'SolarRuntimeValidation.json'
        target.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
        self.system.focus_body(3)
        self.system.set_time_scale(1)
        self.pawn.set_actor_tick_enabled(True)
        self.world=self.system=self.pawn=None
        print('SOLAR_RUNTIME_DONE',report['success'],failures)


solar_probe=SolarProbe()
