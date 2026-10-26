"""逐机位保存受光校准证据；在 SolarSystem PIE 中调用 start(stage)。"""
import json
import math
import time
from pathlib import Path
import unreal as u

ROOT = Path(u.Paths.project_dir()).resolve()
OUT = ROOT / 'Saved/Diagnostics/SurfaceLighting'
IMAGES = ROOT / 'Images/2026-10-11/SurfaceLighting'


class LightingProbe:
    def __init__(self, stage, views=None):
        self.stage = stage
        self.world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_game_world()
        self.system = u.GameplayStatics.get_all_actors_of_class(self.world, u.SolarSystemActor)[0]
        self.pawn = u.GameplayStatics.get_player_pawn(self.world, 0)
        assert isinstance(self.pawn, u.SolarExplorerPawn), 'Requires Play, not Simulate'
        self.pawn.set_actor_tick_enabled(False)
        self.system.set_time_scale(0)
        self.system.set_simulation_time(0)
        self.views = views or [(3, 'surface'), (4, 'surface'), (5, 'surface'),
                               (2, 'surface'), (3, 'blend'), (3, 'orbit')]
        self.rows, self.errors = [], []
        self.index, self.done, self.busy = -1, False, True
        OUT.mkdir(parents=True, exist_ok=True)
        IMAGES.mkdir(parents=True, exist_ok=True)
        self.handle = u.register_slate_post_tick_callback(self.tick)
        self.next_view()
        self.busy = False

    def next_view(self):
        self.index += 1
        if self.index == len(self.views):
            self.finish()
            return
        body, view = self.views[self.index]
        self.system.focus_body(body)
        if view != 'orbit':
            assert self.system.visit_surface(25, 0, 35)
        if view == 'night':
            reference=json.loads((OUT/'before.json').read_text(encoding='utf-8'))
            day=next(r for r in reference['views'] if r['body']==body and r['view']=='surface')
            n=-u.Vector(*day['position_cm']).normal()
            assert self.system.visit_surface(math.degrees(math.asin(n.z)), math.degrees(math.atan2(n.y, n.x)), 35)
        if view in ['blend', 'low-orbit']:
            n = self.pawn.get_actor_location().normal()
            altitude = 300 if view == 'blend' else 180
            self.pawn.set_view_pose(n * ((self.system.bodies[body].radius_km + altitude) * 100000),
                                   u.MathLibrary.make_rot_from_xz(-n, self.pawn.get_actor_right_vector()))
        self.phase = 'capture'
        self.deadline = time.monotonic() + (8 if view == 'orbit' else 18)

    def tick(self, dt):
        if self.busy or self.done or time.monotonic() < self.deadline:
            return
        self.busy = True
        try:
            if self.phase == 'advance':
                self.next_view()
                return
            body, view = self.views[self.index]
            key = self.system.bodies[body].key.lower()
            row = {'body': body, 'view': view, 'position_cm': self.pawn.get_actor_location().to_tuple(),
                   'rotation': self.pawn.get_actor_rotation().to_tuple(),
                   'sun_intensity': self.system.sun_light.intensity,
                   'diagnostics': json.loads(self.system.get_diagnostics())}
            if self.stage != 'before':
                pp = self.system.lighting_exposure.settings
                row['exposure'] = {'method': str(pp.auto_exposure_method),
                                   'physical': pp.auto_exposure_apply_physical_camera_exposure,
                                   'bias': pp.auto_exposure_bias, 'iso': pp.camera_iso,
                                   'shutter': pp.camera_shutter_speed, 'fstop': pp.depth_of_field_fstop}
                row['sky_intensity'] = self.system.surface_sky_light.intensity
                if pp.auto_exposure_method != u.AutoExposureMethod.AEM_MANUAL:
                    self.errors.append(key + ': exposure is not manual')
                if body in [1, 4] and row['sky_intensity'] != 0:
                    self.errors.append(key + ': atmospheric sky fill on airless body')
            if view in ['surface', 'night'] and row['diagnostics']['terrain_blend'] < .999:
                self.errors.append(key + ': terrain did not finish loading')
            self.rows.append(row)
            u.AutomationLibrary.take_high_res_screenshot(1280, 720, str(IMAGES / (key + '-' + view + '-' + self.stage + '.png')))
            self.phase, self.deadline = 'advance', time.monotonic() + 2
        except Exception as exc:
            self.errors.append(repr(exc))
            self.finish()
            raise
        finally:
            self.busy = False

    def finish(self):
        if self.done:
            return
        self.done = True
        u.unregister_slate_post_tick_callback(self.handle)
        (OUT / (self.stage + '.json')).write_text(json.dumps({'success': not self.errors,
            'errors': self.errors, 'views': self.rows}, ensure_ascii=False, indent=2), encoding='utf-8')
        print('SURFACE_LIGHTING_PROBE_DONE', self.stage, self.errors)
        self.pawn.set_actor_tick_enabled(True)
        self.world = self.system = self.pawn = None


def inspect_materials_and_light():
    """读取最终材质连接与所有天体照度/曝光；不改写运行资产。"""
    world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_game_world()
    system=u.GameplayStatics.get_all_actors_of_class(world,u.SolarSystemActor)[0]
    pawn=u.GameplayStatics.get_player_pawn(world,0)
    rows=[]
    for name in ['M_Terrain','M_Ocean','M_Planet','M_Star','M_Clouds','M_PlanetCloudVolume','M_Rings','M_Atmosphere']:
        m=u.load_asset('/Game/SolarSystem/Materials/'+name)
        stats=u.MaterialEditingLibrary.get_statistics(m)
        row={'material':name,'shading':str(m.get_editor_property('shading_model')),
             'pixel_instructions':stats.num_pixel_shader_instructions,
             'vertex_instructions':stats.num_vertex_shader_instructions}
        if name in ['M_Terrain','M_Ocean']:
            assert m.get_editor_property('shading_model')==u.MaterialShadingModel.MSM_DEFAULT_LIT
            base=u.MaterialEditingLibrary.get_material_property_input_node(m,u.MaterialProperty.MP_BASE_COLOR)
            emissive=u.MaterialEditingLibrary.get_material_property_input_node(m,u.MaterialProperty.MP_EMISSIVE_COLOR)
            row['base_color_connected']=base is not None
            row['emissive_constant']=emissive.get_editor_property('r')
            assert base and row['emissive_constant']==0
        assert stats.num_pixel_shader_instructions>0, name
        rows.append(row)
    pp=system.lighting_exposure.settings
    assert pp.auto_exposure_method==u.AutoExposureMethod.AEM_MANUAL
    assert pp.auto_exposure_apply_physical_camera_exposure
    report={'materials':rows,'reference_lux':system.solar_illuminance_at_one_au,
            'physical_exposure':True,'base_ev100':math.log2(pp.depth_of_field_fstop**2*pp.camera_shutter_speed*100/pp.camera_iso),
            'scope':'编译后材质统计与连接检查；画面和昼夜另由截图与运行记录验证。'}
    (OUT/'MaterialAudit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    return report


def start(stage, views=None):
    global probe
    probe = LightingProbe(stage, views)
    return probe


class LightResponseProbe:
    """同机位光照开关对照；结束时恢复太阳和天空光，不保存诊断状态。"""
    def __init__(self):
        self.world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_game_world()
        self.system=u.GameplayStatics.get_all_actors_of_class(self.world,u.SolarSystemActor)[0]
        self.pawn=u.GameplayStatics.get_player_pawn(self.world,0)
        self.system.set_actor_tick_enabled(True)
        self.pawn.set_actor_tick_enabled(False)
        self.system.set_time_scale(0)
        self.system.set_simulation_time(0)
        self.system.focus_body(3)
        self.system.visit_surface(25,0,35)
        self.phase=0
        self.deadline=time.monotonic()+20
        self.samples=[]
        self.done=False
        self.handle=u.register_slate_post_tick_callback(self.tick)

    def capture(self,name):
        u.AutomationLibrary.take_high_res_screenshot(1280,720,str(IMAGES/(name+'.png')))

    def tick(self,dt):
        if self.done or time.monotonic()<self.deadline:return
        pp=self.system.lighting_exposure.settings
        self.samples.append({'phase':self.phase,'bias':pp.auto_exposure_bias,
                             'method':str(pp.auto_exposure_method),
                             'sun':self.system.sun_light.intensity,'sky':self.system.surface_sky_light.intensity})
        if self.phase==0:
            self.capture('earth-light-on')
            self.rotation=self.pawn.get_actor_rotation()
            self.sun=self.system.sun_light.intensity
            self.sky=self.system.surface_sky_light.intensity
        elif self.phase==1:
            self.system.set_actor_tick_enabled(False)
            self.system.sun_light.set_intensity(0)
            self.system.surface_sky_light.set_intensity(0)
        elif self.phase==2:
            self.capture('earth-light-off-diagnostic')
        elif self.phase==3:
            self.system.sun_light.set_intensity(self.sun)
            self.system.surface_sky_light.set_intensity(self.sky)
            self.system.set_actor_tick_enabled(True)
            self.pawn.set_actor_rotation(u.MathLibrary.make_rot_from_xz(-self.pawn.get_actor_forward_vector(),self.pawn.get_actor_up_vector()),False)
        elif self.phase==4:
            self.capture('earth-opposite-view')
        elif self.phase==5:
            self.pawn.set_actor_rotation(self.rotation,False)
        elif self.phase==6:
            self.capture('earth-light-restored')
            u.SystemLibrary.execute_console_command(self.world,'r.ProfileGPU.ShowUI 0')
            u.log('SURFACE_LIGHTING_FINAL_GPU_SAMPLE')
            u.SystemLibrary.execute_console_command(self.world,'profilegpu')
        else:
            self.done=True
            u.unregister_slate_post_tick_callback(self.handle)
            stable=len(set(round(x['bias'],7) for x in self.samples))==1
            assert stable and all('AEM_MANUAL' in x['method'] for x in self.samples)
            (OUT/'LightResponse.json').write_text(json.dumps({'fixed_exposure':stable,'samples':self.samples,
                'scope':'同机位太阳与天空光关闭/恢复；关灯画面仅为诊断。转向检查记录固定曝光设置，不等同逐帧亮度计测量。'},ensure_ascii=False,indent=2),encoding='utf-8')
            self.pawn.set_actor_tick_enabled(True)
            self.system.set_time_scale(1)
            self.system=self.world=self.pawn=None
            print('LIGHT_RESPONSE_DONE')
        self.phase+=1
        self.deadline=time.monotonic()+3
