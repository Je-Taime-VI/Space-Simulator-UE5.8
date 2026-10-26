"""定向采集海岸、海面、水下与高空，并验证正常移动函数能否穿过海面。"""
import json
import math
import time
from pathlib import Path
import unreal as u

ROOT=Path(u.Paths.project_dir()).resolve()
OUT=ROOT/'Saved/Diagnostics/Ocean_20261018'


def direction(lat,lon):
    a,b=math.radians(lat),math.radians(lon)
    return u.Vector(math.cos(a)*math.cos(b),math.cos(a)*math.sin(b),math.sin(a))


def manual_speed(p,target):
    p.apply_flight_input(u.Vector(),0,False,False)
    p.apply_flight_input(u.Vector(),0,True,False)
    duration=math.log2(target/p.manual_speed_km_per_second)*p.speed_adjustment_doubling_seconds
    while abs(duration)>1e-6:
        dt=min(.1,abs(duration))
        p.apply_flight_input(u.Vector(),dt,duration>0,duration<0)
        duration-=math.copysign(dt,duration)
    p.apply_flight_input(u.Vector(),0,False,False)


class OceanProbe:
    def __init__(self,stage,views=None):
        self.w=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_game_world()
        self.s=u.GameplayStatics.get_all_actors_of_class(self.w,u.SolarSystemActor)[0]
        self.p=u.GameplayStatics.get_player_pawn(self.w,0)
        assert isinstance(self.p,u.SolarExplorerPawn),'PIE required'
        self.saved=dict(focus=self.s.focus_index,seconds=self.s.simulation_seconds,scale=self.s.time_scale,
            pos=self.p.get_actor_location(),rot=self.p.get_actor_rotation(),tick=self.p.is_actor_tick_enabled(),
            auto=self.p.automatic_speed,manual=self.p.manual_speed_km_per_second,speed=self.p.speed_km_per_second)
        self.s.set_time_scale(0);self.s.set_simulation_time(0);self.s.focus_body(3);self.p.set_actor_tick_enabled(False)
        self.stage=stage;self.folder=OUT/stage;self.folder.mkdir(parents=True,exist_ok=True)
        sitefile=OUT/'Sites.json'
        if not sitefile.exists():
            lat,lon=-14.376406312559912,109.8449118967303
            lo,hi=lon-.02,lon
            for _ in range(24):
                mid=(lo+hi)*.5
                if json.loads(self.s.get_surface_region(3,direction(lat,mid)))['height_km']<0:lo=mid
                else:hi=mid
            sites=[dict(name='coast',lat=lat,lon=(lo+hi)*.5-.003,height_m=8,tilt=-.14),
                   dict(name='sea',lat=lat,lon=lon-.1,height_m=12,tilt=-.25),
                   dict(name='underwater',lat=lat,lon=lon-.1,height_m=-20,tilt=-.1),
                   dict(name='underwater-up',lat=lat,lon=lon-.1,height_m=-20,tilt=1.2),
                   dict(name='high-20km',lat=lat,lon=lon-.1,height_m=20000,tilt=-.7),
                   dict(name='handoff-300km',lat=lat,lon=lon-.1,height_m=300000,tilt=-1.2)]
            sitefile.write_text(json.dumps(sites,indent=2),encoding='utf-8')
        self.sites=json.loads(sitefile.read_text(encoding='utf-8'))
        if views:self.sites=[x for x in self.sites if x['name'] in views]
        self.rows=[];self.errors=[];self.index=-1;self.done=False;self.busy=False
        self.camera_check=self.check_movement()
        self.handle=u.register_slate_post_tick_callback(self.tick);self.advance()

    def check_movement(self):
        n=direction(-14.376406312559912,109.7449118967303);r=self.s.bodies[3].radius_km
        rot=u.MathLibrary.make_rot_from_xz(u.Vector(0,0,1).cross(n).normal(),n)
        self.p.set_view_pose(n*((r+.01)*100000),rot)
        manual_speed(self.p,.02)
        for _ in range(30):self.p.apply_flight_input(n*-1.,.1,False,False)
        alt=(self.p.get_actor_location().length()/100000-r)*1000
        for _ in range(80):self.p.apply_flight_input(n*-1.,.1,False,False)
        floor=json.loads(self.s.get_surface_region(3,n))['height_km']*1000
        bottom=(self.p.get_actor_location().length()/100000-r)*1000
        for _ in range(120):self.p.apply_flight_input(n,.1,False,False)
        returned=(self.p.get_actor_location().length()/100000-r)*1000
        return dict(descend_altitude_m=alt,ground_height_m=floor,bottom_clearance_m=bottom-floor,
                    returned_altitude_m=returned,entered_water=alt<-40,seabed_stopped=abs(bottom-floor-3)<.05,exited_water=returned>0)

    def advance(self):
        self.index+=1
        if self.index==len(self.sites):self.finish();return
        site=self.sites[self.index];n=direction(site['lat'],site['lon']);east=u.Vector(0,0,1).cross(n).normal()
        self.s.visit_surface(site['lat'],site['lon'],8)
        self.p.set_view_pose(n*((self.s.bodies[3].radius_km+site['height_m']*.001)*100000),
                             u.MathLibrary.make_rot_from_xz((east+n*site['tilt']).normal(),n))
        self.phase='capture';self.frames=0;self.deadline=time.monotonic()+12

    def tick(self,dt):
        if self.done or self.busy:return
        self.busy=True
        try:
            self.frames+=1
            if time.monotonic()<self.deadline or self.frames<32:return
            if self.phase=='next':self.advance();return
            site=self.sites[self.index]
            if site['height_m']<180000:assert self.s.terrain_blend>.999,'Terrain not ready'
            material=self.s.active_terrain.ocean_material.default_material
            self.rows.append(dict(site=site,pos=self.p.get_actor_location().to_tuple(),rot=self.p.get_actor_rotation().to_tuple(),
                material=material.parent.get_path_name(),blend=self.s.terrain_blend,sun_lux=self.s.sun_light.intensity,
                exposure_bias=self.s.lighting_exposure.settings.auto_exposure_bias,
                cloud_rt=u.SystemLibrary.get_console_variable_int_value('r.VolumetricRenderTarget'),
                ap=u.SystemLibrary.get_console_variable_int_value('r.SkyAtmosphere.AerialPerspectiveLUT.FastApplyOnOpaque')))
            u.SystemLibrary.execute_console_command(self.w,'Shot filename="%s"'%(self.folder/(site['name']+'.png')).as_posix())
            self.phase='next';self.deadline=time.monotonic()+.5;self.frames=0
        except Exception as exc:
            self.errors.append(repr(exc));self.finish();raise
        finally:self.busy=False

    def finish(self):
        if self.done:return
        self.done=True;u.unregister_slate_post_tick_callback(self.handle)
        (OUT/(self.stage+'.json')).write_text(json.dumps(dict(completed=not self.errors,errors=self.errors,
            camera=self.camera_check,frames=self.rows),ensure_ascii=False,indent=2),encoding='utf-8')
        self.s.focus_body(self.saved['focus']);self.s.set_simulation_time(self.saved['seconds']);self.s.set_time_scale(self.saved['scale'])
        self.p.set_view_pose(self.saved['pos'],self.saved['rot']);self.p.set_actor_tick_enabled(self.saved['tick'])
        self.p.speed_km_per_second=self.saved['speed']
        if self.saved['auto']:
            self.p.apply_flight_input(u.Vector(),0,True,True);self.p.apply_flight_input(u.Vector(),0,False,False)
        else:manual_speed(self.p,self.saved['manual'])
        print('OCEAN_PROBE_DONE',self.stage,self.errors)


def start(stage='after',views=None):return OceanProbe(stage,views)
