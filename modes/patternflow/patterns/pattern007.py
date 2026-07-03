# Pattern: Asymmetric Bitwise Glitch Cascade
import math
from .. import core_canvas as pf_canvas

NAME = "Bitwise Cascade"
KNOB_LABELS = ["tear", "speed", "block", "bits"]

_tear = 0.5
_velocity = 2.0
_block_size = 2.5
_bit_thresh = 0.06
_time_acc = 0.0

_DITHER = [0, 12, 3, 15, 8, 4, 11, 7, 2, 14, 1, 13, 10, 6, 9, 5]


def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def setup():
    global _tear, _velocity, _block_size, _bit_thresh, _time_acc
    _tear = 0.5; _velocity = 2.0; _block_size = 2.5; _bit_thresh = 0.06; _time_acc = 0.0


def update(dt: float, inp) -> None:
    global _tear, _velocity, _block_size, _bit_thresh, _time_acc
    if inp.knob_deltas[0]: _tear = _clamp(_tear + inp.knob_deltas[0] * 0.04, 0.0, 1.0)
    if inp.btn_pressed[0]: _tear = 0.5
    if inp.knob_deltas[1]: _velocity = _clamp(_velocity + inp.knob_deltas[1] * 0.1, 0.0, 4.0)
    if inp.btn_pressed[1]: _velocity = 2.0
    if inp.knob_deltas[2]: _block_size = _clamp(_block_size + inp.knob_deltas[2] * 0.1, 0.0, 4.0)
    if inp.btn_pressed[2]: _block_size = 2.5
    if inp.knob_deltas[3]: _bit_thresh = _clamp(_bit_thresh + inp.knob_deltas[3] * 0.01, 0.0, 1.0)
    if inp.btn_pressed[3]: _bit_thresh = 0.06
    _time_acc += dt * _velocity * 3.0


def draw() -> None:
    w, h = pf_canvas.W, pf_canvas.H
    p_size = max(1, math.floor(1.0 + _block_size * 4.0))
    mask_val = math.floor(_bit_thresh * 31)
    for y in range(h):
        fault_line = math.sin(y * 0.08 + _time_acc * 0.4) * math.cos(y * 0.03)
        h_shift = 0
        if fault_line > 0.9 - _tear * 0.7:
            h_shift = math.floor(math.tan(y * 0.05 + _time_acc) * (_tear * 15.0))
        for x in range(w):
            sx = math.floor(((x + h_shift + w) % w) / p_size) * p_size
            sy = math.floor(y / p_size) * p_size
            stream_seed = math.sin(math.floor(sx / 8) * 54.12) * 0.5 + 0.5
            drop = math.floor(sy / 4 - _time_acc * (0.6 + stream_seed * 0.4)) % 16
            rain_mass = 1.0 if drop < 6 else 0.0
            bit_field = 0.5 if ((int(sx / p_size) ^ int(sy / p_size)) & mask_val) == 0 else 0.0
            cx = sx - w * 0.5
            cy = sy - h * 0.5
            total_signal = rain_mass * 0.6 + bit_field + math.sin(math.sqrt(cx * cx + cy * cy) * 0.15 - _time_acc) * 0.25
            thresh = _DITHER[(y % 4) * 4 + (x % 4)] / 16.0
            if total_signal > thresh:
                if rain_mass > 0.0 and drop == 0:
                    r, g, b = 255, 0, 150
                else:
                    r = g = b = 255
            else:
                r = g = b = 0
            pf_canvas.set_pixel(x, y, r, g, b)
    pf_canvas.present()
