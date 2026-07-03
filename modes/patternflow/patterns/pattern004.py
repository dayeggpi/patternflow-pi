# Pattern: Shifted Checker Blocks
import math
from .. import core_color  as pf_color
from .. import core_canvas as pf_canvas

NAME = "Shifted Checker"
KNOB_LABELS = ["hue", "speed", "shift", "size"]

_hue = 0.56
_speed = 0.42
_mode = 0.35
_freq = 0.45
_time_acc = 0.0


def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def _mix(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def setup():
    global _hue, _speed, _mode, _freq, _time_acc
    _hue = 0.56; _speed = 0.42; _mode = 0.35; _freq = 0.45; _time_acc = 0.0


def update(dt: float, inp) -> None:
    global _hue, _speed, _mode, _freq, _time_acc
    if inp.knob_deltas[0]: _hue = (_hue + inp.knob_deltas[0] * 0.012) % 1.0
    if inp.btn_pressed[0]: _hue = 0.56
    if inp.knob_deltas[1]: _speed = _clamp(_speed + inp.knob_deltas[1] * 0.018, 0.0, 1.0)
    if inp.btn_pressed[1]: _speed = 0.42
    if inp.knob_deltas[2]: _mode = _clamp(_mode + inp.knob_deltas[2] * 0.018, 0.0, 1.0)
    if inp.btn_pressed[2]: _mode = 0.35
    if inp.knob_deltas[3]: _freq = _clamp(_freq + inp.knob_deltas[3] * 0.018, 0.0, 1.0)
    if inp.btn_pressed[3]: _freq = 0.45
    _time_acc += dt * (0.18 + _speed * 1.85)


def draw() -> None:
    cell_size = max(1, int(_mix(16.0, 4.0, _freq)))
    inv_cell = 1.0 / cell_size
    c1 = pf_color.hsv_to_rgb(_hue, 0.9, 1.0)
    shift_intensity = _mix(0.0, 3.0, _mode)
    for y in range(pf_canvas.H):
        gy = math.floor(y * inv_cell)
        shift_x = math.floor(math.sin(gy * 0.5 + _time_acc * 2.0) * cell_size * shift_intensity)
        ny = (y - gy * cell_size) * inv_cell - 0.5
        abs_ny = abs(ny)
        for x in range(pf_canvas.W):
            eff_x = x + shift_x
            gx = math.floor(eff_x * inv_cell)
            nx = (eff_x - gx * cell_size) * inv_cell - 0.5
            abs_nx = abs(nx)
            r = g = b = 0
            if (gx + gy) % 2 == 0:
                if abs_nx < 0.3 and abs_ny < 0.3:
                    r, g, b = c1
            elif abs_nx > 0.4 or abs_ny > 0.4:
                r = g = b = 255
            pf_canvas.set_pixel(x, y, r, g, b)
    pf_canvas.present()
