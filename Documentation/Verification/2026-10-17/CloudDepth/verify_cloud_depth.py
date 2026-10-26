"""太阳系远距云连续帧对照。冻结时间，覆盖静止、微动和返回原位。

在PIE中调用start()；原始帧写入Saved，使用正常Shot而非HighResShot。
不把采集成功当作画面无缺陷；需另行比较连续帧与地表遮挡。
"""
import json
import math
from pathlib import Path
import unreal as u

ROOT = Path(u.Paths.project_dir()).resolve()
OUT = ROOT / 'Saved/Diagnostics/CloudDepth_20261017'


class CloudDepthProbe:
    def __init__(self, values, stage):
        self.world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_game_world()
        self.s = u.GameplayStatics.get_all_actors_of_class(self.world, u.SolarSystemActor)[0]
        self.p = u.GameplayStatics.get_player_pawn(self.world, 0)
        assert isinstance(self.p, u.SolarExplorerPawn)
        self.saved = dict(scale=self.s.time_scale, tick=self.p.is_actor_tick_enabled(),
                          rt=u.SystemLibrary.get_console_variable_int_value('r.VolumetricRenderTarget'))
        self.s.set_time_scale(0)
        self.p.set_actor_tick_enabled(False)
        self.origin = self.p.get_actor_location()
        self.rotation = self.p.get_actor_rotation()
        self.right = self.p.get_actor_right_vector()
        self.forward = self.p.get_actor_forward_vector()
        self.up = self.p.get_actor_up_vector()
        self.values, self.stage = list(values), stage
        self.folder = OUT / stage
        self.folder.mkdir(parents=True, exist_ok=True)
        self.index = -1
        self.rows, self.errors = [], []
        self.done = self.busy = False
        self.handle = u.register_slate_post_tick_callback(self.tick)
        self.advance()

    def command(self, text):
        u.SystemLibrary.execute_console_command(self.world, text)

    def advance(self):
        self.index += 1
        if self.index == len(self.values):
            self.finish()
            return
        self.command('r.VolumetricRenderTarget %d' % self.values[self.index])
        self.p.set_view_pose(self.origin, self.rotation)
        self.frame = -24  # Warm normal render histories before measurement.

    def tick(self, dt):
        if self.done or self.busy:
            return
        self.busy = True
        try:
            self.frame += 1
            if self.frame < 0:
                return
            if self.frame >= 64:
                self.advance()
                return
            if self.frame == 0:
                u.log('CLOUD_DEPTH_PROFILE %s rt=%d' % (self.stage, self.values[self.index]))
                self.command('r.ProfileGPU.ShowUI 0')
                self.command('profilegpu')
            if self.frame in range(0, 16) or self.frame in range(16, 40) or self.frame in range(48, 64):
                phase = 'still' if self.frame < 16 else 'move' if self.frame < 40 else 'returned'
                name = 'rt%d-%s-%03d' % (self.values[self.index], phase, self.frame)
                self.command('Shot filename="%s"' % (self.folder / (name + '.png')).as_posix())
                self.rows.append(dict(name=name, phase=phase, rt=self.values[self.index],
                                      position_cm=self.p.get_actor_location().to_tuple(),
                                      rotation=self.p.get_actor_rotation().to_tuple(),
                                      simulation_seconds=self.s.simulation_seconds))
            # Pose changes apply to subsequent normal render frames.
            if 15 <= self.frame < 39:
                t = (self.frame - 15) / 24
                offset = math.sin(t * math.pi * 2)
                forward = u.MathLibrary.rotate_angle_axis(self.forward, offset * .3, self.up)
                self.p.set_view_pose(self.origin + self.right * (offset * 10000000),
                                     u.MathLibrary.make_rot_from_xz(forward, self.up))
            elif self.frame == 39:
                self.p.set_view_pose(self.origin, self.rotation)
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
        report = dict(completed=not self.errors, errors=self.errors, rows=self.rows,
                      stage=self.stage, time_frozen=True,
                      scope='正常视口连续帧；静止16帧、微动24帧、返回16帧；采集完成与图像判断分开。')
        (OUT / (self.stage + '.json')).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
        self.p.set_view_pose(self.origin, self.rotation)
        self.s.set_time_scale(self.saved['scale'])
        self.p.set_actor_tick_enabled(self.saved['tick'])
        self.command('r.VolumetricRenderTarget %d' % self.saved['rt'])
        print('CLOUD_DEPTH_DONE', self.stage, self.errors)


def start(values=(1, 0), stage='comparison'):
    return CloudDepthProbe(values, stage)
