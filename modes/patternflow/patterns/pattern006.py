# Pattern: Sheared Noise Bands
import math
from .. import core_color  as pf_color
from .. import core_canvas as pf_canvas

NAME = "Sheared Bands"
KNOB_LABELS = ["split", "speed", "shear", "bands"]

_split = 0.5
_speed = 1.0
_shear = 20.0
_bands = 0.1
_time_acc = 0.0


def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def _hash21(x: float, y: float) -> float:
    n = math.sin(x * 12.9898 + y * 78.233) * 43758.5453
    return n - math.floor(n)


def _noise2d(x: float, y: float) -> float:
    ix = math.floor(x); iy = math.floor(y)
    fx = x - ix; fy = y - iy
    ux = fx * fx * (3.0 - 2.0 * fx)
    uy = fy * fy * (3.0 - 2.0 * fy)
    a = _hash21(ix, iy); b = _hash21(ix + 1, iy)
    c = _hash21(ix, iy + 1); d = _hash21(ix + 1, iy + 1)
    return (a * (1.0 - ux) + b * ux) * (1.0 - uy) + (c * (1.0 - ux) + d * ux) * uy


def setup():
    global _split, _speed, _shear, _bands, _time_acc
    _split = 0.5; _speed = 1.0; _shear = 20.0; _bands = 0.1; _time_acc = 0.0


def update(dt: float, inp) -> None:
    global _split, _speed, _shear, _bands, _time_acc
    if inp.knob_deltas[0]: _split = (_split + inp.knob_deltas[0] * 0.03) % 1.0
    if inp.btn_pressed[0]: _split = 0.5
    if inp.knob_deltas[1]: _speed = _clamp(_speed + inp.knob_deltas[1] * 0.1, 0.0, 2.0)
    if inp.btn_pressed[1]: _speed = 1.0
    if inp.knob_deltas[2]: _shear = _clamp(_shear + inp.knob_deltas[2] * 2.0, 0.0, 40.0)
    if inp.btn_pressed[2]: _shear = 20.0
    if inp.knob_deltas[3]: _bands = _clamp(_bands + inp.knob_deltas[3] * 0.01, 0.02, 0.22)
    if inp.btn_pressed[3]: _bands = 0.1
    _time_acc += dt * _speed


def draw() -> None:
    for y in range(pf_canvas.H):
        band_id = math.floor(y * _bands)
        band_fract = y * _bands - band_id
        direction = 1 if band_id % 2 == 0 else -1
        band_speed = direction * (1.0 + _noise2d(band_id, 0) * 2.0) * _time_acc
        offset = _noise2d(band_id * 5.1, _time_acc * 0.2) * _shear
        edge_darken = math.sin(band_fract * math.pi)
        for x in range(pf_canvas.W):
            sheared_x = x + offset + band_speed
            n = _noise2d(sheared_x * 0.05, y * 0.05)
            local_hue = n * 0.2 if band_id % 2 == 0 else _split + n * 0.2
            val = max(0.0, n * 1.5 * edge_darken)
            r, g, b = pf_color.hsv_to_rgb(local_hue, 0.8, min(1.0, val))
            pf_canvas.set_pixel(x, y, r, g, b)
    pf_canvas.present()
