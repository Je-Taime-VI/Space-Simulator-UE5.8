"""太阳系远景回归：三颗岩质天体、地球云层与交接高度、金星云层。

在 SolarSystem 的 PIE 中调用 start()。截图保留在本轮开始日期目录；
报告记录实际运行时间。使用固定时刻/机位，不修改地图或星表。
"""
import importlib.util
import json
import time
from datetime import datetime
from pathlib import Path
import unreal as u

ROOT=Path(u.Paths.project_dir()).resolve()
OUT=ROOT/'Saved/Diagnostics/OrbitalAppearance'
IMAGES=ROOT/'Images/2026-10-15/OrbitalAppearance'


def start():
    spec=importlib.util.spec_from_file_location('orbital_surface_probe',ROOT/'Tools/verify_surface_materials.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    module.OUT=OUT;module.IMAGES=IMAGES

    class OrbitalProbe(module.SurfaceProbe):
        def advance(self):
            super().advance()
            if self.done:return
            site=self.sites[self.index]
            if 'alt_km' in site:
                radius=self.system.bodies[site['body']].radius_km
                normal=self.pawn.get_actor_location().normal()
                self.pawn.set_view_pose(normal*((radius+site['alt_km'])*100000),self.pawn.get_actor_rotation())
                self.deadline=time.monotonic()+18
            if site.get('offset'):
                location=self.pawn.get_actor_location()
                self.pawn.set_view_pose(location+self.pawn.get_actor_right_vector()*5000000,self.pawn.get_actor_rotation())

        def finish(self):
            if self.done:return
            super().finish()
            report=json.loads((OUT/'final.json').read_text(encoding='utf-8'))
            report['finished_local']=datetime.now().isoformat()
            report['cloud_settings']={k:u.SystemLibrary.get_console_variable_int_value(k) for k in
                ['r.VolumetricRenderTarget','r.VolumetricRenderTarget.Mode','r.VolumetricRenderTarget.UpsamplingMode','r.VolumetricCloud']}
            report['material_statistics']={}
            for name in ['M_Planet','M_Terrain']:
                stats=u.MaterialEditingLibrary.get_statistics(u.load_asset('/Game/SolarSystem/Materials/'+name))
                report['material_statistics'][name]={'pixel_instructions':stats.num_pixel_shader_instructions,'samplers':stats.num_samplers}
            (OUT/'final.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')

    sites=[{'body':i,'name':name,'orbit':True} for i,name in [(1,'Mercury'),(4,'Moon'),(5,'Mars'),(3,'Earth-orbit-cloud')]]
    sites += [dict(body=3,name='Earth-orbit-offset',orbit=True,offset=True),
              dict(body=3,name='Earth-transition',orbit=True,alt_km=315),
              dict(body=3,name='Earth-20km',orbit=True,alt_km=20),
              dict(body=2,name='Venus-orbit-cloud',orbit=True)]
    return OrbitalProbe('final',sites)
