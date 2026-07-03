# Pattern: Solar Flare Storm
import math
from .. import core_canvas as pf_canvas

NAME = "Solar Flare"
KNOB_LABELS = ["chaos", "speed", "life", "temp"]

_chaos = 0.3
_speed = 2.0
_lifetime = 3.0
_temp = 0.15
_time_acc = 0.0


def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def _clip(v: float) -> int:
    return int(_clamp(v, 0.0, 255.0))


def setup():
    global _chaos, _speed, _lifetime, _temp, _time_acc
    _chaos = 0.3; _speed = 2.0; _lifetime = 3.0; _temp = 0.15; _time_acc = 0.0


def update(dt: float, inp) -> None:
    global _chaos, _speed, _lifetime, _temp, _time_acc
    if inp.knob_deltas[0]: _chaos = _clamp(_chaos + inp.knob_deltas[0] * 0.04, 0.0, 1.0)
    if inp.btn_pressed[0]: _chaos = 0.3
    if inp.knob_deltas[1]: _speed = _clamp(_speed + inp.knob_deltas[1] * 0.2, 0.1, 10.0)
    if inp.btn_pressed[1]: _speed = 2.0
    if inp.knob_deltas[2]: _lifetime = _clamp(_lifetime + inp.knob_deltas[2] * 0.2, 0.0, 4.9)
    if inp.btn_pressed[2]: _lifetime = 3.0
    if inp.knob_deltas[3]: _temp = _clamp(_temp + inp.knob_deltas[3] * 0.04, 0.0, 1.0)
    if inp.btn_pressed[3]: _temp = 0.15
    _time_acc += dt * _speed


def draw() -> None:
    w, h = pf_canvas.W, pf_canvas.H
    for y in range(h):
        for x in range(w):
            pf_canvas.set_pixel(x, y, 0, 0, 0)

    num_flares = math.floor(8 + _chaos * 20)
    decay_rate = 0.1 + (4.9 - _lifetime) * 0.3
    center_x = w / 2.0
    center_y = h / 2.0

    for i in range(num_flares):
        seed = i * 133.7
        tail_steps = 10
        for step in range(tail_steps):
            hist_t = _time_acc - step * decay_rate
            hist_base_rad = 15 + math.sin(hist_t * 0.2 + seed) * 10
            hist_angle = hist_t * (0.5 + math.sin(seed) * 0.3) + seed
            hist_noise_x = math.sin(hist_t * 1.5 + seed * 2) * _chaos * 15
            hist_noise_y = math.cos(hist_t * 1.3 + seed * 2) * _chaos * 15
            px = math.floor(center_x + math.cos(hist_angle) * hist_base_rad + hist_noise_x)
            py = math.floor(center_y + math.sin(hist_angle) * hist_base_rad + hist_noise_y)
            if not (0 <= px < w and 0 <= py < h):
                continue
            life = 1.0 - step / tail_steps
            if life > 0.8:
                r, g, b = 255, 255, 200
            elif life > 0.4:
                r = 255
                g = _clip(_temp * 255 + life * (1.0 - _temp) * 200)
                b = _clip(_temp * 100)
            else:
                r = _clip(life * 255)
                g = _clip(life * _temp * 150)
                b = 0
            pf_canvas.set_pixel(px, py, r, g, b)
            if step == 0:
                glow = (_clip(r / 2), _clip(g / 2), _clip(b / 2))
                if px + 1 < w: pf_canvas.set_pixel(px + 1, py, *glow)
                if px - 1 >= 0: pf_canvas.set_pixel(px - 1, py, *glow)
                if py + 1 < h: pf_canvas.set_pixel(px, py + 1, *glow)
                if py - 1 >= 0: pf_canvas.set_pixel(px, py - 1, *glow)
    pf_canvas.present()
