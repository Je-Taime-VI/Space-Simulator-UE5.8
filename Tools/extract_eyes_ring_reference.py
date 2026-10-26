"""从已下载的NASA Eyes脚本文本提取星环配置事实；不执行网页代码。"""
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'Saved/Reference/NasaEyes_20261017/app.js'
DEST = ROOT / 'SourceAssets/SolarSystem/Rings'


def extract(source=SOURCE):
    data = source.read_bytes()
    text = data.decode('utf-8')
    component = text.split('class RingsComponent ', 1)[1].split('class ', 1)[0]
    required = ['transparent:!0', 'depthWrite:!1', 'NormalBlending', 'DoubleSide',
                'spheroidShadow', 'topTexture', 'bottomTexture']
    assert all(x in component for x in required), 'Reference implementation changed'
    result = {}
    for body, next_body in [('jupiter', 'saturn'), ('saturn', 'uranus'),
                            ('uranus', 'neptune'), ('neptune', None)]:
        marker = body + ':{groups:["planets"'
        block = text.split(marker, 1)[1]
        block = block.split(next_body + ':{groups:["planets"', 1)[0] if next_body else block.split('const r={hintIndex:', 1)[0]
        row = {'ring_component_configured': 'addComponent(s.RingsComponent)' in block}
        if row['ring_component_configured']:
            for prop in ('InnerRadius', 'OuterRadius'):
                value = re.search(r'set' + prop + r'\(([\d.eE+-]+)\)', block)
                assert value, (body, prop)
                row['inner_radius_km' if prop == 'InnerRadius' else 'outer_radius_km'] = float(value[1])
            for prop in ('Top', 'Bottom'):
                value = re.search(r'set' + prop + r'TextureUrl\("([^\"]+)"\)', block)
                assert value, (body, prop)
                row[prop.lower() + '_texture_reference'] = value[1].replace('$STATIC_ASSETS_URL', 'https://eyes.nasa.gov/assets/static')
            assert 0 < row['inner_radius_km'] < row['outer_radius_km']
        result[body] = row
    return {'checked_date': '2026-10-17', 'source_url': 'https://eyes.nasa.gov/apps/solar-system/app.js',
            'source_sha256': hashlib.sha256(data).hexdigest(), 'bodies': result,
            'interpretation': '网页实现参数，不等同于完整科学环目录；仅木星当前配置未发现该组件，不推断木星没有环。',
            'reuse': '只保存参数事实与纹理来源引用；未复制网页程序或纹理到运行资产。'}


if __name__ == '__main__':
    result = extract()
    DEST.mkdir(parents=True, exist_ok=True)
    (DEST / 'EyesReference.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print('Extracted:', ', '.join(result['bodies']))
