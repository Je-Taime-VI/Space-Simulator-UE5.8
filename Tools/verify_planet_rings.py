"""在游戏视口采集四颗巨行星星环；固定时间、机位并恢复巡视状态。"""
import json
import math
import time
from pathlib import Path
import unreal as u

ROOT = Path(u.Paths.project_dir()).resolve()
OUT = ROOT/'Saved/Diagnostics/PlanetRings_20261017'


class RingProbe:
    def __init__(self, stage='after', views=('lit','back','edge','near'), bodies=(6,7,8,9)):
        self.w=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_game_world()
        self.s=u.GameplayStatics.get_all_actors_of_class(self.w,u.SolarSystemActor)[0]
        self.p=u.GameplayStatics.get_player_pawn(self.w,0)
        self.saved=dict(focus=self.s.focus_index,seconds=self.s.simulation_seconds,scale=self.s.time_scale,
                       pos=self.p.get_actor_location(),rot=self.p.get_actor_rotation(),tick=self.p.is_actor_tick_enabled(),
                       speed=self.p.speed_km_per_second)
        self.s.set_time_scale(0);self.s.set_simulation_time(0);self.p.set_actor_tick_enabled(False)
        self.stage=stage;self.folder=OUT/stage;self.folder.mkdir(parents=True,exist_ok=True)
        self.steps=[(b,v) for b in bodies for v in views]
        self.rows=[];self.errors=[];self.index=-1;self.done=False;self.busy=False
        self.handle=u.register_slate_post_tick_callback(self.tick)
        self.advance()

    def advance(self):
        self.index+=1
        if self.index==len(self.steps):
            self.finish();return
        b,v=self.steps[self.index]
        self.s.focus_body(b)
        self.phase='setup';self.frame=0;self.deadline=time.monotonic()+1

    def setup(self):
        b,v=self.steps[self.index]
        sun=self.s.sun_light.get_forward_vector()*-1.
        xy=u.Vector(sun.x,sun.y,0).normal();z=1 if sun.z>=0 else -1
        n=(xy*.8+u.Vector(0,0,z*.6)).normal()
        if v=='back': n=(xy*-0.97+u.Vector(0,0,-z*.24)).normal()
        if v=='edge': n=(xy+u.Vector(0,0,z*.012)).normal()
        distance=6.5 if b==7 else 5.8
        pos=n*(self.s.bodies[b].radius_km*distance*100000)
        target=u.Vector(0,0,0)
        if v=='near':
            radius={6:126000,7:105000,8:51149,9:62933}[b]
            target=xy*(radius*100000)
            pos=target+u.Vector(0,0,z*radius*.24*100000)
        self.p.set_view_pose(pos,u.MathLibrary.make_rot_from_xz((target-pos).normal(),u.Vector(0,0,1) if v!='near' else xy))
        self.phase='capture';self.frame=0;self.deadline=time.monotonic()+3

    def tick(self,dt):
        if self.done or self.busy:return
        self.busy=True
        try:
            self.frame+=1
            if self.frame<24 or time.monotonic()<self.deadline:return
            if self.phase=='setup':self.setup()
            elif self.phase=='capture':
                b,v=self.steps[self.index];name=self.s.bodies[b].key+'-'+v
                u.SystemLibrary.execute_console_command(self.w,'Shot filename="%s"'%(self.folder/(name+'.png')).as_posix())
                components=self.s.get_components_by_class(u.ProceduralMeshComponent)
                rings=[dict(name=c.get_name(),scale=c.get_world_scale().to_tuple(),position=c.get_world_location().to_tuple(),
                       rotation=c.get_world_rotation().to_tuple(),material=c.get_material(0).get_name() if c.get_material(0) else None,
                       visible=c.is_visible()) for c in components if 'Ring' in c.get_name()]
                self.rows.append(dict(name=name,body=b,view=v,pos=self.p.get_actor_location().to_tuple(),rot=self.p.get_actor_rotation().to_tuple(),
                        rings=rings,diagnostics=json.loads(self.s.get_diagnostics()),
                        cloud_rt=u.SystemLibrary.get_console_variable_int_value('r.VolumetricRenderTarget'),
                        ap=u.SystemLibrary.get_console_variable_int_value('r.SkyAtmosphere.AerialPerspectiveLUT.FastApplyOnOpaque')))
                self.phase='next';self.deadline=time.monotonic()+.3
            else:self.advance()
        except Exception as exc:
            self.errors.append(repr(exc));self.finish();raise
        finally:self.busy=False

    def finish(self):
        if self.done:return
        self.done=True;u.unregister_slate_post_tick_callback(self.handle)
        (OUT/(self.stage+'.json')).write_text(json.dumps(dict(completed=not self.errors,errors=self.errors,frames=self.rows),ensure_ascii=False,indent=2),encoding='utf-8')
        self.s.focus_body(self.saved['focus']);self.s.set_simulation_time(self.saved['seconds']);self.s.set_time_scale(self.saved['scale'])
        self.p.set_view_pose(self.saved['pos'],self.saved['rot']);self.p.speed_km_per_second=self.saved['speed'];self.p.set_actor_tick_enabled(self.saved['tick'])
        print('RING_PROBE_DONE',self.stage,self.errors)


def start(stage='after',views=('lit','back','edge','near'),bodies=(6,7,8,9)):
    return RingProbe(stage,views,bodies)


class RingMotionProbe(RingProbe):
    """四个机位各采集静止8帧、平移/转向16帧、返回8帧。"""
    def __init__(self):
        super().__init__('motion',('lit',))

    def setup(self):
        b,_=self.steps[self.index]
        # Dust rings are inspected in backlight; dense rings in reflected light.
        self.steps[self.index]=(b,'lit' if b in (7,8) else 'back')
        super().setup()
        self.origin=self.p.get_actor_location();self.rotation=self.p.get_actor_rotation()
        self.right=self.p.get_actor_right_vector();self.forward=self.p.get_actor_forward_vector();self.up=self.p.get_actor_up_vector()
        self.phase='warm';self.motion_frame=0

    def tick(self,dt):
        if self.done or self.busy:return
        self.busy=True
        try:
            self.frame+=1
            if self.phase in ('setup','warm') and (self.frame<24 or time.monotonic()<self.deadline):return
            if self.phase=='setup':self.setup();return
            self.phase='motion'
            frame=self.motion_frame;b,v=self.steps[self.index]
            if frame>=40:self.advance();return
            if frame<24 or frame>=32:
                phase='still' if frame<8 else 'move' if frame<24 else 'returned'
                name='%s-%s-%03d'%(self.s.bodies[b].key,phase,frame)
                u.SystemLibrary.execute_console_command(self.w,'Shot filename="%s"'%(self.folder/(name+'.png')).as_posix())
                self.rows.append(dict(name=name,body=b,phase=phase,pos=self.p.get_actor_location().to_tuple(),rot=self.p.get_actor_rotation().to_tuple()))
            if 7<=frame<23:
                offset=math.sin((frame-7)/16*2*math.pi)
                direction=u.MathLibrary.rotate_angle_axis(self.forward,offset*.3,self.up)
                self.p.set_view_pose(self.origin+self.right*(offset*self.s.bodies[b].radius_km*1000),u.MathLibrary.make_rot_from_xz(direction,self.up))
            elif frame==23:self.p.set_view_pose(self.origin,self.rotation)
            self.motion_frame+=1
        except Exception as exc:
            self.errors.append(repr(exc));self.finish();raise
        finally:self.busy=False


def start_motion():return RingMotionProbe()
