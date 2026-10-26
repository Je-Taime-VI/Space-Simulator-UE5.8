"""量化冻结时间与机位的连续帧亮度范围；只读截图，不改写图像。"""
import json
from pathlib import Path
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'Saved/Diagnostics/CloudDepth_20261017'


def analyze(stage):
    folder = OUT / stage
    result = {}
    # Fixed 1376x808 viewport: the disc lies inside this rectangle, excluding HUD.
    for rt in (1, 0):
        files = sorted(folder.glob('rt%d-still-*.png' % rt)) + sorted(folder.glob('rt%d-returned-*.png' % rt))
        if not files:
            continue
        sums = squares = low = high = None
        rows = []
        for file in files:
            with Image.open(file) as image:
                assert image.size == (1376, 808), image.size
                pixels = np.asarray(image.convert('RGB'), dtype=np.float32)
                # Shot is a shared screenshot request; reject an editor preview
                # captured during PIE startup instead of silently mixing views.
                assert pixels[20:145,20:300].mean() > 10, 'PIE HUD missing: '+str(file)
                data = pixels[170:725, 390:985].mean(2)
            if sums is None:
                sums, squares, low, high = data.copy(), data*data, data.copy(), data.copy()
            else:
                sums += data
                squares += data*data
                low = np.minimum(low, data)
                high = np.maximum(high, data)
            rows.append(dict(file=file.name, mean=float(data.mean()), lower_left=float(data[260:440, 20:200].mean())))
        n = len(files)
        variance = np.maximum(0, squares/n - (sums/n)**2)
        span = high-low
        result['rt%d' % rt] = dict(frames=n, mean_temporal_std=float(np.sqrt(variance).mean()),
                                 p99_peak_to_peak=float(np.percentile(span, 99)),
                                 fraction_peak_to_peak_gt20=float((span>20).mean()),
                                 brightest=max(rows,key=lambda x:x['lower_left']),
                                 darkest=min(rows,key=lambda x:x['lower_left']))
    report = dict(stage=stage, roi_xyxy=[390,170,985,725], intensity_scale=255,
                  interpretation='固定位置亮度波动；不等同于所有相机运动或云地遮挡的验收。', results=result)
    (OUT/(stage+'-metrics.json')).write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2))


if __name__ == '__main__':
    import sys
    analyze(sys.argv[1] if len(sys.argv)>1 else 'comparison')
