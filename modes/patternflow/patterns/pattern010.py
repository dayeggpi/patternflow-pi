# Pattern: Hyper-Dimensional Folded Cross Matrix
import math
from .. import core_canvas as pf_canvas

NAME = "Folded Matrix"
KNOB_LABELS = ["scale", "speed", "folds", "color"]

_scale = 0.5
_speed = 2.0
_folds = 2.5
_color_mask = 0.3
_time_acc = 0.0


def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def _clip(v: float) -> int:
    return int(_clamp(v, 0.0, 255.0))


def setup():
    global _scale, _speed, _folds, _color_mask, _time_acc
    _scale = 0.5; _speed = 2.0; _folds = 2.5; _color_mask = 0.3; _time_acc = 0.0


def update(dt: float, inp) -> None:
    global _scale, _speed, _folds, _color_mask, _time_acc
    if inp.knob_deltas[0]: _scale = _clamp(_scale + inp.knob_deltas[0] * 0.04, 0.0, 1.0)
    if inp.btn_pressed[0]: _scale = 0.5
    if inp.knob_deltas[1]: _speed = _clamp(_speed + inp.knob_deltas[1] * 0.2, 0.1, 10.0)
    if inp.btn_pressed[1]: _speed = 2.0
    if inp.knob_deltas[2]: _folds = _clamp(_folds + inp.knob_deltas[2] * 0.2, 0.0, 4.9)
    if inp.btn_pressed[2]: _folds = 2.5
    if inp.knob_deltas[3]: _color_mask = _clamp(_color_mask + inp.knob_deltas[3] * 0.04, 0.0, 1.0)
    if inp.btn_pressed[3]: _color_mask = 0.3
    _time_acc += dt * _speed


def draw() -> None:
    f_size = 8 + math.floor(_scale * 24)
    period = f_size * 2
    for y in range(pf_canvas.H):
        fy = abs((y % period) - f_size) * _folds
        for x in range(pf_canvas.W):
            fx = abs((x % period) - f_size) * _folds
            cross_a = math.sin(fx * 0.2 + _time_acc) * math.cos(fy * 0.2 - _time_acc)
            cross_b = math.cos(fx * 0.1 - _time_acc * 1.5) * math.sin(fy * 0.1 + _time_acc)
            combined = abs(cross_a + cross_b)
            r = g = b = 0
            if combined > 0.65:
                edge = (combined - 0.65) / 0.35
                if _color_mask < 0.5:
                    r = _clip(255 * edge); g = 0; b = _clip(120 + 135 * (1.0 - edge))
                else:
                    r = 0; g = _clip(255 * edge); b = _clip(180 * edge)
                if combined > 0.92:
                    r = g = b = 255
            elif combined < 0.08:
                r, g, b = 255, 255, 0
            pf_canvas.set_pixel(x, y, r, g, b)
    pf_canvas.present()
