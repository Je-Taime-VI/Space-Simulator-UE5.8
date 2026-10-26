"""检查星环采集元数据、统计同机位波动并归档真实视口图像。"""
import json
import shutil
from pathlib import Path
import numpy as np
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'Saved/Diagnostics/PlanetRings_20261017'
PROOF=ROOT/'Documentation/Verification/2026-10-17/PlanetRings'
IMAGES=ROOT/'Images/2026-10-17/PlanetRings'


def read(name):return json.loads((SOURCE/(name+'.json')).read_text(encoding='utf-8'))
def image(stage,name):
    files=sorted((SOURCE/stage).glob(name+'*.png'))
    assert files,(stage,name)
    return files[-1]


def main():
    PROOF.mkdir(parents=True,exist_ok=True);IMAGES.mkdir(parents=True,exist_ok=True)
    before,after,final,motion=[read(n) for n in ('before','after','finalSaturn','motion')]
    assert all(x['completed'] and not x['errors'] for x in (before,after,final,motion))
    frames=[dict(x,stage='after') for x in after['frames'] if x['body']!=7]
    frames += [dict(x,stage='finalSaturn') for x in final['frames']]
    assert len(frames)==16 and len(motion['frames'])==128
    for x in frames:
        assert len(x['rings'])==4 and x['cloud_rt']==0 and x['ap']==0
        b=x['body'];expected=[69911,58232,25362,24622][b-6]*100000
        assert all(abs(s-expected)<.01 for s in x['rings'][b-6]['scale'])
        assert all(r['material'] and r['visible'] for r in x['rings'])
        target=x['name']+'.png'
        shutil.copy2(image(x['stage'],x['name']),IMAGES/target)
        x['archived_image']=target
    for x in before['frames']:
        shutil.copy2(image('before',x['name']),IMAGES/(x['name']+'-before.png'))
    metrics=[]
    for b,key in ((6,'Jupiter'),(7,'Saturn'),(8,'Uranus'),(9,'Neptune')):
        rows=[x for x in motion['frames'] if x['body']==b]
        assert len(rows)==32
        still=[x for x in rows if x['phase']!='move']
        assert len(still)==16 and all(x['pos']==still[0]['pos'] and x['rot']==still[0]['rot'] for x in still)
        arrays=[np.asarray(Image.open(image('motion',x['name'])).convert('RGB'),dtype=np.float32) for x in still]
        stack=np.stack(arrays)
        # Exclude HUD; these metrics include the planetary disc and background,
        # and are not a motion error measurement or a ring-only photometric test.
        mask=np.zeros(stack.shape[1:3],dtype=bool);mask[180:730,50:1320]=True
        fluctuation=(stack.max(axis=0)-stack.min(axis=0)).mean(axis=2)[mask]
        metrics.append(dict(body=key,static_return_frames=len(still),move_frames=16,
            mean_peak_to_peak_rgb=float(fluctuation.mean()),p99_peak_to_peak_rgb=float(np.percentile(fluctuation,99)),
            fraction_peak_to_peak_above_20=float((fluctuation>20).mean()),
            limitation='只统计同机位静止和返回，包含天体/背景；不把移动视差视为闪烁误差。'))
        for index in (0,16,31):
            r=rows[index];shutil.copy2(image('motion',r['name']),IMAGES/(r['name']+'.png'))
    report=dict(completed=True,final_view_count=16,before_count=4,motion_count=128,
                all_active_ring_scales_correct=True,cloud_direct_path_preserved=True,
                opaque_air_perspective_fix_preserved=True,frames=frames,motion_metrics=metrics)
    (PROOF/'Results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    for name in ('before','after','finalSaturn','motion','Material','ModelValidation'):
        shutil.copy2(SOURCE/(name+'.json'),PROOF/(name+'.json'))
    shutil.copy2(ROOT/'Saved/Logs/PlanetRingsBuild.log',PROOF/'Build.log')
    print(json.dumps(dict(final_views=16,motion_frames=128,metrics=metrics),ensure_ascii=False,indent=2))


if __name__=='__main__':main()
