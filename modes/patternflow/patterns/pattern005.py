# Pattern: Grid Interference
import math
from .. import core_color  as pf_color
from .. import core_canvas as pf_canvas

NAME = "Grid Interference"
KNOB_LABELS = ["hue", "speed", "freq", "chaos"]

_hue_base = 0.6
_speed = 1.0
_freq = 0.1
_chaos = 1.0
_time_acc = 0.0


def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def setup():
    global _hue_base, _speed, _freq, _chaos, _time_acc
    _hue_base = 0.6; _speed = 1.0; _freq = 0.1; _chaos = 1.0; _time_acc = 0.0


def update(dt: float, inp) -> None:
    global _hue_base, _speed, _freq, _chaos, _time_acc
    if inp.knob_deltas[0]: _hue_base = (_hue_base + inp.knob_deltas[0] * 0.05) % 1.0
    if inp.btn_pressed[0]: _hue_base = 0.6
    if inp.knob_deltas[1]: _speed = max(0.0, _speed + inp.knob_deltas[1] * 0.1)
    if inp.btn_pressed[1]: _speed = 1.0
    if inp.knob_deltas[2]: _freq = _clamp(_freq + inp.knob_deltas[2] * 0.005, 0.05, 0.2)
    if inp.btn_pressed[2]: _freq = 0.1
    if inp.knob_deltas[3]: _chaos = _clamp(_chaos + inp.knob_deltas[3] * 0.1, 0.0, 3.0)
    if inp.btn_pressed[3]: _chaos = 1.0
    _time_acc += dt * _speed


def draw() -> None:
    for y in range(pf_canvas.H):
        for x in range(pf_canvas.W):
            v1 = math.sin(x * _freq + _time_acc)
            v2 = math.sin(y * _freq * 1.3 - _time_acc * 1.1)
            v3 = math.sin((x + y) * _freq * 0.7 + _time_acc * 0.8)
            v4 = math.sin((x - y) * _freq * 1.2 - _time_acc * 0.9)
            field = abs(v1 + v2 + v3 + v4) * (0.4 + _chaos * 0.1)
            val = _clamp(1.2 - field, 0.0, 1.0) ** 3.0
            hue = (_hue_base + (x + y) * 0.003 + field * 0.4) % 1.0
            r, g, b = pf_color.hsv_to_rgb(hue, 0.9, val * 0.9 + 0.1)
            pf_canvas.set_pixel(x, y, r, g, b)
    pf_canvas.present()
