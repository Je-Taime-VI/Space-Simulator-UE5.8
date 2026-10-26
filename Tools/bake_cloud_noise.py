"""离线生成可重复的64³云侵蚀密度，供体积纹理使用；不含观测气象数据。"""
from pathlib import Path
import numpy as np
from PIL import Image

SIZE = 64
ROOT = Path(__file__).resolve().parents[1]


def noise(points, period):
    cell = np.floor(points).astype(np.int64)
    f = points - cell
    f = f * f * (3 - 2 * f)
    result = np.zeros(points.shape[:-1])
    for x in (0, 1):
        for y in (0, 1):
            for z in (0, 1):
                c = (cell + (x, y, z)) % period
                h = (c[..., 0] * 73856093 ^ c[..., 1] * 19349663 ^ c[..., 2] * 83492791).astype(np.uint32)
                h = (h ^ (h >> 13)) * np.uint32(1274126177)
                value = (h & 65535) / 65535.
                weight = (f[..., 0] if x else 1-f[..., 0]) * (f[..., 1] if y else 1-f[..., 1]) * (f[..., 2] if z else 1-f[..., 2])
                result += value * weight
    return result


def bake():
    z, y, x = np.mgrid[:SIZE, :SIZE, :SIZE]
    points = np.stack((x, y, z), axis=-1) + .5
    # Integer periods guarantee continuity across all three volume boundaries.
    field = .7 * noise(points * (14 / SIZE), 14) + .3 * noise(points * (39 / SIZE) + 17, 39)
    data = np.rint(np.clip(field, 0, 1) * 255).astype(np.uint8)
    atlas = np.empty((SIZE * 8, SIZE * 8), dtype=np.uint8)
    for layer in range(SIZE):
        row, col = divmod(layer, 8)
        atlas[row*SIZE:(row+1)*SIZE, col*SIZE:(col+1)*SIZE] = data[layer]
    target = ROOT / 'SourceAssets/SolarSystem/T_CloudDetailAtlas.png'
    Image.fromarray(atlas).save(target)
    print(target, '64x64x64, linear G8; atlas 512x512')


if __name__ == '__main__':
    bake()
