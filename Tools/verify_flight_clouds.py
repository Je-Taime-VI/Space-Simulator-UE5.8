"""PIE 回归：实际飞行函数、云采样设置、固定机位 GPU 事件与真实截图。"""
import json
import math
import time
from pathlib import Path
import unreal as u

ROOT=Path(u.Paths.project_dir()).resolve()
OUT=ROOT/'Saved/Diagnostics/CloudPerf'
IMAGES=ROOT/'Images/2026-10-10/CloudPerformance'


class FlightCloudProbe:
    def __init__(self):
        OUT.mkdir(parents=True,exist_ok=True);IMAGES.mkdir(parents=True,exist_ok=True)
        self.world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_game_world()
        self.system=u.GameplayStatics.get_all_actors_of_class(self.world,u.SolarSystemActor)[0]
        self.pawn=u.GameplayStatics.get_player_pawn(self.world,0)
        self.pawn.set_actor_tick_enabled(False)
        self.system.set_time_scale(0);self.system.set_simulation_time(0)
        self.rows=[];self.controls=[];self.failures=[];self.switches=[]
        self.config={k:u.SystemLibrary.get_console_variable_int_value(k) for k in ['r.VolumetricRenderTarget','r.VolumetricRenderTarget.Mode']}
        self.config['reprojection_distance_km']=u.SystemLibrary.get_console_variable_float_value('r.VolumetricRenderTarget.MinimumDistanceKmToEnableReprojection')
        assert self.config=={'r.VolumetricRenderTarget':0,'r.VolumetricRenderTarget.Mode':3,'reprojection_distance_km':4.0},self.config
        self.test_movement()
        self.steps=[(3,'orbit'),(2,'orbit'),(3,'orbit-repeat'),(2,'orbit-repeat'),
                    (3,'low-orbit'),(3,'inside'),(3,'surface'),(2,'inside'),(2,'surface')]
        self.index=-1;self.busy=True;self.done=False
        u.SystemLibrary.execute_console_command(self.world,'r.ProfileGPU.ShowUI 0')
        self.handle=u.register_slate_post_tick_callback(self.tick)
        self.next_view();self.busy=False

    def test_movement(self):
        import importlib.util
        spec=importlib.util.spec_from_file_location('retained_speed_checks',ROOT/'Tools/verify_retained_speed.py')
        checks=importlib.util.module_from_spec(spec)
        spec.loader.exec_module(checks)
        rows,failures=checks.verify_speed_controls(self.system,self.pawn)
        self.controls.extend(rows);self.failures.extend(failures)

    def next_view(self):
        self.index+=1
        if self.index==len(self.steps):self.finish();return
        index,mode=self.steps[self.index]
        start=time.perf_counter();self.system.focus_body(index)
        self.switches.append({'body':index,'view':mode,'focus_call_ms':(time.perf_counter()-start)*1000})
        if mode not in ['orbit','orbit-repeat']:
            if mode=='inside' and index==3:
                sun=-self.system.sun_light.get_forward_vector();candidates=[]
                for j in range(512):
                    z=1-2*(j+.5)/512;a=j*2.399963229728653
                    n=u.Vector(math.sqrt(1-z*z)*math.cos(a),math.sqrt(1-z*z)*math.sin(a),z)
                    if n.dot(sun)>.65:candidates.append((self.system.get_cloud_coverage(n),n))
                _,n=max(candidates,key=lambda x:x[0])
                self.system.visit_surface(math.degrees(math.asin(n.z)),math.degrees(math.atan2(n.y,n.x)),35)
            else:self.system.visit_surface(25,0,35)
            n=self.pawn.get_actor_location().normal()
            if mode=='low-orbit':
                self.pawn.set_view_pose(n*((6371.0084+488.53)*100000),u.MathLibrary.make_rot_from_xz(-n,self.pawn.get_actor_right_vector()))
            if mode=='inside':
                radius=self.system.bodies[index].radius_km
                altitude=5 if index==3 else 58
                self.pawn.set_actor_location(n*((radius+altitude)*100000),False,False)
        self.pawn.apply_flight_input(u.Vector(),0,False,False)
        self.deadline=time.monotonic()+(12 if mode not in ['orbit','orbit-repeat'] else 6)
        self.phase='profile';self.samples=0

    def tick(self,dt):
        if self.busy or self.done or time.monotonic()<self.deadline:return
        self.busy=True
        try:
            body,mode=self.steps[self.index]
            if self.phase=='profile':
                u.log('CLOUD_FINAL_PROFILE body=%d view=%s sample=%d'%(body,mode,self.samples))
                u.SystemLibrary.execute_console_command(self.world,'profilegpu')
                self.samples+=1
                if self.samples>=(3 if mode=='orbit' else 1):self.phase='capture'
                self.deadline=time.monotonic()+2
            elif self.phase=='capture':
                cloud=self.system.volume_clouds
                row={'body':body,'view':mode,'camera_cm':self.pawn.get_actor_location().to_tuple(),
                     'cloud_visible':cloud.is_visible(),
                     'view_sample_scale':cloud.get_editor_property('view_sample_count_scale'),
                     'material_usage':cloud.get_editor_property('material').get_base_material().get_editor_property('used_with_volumetric_cloud')}
                self.rows.append(row)
                if not row['cloud_visible'] or not row['material_usage'] or row['view_sample_scale']!=.25:self.failures.append('cloud configuration')
                name=('earth' if body==3 else 'venus')+'-'+mode+'-after.png'
                u.AutomationLibrary.take_high_res_screenshot(1280,720,str(IMAGES/name))
                self.phase='advance';self.deadline=time.monotonic()+2
            else:self.next_view()
        except Exception as e:
            self.failures.append(repr(e));self.finish();raise
        finally:self.busy=False

    def finish(self):
        if self.done:return
        self.done=True;u.unregister_slate_post_tick_callback(self.handle)
        if len(self.rows)!=len(self.steps):self.failures.append('incomplete views')
        report={'success':not self.failures,'failures':self.failures,'config':self.config,
                'movement':self.controls,'views':self.rows,'switch_calls':self.switches,
                'scope':'冻结输入后调用与键盘共用的 C++ 飞行函数；未模拟物理按键。GPU 事件另存日志，截图需人工检查；切换调用耗时不是首帧显示延迟。'}
        (OUT/'FlightCloudVerification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
        self.system.focus_body(3);self.system.visit_surface(25,0,35)
        self.system.set_time_scale(1);self.pawn.set_actor_tick_enabled(True)
        print('FLIGHT_CLOUD_VERIFICATION',report['success'],self.failures)
        self.pawn=self.system=self.world=None


flight_cloud_probe=FlightCloudProbe()
