# Pattern: Bitwise Interference Shards
import math
from .. import core_canvas as pf_canvas

NAME = "Bitwise Shards"
KNOB_LABELS = ["res", "speed", "shift", "palette"]

_res = 0.5
_speed = 2.0
_bit_mod = 2.0
_palette = 0.3
_time_acc = 0.0


def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def _clip(v: float) -> int:
    return int(_clamp(v, 0.0, 255.0))


def setup():
    global _res, _speed, _bit_mod, _palette, _time_acc
    _res = 0.5; _speed = 2.0; _bit_mod = 2.0; _palette = 0.3; _time_acc = 0.0


def update(dt: float, inp) -> None:
    global _res, _speed, _bit_mod, _palette, _time_acc
    if inp.knob_deltas[0]: _res = _clamp(_res + inp.knob_deltas[0] * 0.04, 0.0, 1.0)
    if inp.btn_pressed[0]: _res = 0.5
    if inp.knob_deltas[1]: _speed = _clamp(_speed + inp.knob_deltas[1] * 0.2, 0.1, 10.0)
    if inp.btn_pressed[1]: _speed = 2.0
    if inp.knob_deltas[2]: _bit_mod = _clamp(_bit_mod + inp.knob_deltas[2] * 0.2, 0.0, 4.9)
    if inp.btn_pressed[2]: _bit_mod = 2.0
    if inp.knob_deltas[3]: _palette = _clamp(_palette + inp.knob_deltas[3] * 0.04, 0.0, 1.0)
    if inp.btn_pressed[3]: _palette = 0.3
    _time_acc += dt * _speed


def draw() -> None:
    block_size = max(1, 4 + math.floor(_res * 16))
    shift_val = math.floor(_bit_mod) + 1
    period = block_size * 2
    for y in range(pf_canvas.H):
        bx = y // block_size
        my = abs((y % period) - block_size)
        for x in range(pf_canvas.W):
            ax = x // block_size
            mx = abs((x % period) - block_size)
            shard_id = (ax ^ bx) << shift_val
            combined = abs(math.sin((mx + my) * 0.3 + shard_id * 0.1 + _time_acc))
            r = g = b = 0
            if combined > 0.6:
                norm = (combined - 0.6) / 0.4
                if _palette < 0.5:
                    r = _clip(130 * norm); g = _clip(255 * (1.0 - norm)); b = 255
                else:
                    r = 255; g = _clip(180 * norm); b = 0
                if combined > 0.93:
                    r = g = b = 255
            elif combined < 0.05:
                r, g, b = 20, 20, 40
            pf_canvas.set_pixel(x, y, r, g, b)
    pf_canvas.present()
