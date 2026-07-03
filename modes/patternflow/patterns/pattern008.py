# Pattern: Mechanical Grid Blocks
import math
from .. import core_canvas as pf_canvas

NAME = "Mechanical Grid"
KNOB_LABELS = ["size", "speed", "sparse", "chaos"]

_block_size = 8
_speed = 2.5
_sparsity = 2.0 / 4.9
_chaos = 0.75
_time = 0.0


def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def _clip_color(v: float) -> int:
    return int(_clamp(v, 0.0, 255.0))


def setup():
    global _block_size, _speed, _sparsity, _chaos, _time
    _block_size = 8; _speed = 2.5; _sparsity = 2.0 / 4.9; _chaos = 0.75; _time = 0.0


def update(dt: float, inp) -> None:
    global _block_size, _speed, _sparsity, _chaos, _time
    if inp.knob_deltas[0]: _block_size = int(_clamp(_block_size + inp.knob_deltas[0], 4, 16))
    if inp.btn_pressed[0]: _block_size = 8
    if inp.knob_deltas[1]: _speed = _clamp(_speed + inp.knob_deltas[1] * 0.2, 0.1, 10.0)
    if inp.btn_pressed[1]: _speed = 2.5
    if inp.knob_deltas[2]: _sparsity = _clamp(_sparsity + inp.knob_deltas[2] * 0.03, 0.0, 1.0)
    if inp.btn_pressed[2]: _sparsity = 2.0 / 4.9
    if inp.knob_deltas[3]: _chaos = _clamp(_chaos + inp.knob_deltas[3] * 0.06, 0.0, 1.5)
    if inp.btn_pressed[3]: _chaos = 0.75
    _time += dt * _speed


def draw() -> None:
    bs = max(1, _block_size)
    for y in range(pf_canvas.H):
        block_y = y // bs
        inner_y = (y % bs) / bs - 0.5
        for x in range(pf_canvas.W):
            block_x = x // bs
            inner_x = (x % bs) / bs - 0.5
            cell_energy = math.sin(block_x * 0.35 + block_y * 0.25 + _time) * 0.5 + 0.5
            if _chaos > 0.05:
                structural_noise = math.sin(block_x * 3.1 - block_y * 2.3 - _time * 2.0)
                cell_energy = _clamp(cell_energy + structural_noise * _chaos * 0.3, 0.0, 1.0)
            r = g = b = 0
            if cell_energy > _sparsity:
                radius_sq = inner_x * inner_x + inner_y * inner_y
                max_radius = cell_energy * 0.45
                if max_radius > 0 and radius_sq < max_radius:
                    edge_profile = 1.0 - radius_sq / max_radius
                    if (block_x + block_y) % 2 == 0:
                        r = 255; g = _clip_color(80 + cell_energy * 175); b = _clip_color(edge_profile * 100)
                    else:
                        r = _clip_color(edge_profile * 50); g = 230; b = _clip_color(150 + cell_energy * 105)
                    if edge_profile > 0.85:
                        r = g = b = 255
            pf_canvas.set_pixel(x, y, r, g, b)
    pf_canvas.present()
