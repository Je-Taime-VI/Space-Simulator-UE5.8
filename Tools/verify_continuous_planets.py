"""在 SolarSystem 的 PIE 中检查逐天体外观及不改变机位的连续下降。"""
import json
import math
import time
from pathlib import Path
import unreal as u

ROOT=Path(u.Paths.project_dir()).resolve()
OUT=ROOT/'Saved/Diagnostics/ContinuousPlanets'
IMAGES=ROOT/'Images/2026-10-10'


class ContinuousProbe:
    def __init__(self,views=None,do_descent=True,output_name='Verification.json'):
        OUT.mkdir(parents=True,exist_ok=True);IMAGES.mkdir(parents=True,exist_ok=True)
        self.world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_game_world()
        assert self.world
        self.system=u.GameplayStatics.get_all_actors_of_class(self.world,u.SolarSystemActor)[0]
        self.pawn=u.GameplayStatics.get_player_pawn(self.world,0)
        assert isinstance(self.pawn,u.SolarExplorerPawn)
        self.pawn.set_actor_tick_enabled(False)
        self.system.set_time_scale(0);self.system.set_simulation_time(0)
        self.steps=[('orbit',i) for i in range(10)]+[('surface',i) for i in [1,2,3,4,5]]+[('clouds',3)]
        if views is not None:self.steps=views
        self.do_descent=do_descent;self.output_name=output_name
        self.index=-1;self.rows=[];self.frames=[];self.failures=[]
        self.busy=True;self.done=False;self.phase='views';self.started=time.monotonic()
        self.handle=u.register_slate_post_tick_callback(self.tick)
        self.next_view();self.busy=False

    def next_view(self):
        self.index+=1
        if self.index>=len(self.steps):
            if self.do_descent:self.start_descent()
            else:self.finish()
            return
        mode,index=self.steps[self.index]
        self.system.focus_body(index)
        if mode=='surface':assert self.system.visit_surface(25,0,35)
        if mode=='clouds':
            sun=-self.system.sun_light.get_forward_vector()
            candidates=[]
            for j in range(512):
                z=1-2*(j+.5)/512;a=j*2.399963229728653
                n=u.Vector(math.sqrt(1-z*z)*math.cos(a),math.sqrt(1-z*z)*math.sin(a),z)
                if n.dot(sun)>.65:candidates.append((self.system.get_cloud_coverage(n),n))
            cover,n=max(candidates,key=lambda x:x[0]);assert cover>.7
            assert self.system.visit_surface(math.degrees(math.asin(n.z)),math.degrees(math.atan2(n.y,n.x)),35)
            self.pawn.set_actor_rotation(u.MathLibrary.make_rot_from_xz(n,self.pawn.get_actor_right_vector()),False)
        self.deadline=time.monotonic()+(15 if mode!='orbit' else 5)
        self.captured=False

    def capture_view(self):
        mode,index=self.steps[self.index]
        d=json.loads(self.system.get_diagnostics());key=d['bodies'][index]['key'].lower()
        row={'body':key,'view':mode,'atmosphere':d['atmosphere'],'clouds':d['volumetric_clouds'],
             'terrain_blend':d['terrain_blend'],'camera_cm':self.pawn.get_actor_location().to_tuple(),
             'cloud_column':d.get('earth_cloud_column')}
        if index in [2,3]:
            mat=self.system.volume_clouds.get_editor_property('material').get_base_material()
            if not mat.get_editor_property('used_with_volumetric_cloud'):self.failures.append(key+': cloud material usage missing')
        if mode=='surface':
            t=self.system.active_terrain
            row['lod_count']=len(t.world_scape_lod)
            row['invalid_bounds']=sum(not all(math.isfinite(v) for v in (*o.to_tuple(),*e.to_tuple(),r))
                for o,e,r in [u.SystemLibrary.get_component_bounds(l.mesh) for l in t.world_scape_lod])
            row['ground_cm']=t.get_ground_height(self.pawn.get_actor_location())
            row['clearance_m']=(self.pawn.get_actor_location().length()-t.planet_scale-row['ground_cm'])/100
            if row['invalid_bounds'] or row['terrain_blend']<.999:self.failures.append(key+': terrain not ready')
        if index in [1,4] and row['atmosphere']:self.failures.append(key+': unexpected atmosphere')
        if index in [2,3,5,6,7,8,9] and not row['atmosphere']:self.failures.append(key+': missing atmosphere')
        if index in [2,3] and not row['clouds']:self.failures.append(key+': missing cloud volume')
        self.rows.append(row)
        u.AutomationLibrary.take_high_res_screenshot(1280,720,str(IMAGES/(key+'-'+mode+'-after.png')))
        self.captured=True;self.deadline=time.monotonic()+1

    def start_descent(self):
        self.phase='descent';self.system.focus_body(3);self.system.visit_surface(25,0,35)
        self.normal=self.pawn.get_actor_location().normal()
        self.ground_km=(self.pawn.get_actor_location().length()/100000)-.035
        # Keep one orientation through the entire descent, independent of LOD state.
        east=u.Vector(0,0,1).cross(self.normal).normal()
        forward=(east*.94-self.normal*.342).normal()
        self.rotation=u.MathLibrary.make_rot_from_xz(forward,self.normal)
        self.pawn.speed_km_per_second=321.0
        self.route_heights=[1200,800,488.53,460,450,400,300,220,180,100,70,30,10,7,5,3,1,.2,.035]
        self.route_index=0;self.sent=None;self.segment_frames=0;self.ready_at=time.monotonic()+15
        self.at_altitude(1200)

    def at_altitude(self,height):
        p=self.normal*((self.ground_km+height)*100000)
        self.pawn.set_view_pose(p,self.rotation)
        self.sent=p

    def descent_tick(self):
        if time.monotonic()<self.ready_at:return
        p=self.pawn.get_actor_location();rotation=self.pawn.get_actor_rotation()
        error=(p-self.sent).length()
        angle=max(abs(rotation.pitch-self.rotation.pitch),abs(rotation.yaw-self.rotation.yaw),abs(rotation.roll-self.rotation.roll))
        d=json.loads(self.system.get_diagnostics())
        self.frames.append({'position_error_cm':error,'angle_error_deg':angle,'speed_limit_setting':self.pawn.speed_km_per_second,
                            'clearance_km':p.length()/100000-self.ground_km,'blend':d['terrain_blend'],
                            'clouds':d['volumetric_clouds'],'atmosphere':d['atmosphere']})
        if error>.1 or angle>.001 or self.pawn.speed_km_per_second!=321:
            self.failures.append('Streaming changed camera pose or speed')
        if not d['volumetric_clouds'] or not d['atmosphere']:self.failures.append('Cloud/atmosphere disappeared during descent')
        # 24 successive positions per altitude interval, no VisitSurface/FocusBody calls.
        a,b=self.route_heights[self.route_index:self.route_index+2]
        if self.segment_frames>=24:
            self.route_index+=1;self.segment_frames=0
            if b in [488.53,220,70,10,5,1,.035]:
                tag=str(b).replace('.','p')
                u.AutomationLibrary.take_high_res_screenshot(1280,720,str(IMAGES/('earth-descent-'+tag+'km-after.png')))
            if self.route_index>=len(self.route_heights)-1:
                self.finish();return
            self.ready_at=time.monotonic()+2
            return
        self.segment_frames+=1
        t=self.segment_frames/24
        self.at_altitude(math.exp(math.log(a)*(1-t)+math.log(b)*t))

    def tick(self,dt):
        if self.busy or self.done:return
        self.busy=True
        try:
            if self.phase=='descent':self.descent_tick()
            elif time.monotonic()>=self.deadline:
                if self.captured:self.next_view()
                else:self.capture_view()
        except Exception as e:
            self.failures.append(repr(e));self.finish();raise
        finally:self.busy=False

    def finish(self):
        if self.done:return
        self.done=True;u.unregister_slate_post_tick_callback(self.handle)
        model=json.loads(self.system.validate_model())
        if not model['success']:self.failures.append('Model validation failed')
        if len(self.rows)!=len(self.steps):self.failures.append('Incomplete body views')
        if self.do_descent and len(self.frames)<430:self.failures.append('Incomplete continuous descent')
        # A frame conversion must preserve the logical location, including at Neptune scale.
        initial=json.loads(self.system.get_diagnostics())
        logical=u.Vector(*initial['logical_position_km']);reframes=[]
        for index in range(10):
            self.system.reframe_body(index)
            after=u.Vector(*json.loads(self.system.get_diagnostics())['logical_position_km'])
            error=(after-logical).length();reframes.append({'body':index,'position_error_km':error})
            if error>.00001:self.failures.append('Frame conversion changed logical position')
        self.system.reframe_body(initial['focus'])
        report={'success':not self.failures,'failures':sorted(set(self.failures)),'model':model,'views':self.rows,
                'descent_frames':self.frames,'frame_conversions':reframes,'duration_seconds':time.monotonic()-self.started,
                'scope':('固定纪元、逐天体外观、脚本逐帧连续下降。' if self.do_descent else '最终材质补充回归，不重复下降。')+'画面仍需逐张检查，未模拟物理键盘和航天器动力学。'}
        (OUT/self.output_name).write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
        self.system.set_time_scale(1);self.pawn.speed_km_per_second=.08;self.pawn.set_actor_tick_enabled(True)
        print('CONTINUOUS_VALIDATION_DONE',report['success'],report['failures'])
        self.world=self.system=self.pawn=None


continuous_probe=ContinuousProbe(**globals().get('PROBE_OPTIONS',{}))
