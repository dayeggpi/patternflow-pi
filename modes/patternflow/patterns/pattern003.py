# Pattern: Sliding Segmented Rows
import math
from .. import core_color  as pf_color
from .. import core_canvas as pf_canvas

NAME = "Sliding Segments"
KNOB_LABELS = ["hue", "speed", "rows", "width"]

_hue_base = 0.2
_speed = 1.0
_row_height = 8.0
_seg_width = 16.0
_time_acc = 0.0


def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def setup():
    global _hue_base, _speed, _row_height, _seg_width, _time_acc
    _hue_base = 0.2; _speed = 1.0; _row_height = 8.0; _seg_width = 16.0; _time_acc = 0.0


def update(dt: float, inp) -> None:
    global _hue_base, _speed, _row_height, _seg_width, _time_acc
    if inp.knob_deltas[0]: _hue_base = (_hue_base + inp.knob_deltas[0] * 0.05) % 1.0
    if inp.btn_pressed[0]: _hue_base = 0.2
    if inp.knob_deltas[1]: _speed = max(0.0, _speed + inp.knob_deltas[1] * 0.05)
    if inp.btn_pressed[1]: _speed = 1.0
    if inp.knob_deltas[2]: _row_height = _clamp(_row_height + inp.knob_deltas[2] * 0.5, 4.0, 16.0)
    if inp.btn_pressed[2]: _row_height = 8.0
    if inp.knob_deltas[3]: _seg_width = _clamp(_seg_width + inp.knob_deltas[3] * 1.0, 8.0, 48.0)
    if inp.btn_pressed[3]: _seg_width = 16.0
    _time_acc += dt * _speed


def draw() -> None:
    rh = max(1, int(_row_height))
    sw = max(1, int(_seg_width))
    half_rh = rh >> 1
    half_sw = sw >> 1
    for y in range(pf_canvas.H):
        row_idx = y // rh
        ly = y % rh
        speed_mult = (1 if row_idx % 2 == 0 else -1) * ((row_idx % 3) * 0.5 + 0.5)
        row_offset = _time_acc * 20.0 * speed_mult
        for x in range(pf_canvas.W):
            adj_x = x + row_offset
            seg_idx = math.floor(adj_x / sw)
            lx = math.floor(adj_x % sw)
            val = abs(math.sin(row_idx * 12.9898 + seg_idx * 78.233)) * 10000.0
            val -= math.floor(val)
            draw_px = False
            h_offset = 0.0
            cx = lx - half_sw
            cy = ly - half_rh
            if val < 0.2:
                if half_rh - 2 < ly < half_rh + 2 and lx < sw * 0.8:
                    draw_px = True
            elif val < 0.4:
                if (lx + ly) % 6 < 3:
                    draw_px = True; h_offset = 0.2
            elif val < 0.6:
                pass
            elif val < 0.8:
                if lx % 4 == 0 and ly % 4 == 0:
                    draw_px = True; h_offset = 0.6
            else:
                wave_y = half_rh + math.sin(lx * 0.5) * (half_rh - 1)
                if abs(ly - wave_y) < 1.5:
                    draw_px = True; h_offset = 0.8
            if lx == 0:
                draw_px = True; h_offset = 0.5
            if draw_px:
                r, g, b = pf_color.hsv_to_rgb((_hue_base + h_offset) % 1.0, 0.9, 1.0)
            else:
                r = g = b = 0
            pf_canvas.set_pixel(x, y, r, g, b)
    pf_canvas.present()
