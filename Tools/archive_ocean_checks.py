"""归档海洋阶段一的原始验证与截图，不修改图像内容。"""
import hashlib
import json
import shutil
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'Saved/Diagnostics/Ocean_20261018'
REPORT=ROOT/'Documentation/Verification/2026-10-18/Ocean'
IMAGES=ROOT/'Images/2026-10-18/Ocean'


def main():
    final=json.loads((SOURCE/'endpoints.json').read_text(encoding='utf-8'))
    assert final['completed'] and not final['errors'] and len(final['frames'])==6
    assert all(final['camera'][key] for key in ['entered_water','seabed_stopped','exited_water'])
    boundary=json.loads((SOURCE/'boundary-final.json').read_text(encoding='utf-8'))
    assert boundary['completed'] and not boundary['errors'] and len(boundary['frames'])==2
    materials=json.loads((SOURCE/'MaterialFinal.json').read_text(encoding='utf-8'))
    assert len(materials)==3 and all(row['endpoint_guard'] and row['clip']==.5 for row in materials)
    REPORT.mkdir(parents=True,exist_ok=True);IMAGES.mkdir(parents=True,exist_ok=True)
    files={}
    for name in ['before.json','after.json','precision.json','wrapped.json','final.json','accepted.json','release.json','verified.json','spherical.json','threshold.json','endpoints.json','boundary.json','boundary-final.json','grid-isolation.json','grid-visible.json','Sites.json',
                 'DemoOceanAudit.json','DemoWaterGraph.json','Material.json','MaterialFinal.json',
                 'ModelValidation.json','RetainedSpeed.json']:
        files[SOURCE/name]=REPORT/name
    files[ROOT/'Saved/Logs/OceanBuild.log']=REPORT/'OceanBuild.log'
    files[ROOT/'Saved/Logs/OceanCoverageBuild.log']=REPORT/'OceanCoverageBuild.log'
    for stage in ['before','endpoints']:
        for frame in final['frames']:
            name=frame['site']['name']
            files[SOURCE/stage/(name+'00000.png')]=IMAGES/(name+'-'+('final' if stage=='endpoints' else stage)+'.png')
    for stage,name in [('after','sea'),('after','underwater-up'),('after','handoff-300km')]:
        files[SOURCE/stage/(name+'00000.png')]=IMAGES/(name+'-initial-port.png')
    for stage,name in [('boundary','below-20km'),('boundary','above-20km'),('boundary-final','below-20km'),('boundary-final','above-20km'),('verified','sea'),('grid-isolation','sea')]:
        files[SOURCE/stage/(name+'00000.png')]=IMAGES/(name+'-'+stage+'.png')
    manifest=[]
    for source,dest in files.items():
        assert source.is_file(),source
        shutil.copy2(source,dest)
        digest=hashlib.sha256(source.read_bytes()).hexdigest()
        assert hashlib.sha256(dest.read_bytes()).hexdigest()==digest
        manifest.append(dict(source=source.relative_to(ROOT).as_posix(),archive=dest.relative_to(ROOT).as_posix(),sha256=digest))
    (REPORT/'Manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    print('归档完成：',len(manifest),'个原始文件')


if __name__=='__main__':main()
