"""PIE 云层诊断：同机位、相同移动路径，使用正常视口 Shot 保留时域渲染。

start(compare=True) 对比模式3渲染目标与直接渲染；compare=False 检查工程实际配置。
运行时冻结天文时间，结束恢复调用前的机位、时间和控制。图像需人工复核。
"""
import json
import math
import time
from datetime import datetime
from pathlib import Path
import unreal as u

ROOT = Path(u.Paths.project_dir()).resolve()
OUT = ROOT / 'Saved/Diagnostics/CloudStability'


class CloudProbe:
    def __init__(self, compare):
        self.world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_game_world()
        self.s = u.GameplayStatics.get_all_actors_of_class(self.world, u.SolarSystemActor)[0]
        self.p = u.GameplayStatics.get_player_pawn(self.world, 0)
        assert isinstance(self.p, u.SolarExplorerPawn), 'Requires Play'
        self.saved = dict(focus=self.s.focus_index, seconds=self.s.simulation_seconds,
                          scale=self.s.time_scale, pos=self.p.get_actor_location(),
                          rot=self.p.get_actor_rotation(), tick=self.p.is_actor_tick_enabled(),
                          rt=u.SystemLibrary.get_console_variable_int_value('r.VolumetricRenderTarget'),
                          mode=u.SystemLibrary.get_console_variable_int_value('r.VolumetricRenderTarget.Mode'),
                          samples=self.s.volume_clouds.get_editor_property('view_sample_count_scale'))
        self.s.set_actor_tick_enabled(True)
        self.p.set_actor_tick_enabled(False)
        self.s.set_time_scale(0)
        self.s.set_simulation_time(0)
        self.compare = compare
        variants = [('before', 3, .25), ('candidate', 3, .25)] if compare else [('final', None, None)]
        self.steps = [(body, view, label, mode, samples)
                      for body, view in [(2, 'crescent'), (3, 'orbit'), (3, '20km'),
                                         (3, 'inside'), (2, 'inside')]
                      for label, mode, samples in variants]
        self.index = -1
        self.rows, self.errors = [], []
        self.done = self.busy = False
        self.label = 'comparison' if compare else 'final'
        self.folder = OUT / self.label
        self.folder.mkdir(parents=True, exist_ok=True)
        self.handle = u.register_slate_post_tick_callback(self.tick)
        self.advance()

    def command(self, text):
        u.SystemLibrary.execute_console_command(self.world, text)

    def advance(self):
        self.index += 1
        if self.index == len(self.steps):
            self.finish()
            return
        body, view, label, mode, samples = self.steps[self.index]
        self.s.focus_body(body)
        self.phase = 'setup'
        self.deadline = time.monotonic() + 1

    def setup(self):
        body, view, label, mode, samples = self.steps[self.index]
        # UE Python Vector unary minus mutates its operand; multiplication does not.
        sun = self.s.sun_light.get_forward_vector() * -1.
        side = sun.cross(u.Vector(0, 0, 1)).normal()
        radius = self.s.bodies[body].radius_km
        if view == 'crescent':
            n = (sun * -.65 + side * .76).normal()
            altitude = radius * 3.3
            forward, up = n * -1., u.Vector(0, 0, 1)
        elif view == 'orbit':
            n = (sun + side * .25).normal()
            altitude = radius * 3.3
            forward, up = n * -1., u.Vector(0, 0, 1)
        else:
            candidates = []
            for j in range(512):
                z = 1 - 2 * (j + .5) / 512
                a = j * 2.399963229728653
                n = u.Vector(math.sqrt(1-z*z)*math.cos(a), math.sqrt(1-z*z)*math.sin(a), z)
                if n.dot(sun) > .65:
                    candidates.append((self.s.get_cloud_coverage(n), n))
            n = max(candidates, key=lambda item: item[0])[1] if body == 3 else sun
            altitude = 20 if view == '20km' else (5 if body == 3 else 58)
            east = u.Vector(0, 0, 1).cross(n).normal()
            forward, up = ((east - n * .6).normal(), n)
        self.origin = n * ((radius + altitude) * 100000)
        self.rotation = u.MathLibrary.make_rot_from_xz(forward, up)
        self.p.set_view_pose(self.origin, self.rotation)
        self.travel = self.p.get_actor_right_vector() * (radius * .08 * 100000 if altitude > 100 else 200000)
        if mode is not None:
            self.command('r.VolumetricRenderTarget %d' % (1 if label == 'before' else 0))
            self.command('r.VolumetricRenderTarget.Mode %d' % mode)
            self.s.volume_clouds.set_view_sample_count_scale(samples)
        self.phase = 'settle'
        self.deadline = time.monotonic() + (8 if altitude < 100 else 4)
        self.frame = 0

    def capture(self, suffix):
        body, view, label, mode, samples = self.steps[self.index]
        name = '%s-%s-%s-%s' % ('Earth' if body == 3 else 'Venus', view, label, suffix)
        self.command('Shot filename="%s"' % (self.folder / (name + '.png')).as_posix())
        self.rows.append(dict(name=name, local_time=datetime.now().isoformat(), body=body,
                              rt=u.SystemLibrary.get_console_variable_int_value('r.VolumetricRenderTarget'),
                              view=view, mode=u.SystemLibrary.get_console_variable_int_value('r.VolumetricRenderTarget.Mode'),
                              samples=self.s.volume_clouds.get_editor_property('view_sample_count_scale'),
                              position_cm=self.p.get_actor_location().to_tuple(),
                              rotation=self.p.get_actor_rotation().to_tuple(),
                              visible=self.s.volume_clouds.is_visible()))
        if not self.compare:
            assert self.rows[-1]['rt'] == 0
            assert self.rows[-1]['mode'] == 3
            assert self.rows[-1]['samples'] == .25
            assert self.rows[-1]['visible']
            assert self.s.volume_clouds.get_editor_property('material').get_base_material().get_editor_property('used_with_volumetric_cloud')

    def tick(self, dt):
        if self.busy or self.done or time.monotonic() < self.deadline:
            return
        self.busy = True
        try:
            if self.phase == 'setup':
                self.setup()
            elif self.phase == 'settle':
                self.capture('still')
                u.log('CLOUD_STABILITY_PROFILE ' + self.rows[-1]['name'])
                self.command('r.ProfileGPU.ShowUI 0')
                self.command('profilegpu')
                self.phase = 'move'
                self.deadline = time.monotonic() + .5
            elif self.phase == 'move':
                self.frame += 1
                # Normal render frames, not HighResShot. Pause a callback after each Shot.
                if self.frame in (9, 19, 29, 39):
                    self.capture('move%02d' % self.frame)
                    return
                t = self.frame / 48
                self.p.set_view_pose(self.origin + self.travel * math.sin(t * math.pi * 2), self.rotation)
                if self.frame == 48:
                    self.p.set_view_pose(self.origin, self.rotation)
                    self.phase = 'return'
                    self.deadline = time.monotonic() + 2
            elif self.phase == 'return':
                self.capture('returned')
                self.phase = 'next'
                self.deadline = time.monotonic() + .5
            else:
                self.advance()
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
        (OUT / (self.label + '.json')).write_text(json.dumps(dict(
            completed=not self.errors, errors=self.errors, views=self.rows,
            scope='固定时间平移及返回；图像需人工复核，不把采集完成等同于全部画质通过。'),
            ensure_ascii=False, indent=2), encoding='utf-8')
        self.command('r.VolumetricRenderTarget.Mode %d' % self.saved['mode'])
        self.command('r.VolumetricRenderTarget %d' % self.saved['rt'])
        self.s.focus_body(self.saved['focus'])
        self.s.set_simulation_time(self.saved['seconds'])
        self.s.set_time_scale(self.saved['scale'])
        self.s.volume_clouds.set_view_sample_count_scale(self.saved['samples'])
        self.p.set_view_pose(self.saved['pos'], self.saved['rot'])
        self.p.set_actor_tick_enabled(self.saved['tick'])
        print('CLOUD_STABILITY_DONE', self.label, self.errors)


def start(compare=True):
    return CloudProbe(compare)
