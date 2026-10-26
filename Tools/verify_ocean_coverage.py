"""岸线、深水与海洋交接的固定机位隔离检查；不修改资源。"""
import json, math, time
from pathlib import Path
import unreal as u
from verify_solar_ocean import direction

OUT=Path(u.Paths.project_dir())/'Saved/Diagnostics/OceanCoverage_20261019'

class Probe:
    def __init__(self,stage,jobs):
        self.w=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_game_world()
        self.s=u.GameplayStatics.get_all_actors_of_class(self.w,u.SolarSystemActor)[0]
        self.p=u.GameplayStatics.get_player_pawn(self.w,0)
        self.saved=(self.p.get_actor_location(),self.p.get_actor_rotation(),self.p.is_actor_tick_enabled(),self.s.simulation_seconds,self.s.time_scale,self.s.is_actor_tick_enabled())
        self.s.set_time_scale(0);self.s.set_simulation_time(0);self.p.set_actor_tick_enabled(False)
        self.body=next(c for c in self.s.get_components_by_class(u.StaticMeshComponent) if c.get_name().startswith('Body_Earth'))
        self.atmos=self.s.get_components_by_class(u.SkyAtmosphereComponent)[0]
        self.bottom=self.atmos.get_editor_property('bottom_radius')
        self.stage=stage;self.jobs=jobs;self.folder=OUT/stage;self.folder.mkdir(parents=True,exist_ok=True)
        self.rows=[];self.errors=[];self.index=-1;self.done=False;self.busy=False
        self.handle=u.register_slate_post_tick_callback(self.tick);self.advance()

    def ocean_meshes(self):
        return [c for c in self.s.active_terrain.get_components_by_class(u.MeshComponent)
                if c.get_material(0) and 'Ocean' in c.get_material(0).get_name()]

    def advance(self):
        self.index+=1
        if self.index==len(self.jobs):self.finish();return
        self.s.set_actor_tick_enabled(True)
        self.job=self.jobs[self.index];j=self.job;n=direction(j['lat'],j['lon'])
        east=u.Vector(0,0,1).cross(n).normal()*j.get('east',1)
        self.s.visit_surface(j['lat'],j['lon'],12)
        self.p.set_view_pose(n*((self.s.bodies[3].radius_km+j['alt'])*100000),u.MathLibrary.make_rot_from_xz((east+n*j.get('tilt',-.15)).normal(),n))
        self.body.set_hidden_in_game(j.get('hide_proxy',False))
        self.atmos.set_visibility(not j.get('hide_atmos',False))
        # UpdateTerrain resets ocean visibility every game tick. Disable that
        # writer for isolation shots, while WorldScape continues generating LODs.
        self.frames=0;self.deadline=time.monotonic()+8;self.phase='settle'

    def tick(self,dt):
        if self.done or self.busy:return
        self.busy=True
        try:
            self.frames+=1
            if self.frames<16 or time.monotonic()<self.deadline:return
            if self.phase=='next':self.advance();return
            if self.phase=='settle':
                self.s.set_actor_tick_enabled(False)
                for c in self.ocean_meshes():c.set_hidden_in_game(self.job.get('hide_ocean',False) or self.job['alt']>=20)
                self.phase='capture';self.frames=0;self.deadline=time.monotonic()+1
                return
            floor=json.loads(self.s.get_surface_region(3,self.p.get_actor_location().normal()))['height_km']
            self.rows.append(dict(job=self.job,ground_km=floor,blend=self.s.terrain_blend,ocean_hidden=[c.hidden_in_game for c in self.ocean_meshes()],system_tick=self.s.is_actor_tick_enabled(),position=self.p.get_actor_location().to_tuple(),rotation=self.p.get_actor_rotation().to_tuple()))
            u.SystemLibrary.execute_console_command(self.w,'Shot filename="%s"'%(self.folder/(self.job['name']+'.png')).as_posix())
            self.phase='next';self.frames=0;self.deadline=time.monotonic()+.5
        except Exception as exc:
            self.errors.append(repr(exc));self.finish();raise
        finally:self.busy=False

    def finish(self):
        if self.done:return
        self.done=True;u.unregister_slate_post_tick_callback(self.handle)
        self.body.set_hidden_in_game(False);self.atmos.set_visibility(True)
        for c in self.ocean_meshes():c.set_hidden_in_game(False)
        self.p.set_view_pose(self.saved[0],self.saved[1]);self.p.set_actor_tick_enabled(self.saved[2])
        self.s.set_simulation_time(self.saved[3]);self.s.set_time_scale(self.saved[4])
        self.s.set_actor_tick_enabled(self.saved[5])
        (OUT/(self.stage+'.json')).write_text(json.dumps(dict(completed=not self.errors,errors=self.errors,frames=self.rows),ensure_ascii=False,indent=2),encoding='utf-8')
        print('OCEAN_COVERAGE_DONE',self.stage,self.errors)

def start(stage,jobs):return Probe(stage,jobs)
