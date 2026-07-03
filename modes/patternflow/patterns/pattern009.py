# Pattern: Molten Magma Heat Map
import math
from .. import core_canvas as pf_canvas

NAME = "Molten Magma"
KNOB_LABELS = ["visc", "speed", "core", "crust"]

_viscosity = 0.5
_speed = 2.0
_expansion = 2.0
_crust = 0.4
_time_acc = 0.0


def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def _clip(v: float) -> int:
    return int(_clamp(v, 0.0, 255.0))


def setup():
    global _viscosity, _speed, _expansion, _crust, _time_acc
    _viscosity = 0.5; _speed = 2.0; _expansion = 2.0; _crust = 0.4; _time_acc = 0.0


def update(dt: float, inp) -> None:
    global _viscosity, _speed, _expansion, _crust, _time_acc
    if inp.knob_deltas[0]: _viscosity = _clamp(_viscosity + inp.knob_deltas[0] * 0.04, 0.0, 1.0)
    if inp.btn_pressed[0]: _viscosity = 0.5
    if inp.knob_deltas[1]: _speed = _clamp(_speed + inp.knob_deltas[1] * 0.2, 0.1, 10.0)
    if inp.btn_pressed[1]: _speed = 2.0
    if inp.knob_deltas[2]: _expansion = _clamp(_expansion + inp.knob_deltas[2] * 0.2, 0.0, 4.9)
    if inp.btn_pressed[2]: _expansion = 2.0
    if inp.knob_deltas[3]: _crust = _clamp(_crust + inp.knob_deltas[3] * 0.04, 0.0, 1.0)
    if inp.btn_pressed[3]: _crust = 0.4
    _time_acc += dt * _speed


def draw() -> None:
    w, h = pf_canvas.W, pf_canvas.H
    visc = 0.02 + _viscosity * 0.08
    core_shift = _expansion - 2.5
    cx = w / 2.0
    cy = h / 2.0
    for y in range(h):
        for x in range(w):
            n1 = math.sin(x * visc + _time_acc) * math.cos(y * visc - _time_acc)
            n2 = math.sin((x - cx) * 0.05 - _time_acc * 0.4) * math.sin((y - cy) * 0.05 + _time_acc * 0.6)
            n3 = math.cos(math.sqrt((x - cx) * (x - cx) + (y - cy) * (y - cy)) * 0.1 - _time_acc * 1.5)
            heat_sum = (n1 + n2 * 0.7 + n3 * 0.5) / 2.2 + core_shift * 0.3
            temp = _clamp((heat_sum + 1.0) * 0.5, 0.0, 1.0)
            if temp > 0.85:
                r, g, b = 255, 255, 230
            elif temp > 0.65:
                r, g, b = 255, _clip(180 + (temp - 0.65) * 375), 20
            elif temp > 0.4:
                r, g, b = 220, _clip((temp - 0.4) * 700), 5
            elif temp > 0.18:
                r, g, b = _clip(40 + (temp - 0.18) * 800), 0, 0
            else:
                r, g, b = 10, 5, 15
            if _crust > 0.05:
                crack_pattern = math.sin(x * 1.5) * math.cos(y * 1.5)
                if crack_pattern > 1.0 - _crust and temp < 0.6:
                    r = int(r * 0.15); g = 0; b = int(b * 0.1)
            pf_canvas.set_pixel(x, y, r, g, b)
    pf_canvas.present()
