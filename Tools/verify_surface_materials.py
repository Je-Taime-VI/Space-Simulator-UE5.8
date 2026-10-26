"""在太阳系PIE中固定机位采集地表材质；输出真实截图与采样记录。"""
import json
import time
from pathlib import Path
import unreal as u

ROOT=Path(u.Paths.project_dir()).resolve()
OUT=ROOT/'Saved/Diagnostics/SurfaceMaterials'
IMAGES=ROOT/'Images/2026-10-12/SurfaceMaterials'


class SurfaceProbe:
    def __init__(self,stage,sites=None):
        self.stage=stage
        self.world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_game_world()
        self.system=u.GameplayStatics.get_all_actors_of_class(self.world,u.SolarSystemActor)[0]
        self.pawn=u.GameplayStatics.get_player_pawn(self.world,0)
        assert isinstance(self.pawn,u.SolarExplorerPawn), 'Requires Play'
        OUT.mkdir(parents=True,exist_ok=True)
        sites_path=OUT/'Sites.json'
        if not sites_path.exists():
            sites_path=ROOT/'Documentation/Verification/2026-10-12/SurfaceMaterials/Sites.json'
        self.sites=sites or json.loads(sites_path.read_text(encoding='utf-8'))
        self.saved_scale=self.system.time_scale
        self.saved_time=self.system.simulation_seconds
        self.pawn.set_actor_tick_enabled(False)
        self.system.set_time_scale(0)
        self.system.set_simulation_time(0)
        self.rows=[];self.errors=[];self.index=-1;self.done=False;self.busy=True
        IMAGES.mkdir(parents=True,exist_ok=True)
        self.handle=u.register_slate_post_tick_callback(self.tick)
        self.advance()
        self.busy=False

    def advance(self):
        self.index+=1
        if self.index==len(self.sites):
            self.finish();return
        site=self.sites[self.index]
        self.system.focus_body(site['body'])
        if not site.get('orbit'):
            assert self.system.visit_surface(*site['latlon'],site['height_m'])
            up=self.pawn.get_actor_location().normal()
            east=u.Vector(0,0,1).cross(up).normal()
            forward=(east-up*.4).normal()
            self.pawn.set_view_pose(self.pawn.get_actor_location(),u.MathLibrary.make_rot_from_xz(forward,up))
        self.phase='capture'
        self.deadline=time.monotonic()+(8 if site.get('orbit') else 18)

    def tick(self,dt):
        if self.done or self.busy or time.monotonic()<self.deadline:return
        self.busy=True
        try:
            if self.phase=='advance':self.advance();return
            site=self.sites[self.index]
            row={'site':site,'position_cm':self.pawn.get_actor_location().to_tuple(),
                 'rotation':self.pawn.get_actor_rotation().to_tuple(),
                 'exposure_bias':self.system.lighting_exposure.settings.auto_exposure_bias,
                 'sun_lux':self.system.sun_light.intensity,
                 'diagnostics':json.loads(self.system.get_diagnostics())}
            if not site.get('orbit'):
                assert self.system.terrain_blend>.999,'Terrain is not ready'
                root=self.system.active_terrain
                row['terrain_material']=root.terrain_material.default_material.get_path_name()
                row['ground_height_cm']=root.get_ground_height_h_only(self.pawn.get_actor_location())
            self.rows.append(row)
            u.AutomationLibrary.take_high_res_screenshot(1280,720,str(IMAGES/(site['name']+'-'+self.stage+'.png')))
            self.phase='advance';self.deadline=time.monotonic()+2
        except Exception as exc:
            self.errors.append(repr(exc));self.finish();raise
        finally:
            self.busy=False

    def finish(self):
        if self.done:return
        self.done=True
        u.unregister_slate_post_tick_callback(self.handle)
        (OUT/(self.stage+'.json')).write_text(json.dumps({'success':not self.errors,'errors':self.errors,'views':self.rows},ensure_ascii=False,indent=2),encoding='utf-8')
        self.pawn.set_actor_tick_enabled(True)
        self.system.set_time_scale(self.saved_scale)
        print('SURFACE_MATERIAL_PROBE_DONE',self.stage,self.errors)


class MotionProbe:
    """固定时间的小范围平移/返回，并检查细节淡出后的高空画面。"""
    def __init__(self):
        self.world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_game_world()
        self.system=u.GameplayStatics.get_all_actors_of_class(self.world,u.SolarSystemActor)[0]
        self.pawn=u.GameplayStatics.get_player_pawn(self.world,0)
        self.system.set_time_scale(0);self.system.set_simulation_time(0)
        self.system.focus_body(3);self.system.visit_surface(25,0,5)
        self.pawn.set_actor_tick_enabled(False)
        self.origin=self.pawn.get_actor_location();self.up=self.origin.normal()
        self.east=u.Vector(0,0,1).cross(self.up).normal()
        self.rotation=u.MathLibrary.make_rot_from_xz((self.east-self.up*.6).normal(),self.up)
        self.pawn.set_view_pose(self.origin,self.rotation)
        self.phase=0;self.done=False;self.rows=[];self.busy=False
        self.deadline=time.monotonic()+18
        self.handle=u.register_slate_post_tick_callback(self.tick)

    def tick(self,dt):
        if self.done or self.busy or time.monotonic()<self.deadline:return
        self.busy=True
        names=['origin','offset-50cm','offset-200cm','returned','detail-disabled','fade-10km']
        name=names[self.phase]
        u.AutomationLibrary.take_high_res_screenshot(1280,720,str(IMAGES/('motion-'+name+'.png')))
        self.rows.append({'name':name,'position_cm':self.pawn.get_actor_location().to_tuple(),'rotation':self.pawn.get_actor_rotation().to_tuple()})
        self.phase+=1
        self.deadline=time.monotonic()+4
        self.move_time=time.monotonic()+1
        # Move only on the following callback, after the asynchronous screenshot.
        self.handle_move=u.register_slate_post_tick_callback(self.move)
        self.busy=False

    def move(self,dt):
        if time.monotonic()<self.move_time:return
        u.unregister_slate_post_tick_callback(self.handle_move)
        if self.phase==1:self.pawn.set_view_pose(self.origin+self.east*50,self.rotation)
        elif self.phase==2:self.pawn.set_view_pose(self.origin+self.east*200,self.rotation)
        elif self.phase==3:self.pawn.set_view_pose(self.origin,self.rotation)
        elif self.phase==4:self.system.active_terrain.terrain_material.default_material.set_scalar_parameter_value('DetailStrength',0)
        elif self.phase==5:
            self.system.active_terrain.terrain_material.default_material.set_scalar_parameter_value('DetailStrength',1)
            self.pawn.set_view_pose(self.up*((self.system.bodies[3].radius_km+10)*100000),u.MathLibrary.make_rot_from_xz(-self.up,self.east))
            self.deadline=time.monotonic()+15
        else:
            self.done=True;u.unregister_slate_post_tick_callback(self.handle)
            self.pawn.set_view_pose(self.origin,self.rotation);self.pawn.set_actor_tick_enabled(True);self.system.set_time_scale(1)
            (OUT/'Motion.json').write_text(json.dumps({'views':self.rows,'scope':'平移画面检查及同机位返回对照，不代表所有位置与速度均无纹理滑动。关闭细节仅为诊断，已恢复。'},ensure_ascii=False,indent=2),encoding='utf-8')
            print('SURFACE_MATERIAL_MOTION_DONE')
