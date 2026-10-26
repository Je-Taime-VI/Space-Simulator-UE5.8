"""只读大气边界截图；统计相差400米的同方向画面差异，不替代画面检查。"""
import json
from pathlib import Path
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'Saved/Diagnostics/AtmosphereBoundary_20261017'


def analyze(stage):
    capture = json.loads((OUT / (stage + '.json')).read_text(encoding='utf-8'))
    assert capture['completed'] and not capture['errors']
    images, metadata, results = {}, {}, {}
    for row in capture['frames']:
        matches = list((OUT / stage).glob(row['name'] + '*.png'))
        assert len(matches) == 1, matches
        with Image.open(matches[0]) as im:
            assert im.size == (1376, 808), im.size
            pixels = np.asarray(im.convert('RGB'), dtype=np.float32)
        assert pixels[20:145, 20:300].mean() > 10, 'Missing game HUD: ' + str(matches[0])
        assert row['cloud_rt'] == 0
        if row['body'] in (2, 3, 5):
            assert row['diagnostics']['terrain_blend'] >= .999, row['name']
        images[row['name']] = pixels[300:650, 100:1250]
        metadata[row['name']] = row
    for name, above in images.items():
        if not name.endswith('-above'):
            continue
        below_name = name[:-6] + '-below'
        assert np.max(np.abs(np.array(metadata[name]['rot']) - metadata[below_name]['rot'])) < .0001
        d = np.abs(above - images[below_name])
        results[name[:-6]] = dict(mean_absolute_rgb_difference=float(d.mean()),
                                 p95_rgb_difference=float(np.percentile(d, 95)))
    report = dict(stage=stage, frames=len(images), roi_xyxy=[100, 300, 1250, 650],
                  intensity_scale=255, results=results,
                  scope='高度相差400米，包含视差、云采样和几何细节变化，不能把差异直接称为误差率。')
    (OUT / (stage + '-metrics.json')).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    import sys
    analyze(sys.argv[1] if len(sys.argv) > 1 else 'comparison-final')
