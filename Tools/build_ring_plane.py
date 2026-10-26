"""生成独立的单位星环承载平面，后续材质按半径裁圆；无需第三方网格。"""
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / 'SourceAssets/SolarSystem/Rings'


def build(side=10):
    assert side >= 2
    vertices = [(-1 + 2*x/(side-1), -1 + 2*y/(side-1), 0.)
                for y in range(side) for x in range(side)]
    uv = [(x/(side-1), y/(side-1)) for y in range(side) for x in range(side)]
    faces = []
    for y in range(side-1):
        for x in range(side-1):
            a = y*side+x
            faces.extend([(a, a+1, a+side), (a+1, a+side+1, a+side)])
    # Geometric validation: valid indices, consistent +Z winding and full area.
    area = 0.
    for face in faces:
        a, b, c = [vertices[i] for i in face]
        cross = (b[0]-a[0])*(c[1]-a[1]) - (b[1]-a[1])*(c[0]-a[0])
        assert cross > 0
        area += cross/2
    assert math.isclose(area, 4., abs_tol=1e-10)
    assert len(vertices) == side*side and len(faces) == 2*(side-1)**2
    lines = ['# Original unit plane; XY extent [-1,1], normal +Z, UV [0,1].', 'o RingPlane']
    lines += ['v %.12g %.12g %.12g' % p for p in vertices]
    lines += ['vt %.12g %.12g' % p for p in uv]
    lines += ['vn 0 0 1']
    lines += ['f ' + ' '.join('%d/%d/1' % (i+1, i+1) for i in face) for face in faces]
    DEST.mkdir(parents=True, exist_ok=True)
    (DEST / 'SM_RingPlane.obj').write_text('\n'.join(lines)+'\n', encoding='utf-8')
    report = dict(vertices=len(vertices), triangles=len(faces), area=area, uv_range=[0,1],
                  local_extent=[-1,1], winding='+Z', units='单位半径；接入后按外环半径厘米数缩放',
                  runtime_integrated=False, shader_required=True)
    (DEST / 'PlaneValidation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Validated plane: %d vertices, %d triangles' % (len(vertices), len(faces)))


if __name__ == '__main__':
    build()
