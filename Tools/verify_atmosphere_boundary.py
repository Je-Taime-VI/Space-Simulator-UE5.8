"""冻结时间，在大气上界两侧检查快速空气透视与逐像素路径。截图需复核。"""
import json
import time
from pathlib import Path
import unreal as u

ROOT = Path(u.Paths.project_dir()).resolve()
OUT = ROOT / 'Saved/Diagnostics/AtmosphereBoundary_20261017'
AP = 'r.SkyAtmosphere.AerialPerspectiveLUT.FastApplyOnOpaque'
SKY = 'r.SkyAtmosphere.FastSkyLUT'


class BoundaryProbe:
    def __init__(self, bodies, variants, stage):
        self.w = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_game_world()
        self.s = u.GameplayStatics.get_all_actors_of_class(self.w, u.SolarSystemActor)[0]
        self.p = u.GameplayStatics.get_player_pawn(self.w, 0)
        assert isinstance(self.p, u.SolarExplorerPawn)
        self.saved = dict(focus=self.s.focus_index, seconds=self.s.simulation_seconds,
                          scale=self.s.time_scale, pos=self.p.get_actor_location(),
                          rot=self.p.get_actor_rotation(), tick=self.p.is_actor_tick_enabled(),
                          speed=self.p.speed_km_per_second,
                          ap=u.SystemLibrary.get_console_variable_int_value(AP),
                          sky=u.SystemLibrary.get_console_variable_int_value(SKY))
        self.s.set_time_scale(0)
        self.p.set_actor_tick_enabled(False)
        self.steps = [(b, label, ap, sky, offset) for b in bodies
                      for label, ap, sky in variants for offset in (.2, -.2)]
        self.stage, self.index = stage, -1
        self.folder = OUT / stage
        self.folder.mkdir(parents=True, exist_ok=True)
        self.rows, self.errors = [], []
        self.done = self.busy = False
        self.handle = u.register_slate_post_tick_callback(self.tick)
        self.advance()

    def cmd(self, cmd):
        u.SystemLibrary.execute_console_command(self.w, cmd)

    def advance(self):
        self.index += 1
        if self.index == len(self.steps):
            self.finish()
            return
        body, label, ap, sky, offset = self.steps[self.index]
        changed = self.s.focus_index != body
        self.s.focus_body(body) if changed else None
        self.cmd('%s %d' % (AP, ap))
        self.cmd('%s %d' % (SKY, sky))
        self.changed = changed
        self.frame, self.phase = 0, 'setup'
        self.deadline = time.monotonic() + 1

    def setup(self):
        body, label, ap, sky, offset = self.steps[self.index]
        sun = self.s.sun_light.get_forward_vector() * -1.
        side = sun.cross(u.Vector(0, 0, 1)).normal()
        n = (sun * .8 + side * .6).normal()
        east = u.Vector(0, 0, 1).cross(n).normal()
        self.altitude = self.s.bodies[body].atmosphere_km + offset
        self.p.set_view_pose(n * ((self.s.bodies[body].radius_km + self.altitude) * 100000),
                             u.MathLibrary.make_rot_from_xz((east - n * .4).normal(), n))
        self.frame, self.phase = 0, 'settle'
        self.deadline = time.monotonic() + (12 if self.changed or self.index == 0 else 2)

    def tick(self, dt):
        if self.done or self.busy:
            return
        self.busy = True
        try:
            self.frame += 1
            if time.monotonic() < self.deadline or self.frame < 16:
                return
            if self.phase == 'setup':
                self.setup()
            elif self.phase == 'settle':
                b, label, ap, sky, offset = self.steps[self.index]
                name = '%s-%s-%s' % (self.s.bodies[b].key, label, 'above' if offset > 0 else 'below')
                self.cmd('Shot filename="%s"' % (self.folder/(name+'.png')).as_posix())
                self.rows.append(dict(name=name, body=b, altitude_km=self.altitude,
                                      ap=u.SystemLibrary.get_console_variable_int_value(AP),
                                      sky=u.SystemLibrary.get_console_variable_int_value(SKY),
                                      cloud_rt=u.SystemLibrary.get_console_variable_int_value('r.VolumetricRenderTarget'),
                                      pos=self.p.get_actor_location().to_tuple(),
                                      rot=self.p.get_actor_rotation().to_tuple(),
                                      diagnostics=json.loads(self.s.get_diagnostics())))
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
        (OUT/(self.stage+'.json')).write_text(json.dumps(dict(completed=not self.errors,
            errors=self.errors, frames=self.rows), ensure_ascii=False, indent=2), encoding='utf-8')
        self.cmd('%s %d' % (AP, self.saved['ap']))
        self.cmd('%s %d' % (SKY, self.saved['sky']))
        self.s.focus_body(self.saved['focus'])
        self.s.set_simulation_time(self.saved['seconds'])
        self.s.set_time_scale(self.saved['scale'])
        self.p.set_view_pose(self.saved['pos'], self.saved['rot'])
        self.p.speed_km_per_second = self.saved['speed']
        self.p.set_actor_tick_enabled(self.saved['tick'])
        print('ATMOSPHERE_BOUNDARY_DONE', self.stage, self.errors)


def start(bodies=(3, 5), variants=(('before', 1, 1), ('candidate', 0, 1)), stage='comparison'):
    return BoundaryProbe(bodies, variants, stage)
