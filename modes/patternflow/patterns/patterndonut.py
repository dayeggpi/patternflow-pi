# Pattern: Donut 3D
import math
from .. import core_color  as pf_color
from .. import core_canvas as pf_canvas

NAME = "Donut 3D"
KNOB_LABELS = ["ROTATE", "SPEED", "BODY SIZE", "COLOR / PALETTE"]
EXTRA_BUTTON_LABELS = ["Animation mode", "Color mode"]

KNOB2_MIN_VALUE = 0.1
KNOB2_MAX_VALUE = 10.0
KNOB3_MAX_VALUE = 4.9
MIN_SPEED = 1.0
MAX_SPEED = 5.0
MAX_STEPS = 34
MAX_DISTANCE = 7.0
HIT_DISTANCE = 0.018
MAJOR_RADIUS = 1.1
DARK_SIDE_BRIGHTNESS = 0.80
NORMAL_EPSILON = 0.035
MORPH_TRANSITION_SECONDS = 4.0
SHAPE_TORUS = 0
SHAPE_DIAMOND = 1
INV_SQRT_2 = 0.70710678
EXPLOSION_STAGE1_SECONDS = 0.55
EXPLOSION_STAGE1_SIZE = 1.0
EXPLOSION_STAGE1_RING_WIDTH = 0.20
EXPLOSION_STAGE2_SECONDS = 3.0
EXPLOSION_STAGE2_PARTICLES = 50
EXPLOSION_STAGE2_SPEED = 5.0
EXPLOSION_STAGE2_FRAGMENT_SIZE = 3
TORUS_COLOR_MODE_COUNT = 3
TORUS_BAND_WIDTH = 0.04
TORUS_BAND_ROTATION_SPEED = 0.7
TORUS_BAND_AMBIENT = 0.7
TORUS_BAND_DIFFUSE = 1.0
TORUS_BAND_RIM = 0.8

PALETTE_SIZE = 16
PALETTES = [
    [
        255, 0, 0, 213, 42, 0, 171, 85, 0, 171, 127, 0,
        171, 171, 0, 86, 213, 0, 0, 255, 0, 0, 213, 42,
        0, 171, 85, 0, 86, 170, 0, 0, 255, 42, 0, 213,
        85, 0, 171, 127, 0, 129, 171, 0, 85, 213, 0, 43,
    ],
    [
        85, 0, 171, 132, 0, 124, 181, 0, 75, 229, 0, 27,
        232, 23, 0, 184, 71, 0, 171, 119, 0, 171, 171, 0,
        171, 85, 0, 221, 34, 0, 242, 0, 14, 194, 0, 62,
        143, 0, 113, 95, 0, 161, 47, 0, 208, 0, 7, 249,
    ],
    [
        230, 255, 170, 135, 220, 90, 75, 180, 65, 35, 135, 48,
        12, 95, 36, 0, 120, 28, 20, 155, 45, 50, 190, 65,
        100, 225, 90, 43, 223, 43, 10, 229, 10, 0, 230, 0,
        20, 155, 45, 50, 190, 65, 100, 225, 90, 170, 255, 130,
    ],
    [
        255, 0, 0, 255, 36, 0, 255, 73, 0, 255, 109, 0,
        255, 146, 0, 255, 182, 0, 255, 219, 0, 255, 255, 0,
        255, 255, 34, 255, 255, 68, 255, 255, 102, 255, 255, 122,
        255, 255, 143, 255, 255, 163, 255, 255, 184, 255, 255, 204,
    ],
    [
        0, 92, 210, 24, 115, 215, 49, 139, 220, 73, 162, 225,
        97, 185, 230, 121, 208, 235, 146, 232, 240, 170, 255, 245,
        149, 235, 241, 128, 214, 236, 106, 194, 232, 85, 174, 228,
        64, 153, 223, 43, 133, 219, 21, 112, 214, 0, 92, 210,
    ],
]
PALETTE_BRIGHTNESS = [1.0, 1.0, 1.0, 1.0, 1.0]
PALETTE_COUNT = len(PALETTES)

_time_acc = 0.0
_band_time = 0.0
_morph_time = 0.0
_morph_mix = 0.0
_explosion_time = 0.0
_tilt_knob = 0.558
_speed_knob = 4.799
_tube_knob = 2.263
_hue_knob = 0.447
_shape_a = SHAPE_TORUS
_shape_b = SHAPE_TORUS
_palette_index = 0
_torus_color_mode = 1
_morphing = False
_explosion_active = False
_particle_angles = []
_particle_speeds = []
_particle_delays = []
_particle_hues = []
_render_scale = 1


def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def _wrap01(v: float) -> float:
    v -= math.floor(v)
    if v < 0.0:
        v += 1.0
    return v


def _map_speed(v: float) -> float:
    n = (_clamp(v, KNOB2_MIN_VALUE, KNOB2_MAX_VALUE) - KNOB2_MIN_VALUE) / (KNOB2_MAX_VALUE - KNOB2_MIN_VALUE)
    return MIN_SPEED + n * (MAX_SPEED - MIN_SPEED)


def _map_tube_radius(v: float) -> float:
    n = _clamp(v / KNOB3_MAX_VALUE, 0.0, 1.0)
    return 0.20 + n * 0.24


def _torus_distance(x: float, y: float, z: float, tube_radius: float) -> float:
    qx = math.sqrt(x * x + y * y) - MAJOR_RADIUS
    return math.sqrt(qx * qx + z * z) - tube_radius


def _build_diamond_cache(tube_radius: float) -> dict:
    size = 0.6 + tube_radius * 0.9
    top_z = size * 0.65
    girdle_z = size * 0.10
    point_z = -size * 1.4
    top_radius = size * 0.6
    girdle_radius = size * 1.05
    crown_slope = (girdle_radius - top_radius) / (top_z - girdle_z)
    pavilion_slope = girdle_radius / (girdle_z - point_z)
    return {
        "size": size,
        "top_z": top_z,
        "crown_slope": crown_slope,
        "pavilion_slope": pavilion_slope,
        "crown_scale": 1.0 / math.sqrt(1.0 + crown_slope * crown_slope),
        "pavilion_scale": 1.0 / math.sqrt(1.0 + pavilion_slope * pavilion_slope),
        "crown_offset": top_radius + crown_slope * top_z,
        "pavilion_offset": pavilion_slope * point_z,
    }


def _diamond_distance(x: float, y: float, z: float, diamond: dict) -> float:
    zz = z + diamond["size"] * 0.20
    d = zz - diamond["top_z"]
    radius = max(max(abs(x), abs(y)), max(abs(x + y), abs(x - y)) * INV_SQRT_2)
    crown = (radius + diamond["crown_slope"] * zz - diamond["crown_offset"]) * diamond["crown_scale"]
    pavilion = (radius - diamond["pavilion_slope"] * zz + diamond["pavilion_offset"]) * diamond["pavilion_scale"]
    return max(d, crown, pavilion)


def _shape_distance(shape: int, x: float, y: float, z: float, tube_radius: float, diamond: dict) -> float:
    if shape == SHAPE_TORUS:
        return _torus_distance(x, y, z, tube_radius)
    return _diamond_distance(x, y, z, diamond)


def _smooth01(v: float) -> float:
    v = _clamp(v, 0.0, 1.0)
    return v * v * (3.0 - 2.0 * v)


def _morph_distance(x: float, y: float, z: float, tube_radius: float, t: float, shape_a: int,
                    shape_b: int, morph_mix: float, diamond: dict) -> float:
    if morph_mix <= 0.0 or shape_a == shape_b:
        return _shape_distance(shape_a, x, y, z, tube_radius, diamond)
    d_a = _shape_distance(shape_a, x, y, z, tube_radius, diamond)
    d_b = _shape_distance(shape_b, x, y, z, tube_radius, diamond)
    swirl = math.sin((x + y + z) * 4.2 + t * 2.0) * 0.035 * morph_mix * (1.0 - morph_mix)
    return d_a + (d_b - d_a) * morph_mix + swirl


def _palette_to_rgb(palette_index: int, position: float, brightness: float) -> tuple[int, int, int]:
    palette = PALETTES[palette_index]
    position = _clamp(position, 0.0, 1.0) * (PALETTE_SIZE - 1)
    color_index = math.floor(position)
    mix = position - color_index
    next_color_index = min(color_index + 1, PALETTE_SIZE - 1)
    offset_a = color_index * 3
    offset_b = next_color_index * 3
    inverse_mix = 1.0 - mix
    level = brightness * PALETTE_BRIGHTNESS[palette_index]
    r = (palette[offset_a] * inverse_mix + palette[offset_b] * mix) * level
    g = (palette[offset_a + 1] * inverse_mix + palette[offset_b + 1] * mix) * level
    b = (palette[offset_a + 2] * inverse_mix + palette[offset_b + 2] * mix) * level
    return int(_clamp(r, 0.0, 255.0)), int(_clamp(g, 0.0, 255.0)), int(_clamp(b, 0.0, 255.0))


def _background_rgb(x: int, y: int, w: int, h: int, t: float) -> tuple[int, int, int]:
    nx = x / max(1.0, w - 1.0)
    ny = y / max(1.0, h - 1.0)
    dx = nx - 0.5
    dy = ny - 0.5
    vignette = 1.0 - math.sqrt(dx * dx + dy * dy) * 1.7
    pulse = math.sin(t * 0.55 + nx * 5.0 - ny * 3.0) * 0.5 + 0.5
    v = math.floor(_clamp(vignette, 0.0, 1.0) * (3.0 + pulse * 5.0))
    return 0, v, min(255, v + 2)


def _set_background(x: int, y: int, w: int, h: int, t: float) -> None:
    pf_canvas.set_pixel(x, y, *_background_rgb(x, y, w, h, t))


def _set_pixel_safe(x: int, y: int, r: int, g: int, b: int) -> None:
    if 0 <= x < pf_canvas.W and 0 <= y < pf_canvas.H:
        pf_canvas.set_pixel(x, y, r, g, b)


def _fill_block(x: int, y: int, scale: int, r: int, g: int, b: int) -> None:
    for yy in range(y, min(y + scale, pf_canvas.H)):
        for xx in range(x, min(x + scale, pf_canvas.W)):
            pf_canvas.set_pixel(xx, yy, r, g, b)


def set_fast_render(enabled: bool) -> None:
    global _render_scale
    _render_scale = 2 if enabled else 1


def _initialize_explosion_particles() -> None:
    global _particle_angles, _particle_speeds, _particle_delays, _particle_hues
    _particle_angles = []
    _particle_speeds = []
    _particle_delays = []
    _particle_hues = []
    seed = 505
    for i in range(EXPLOSION_STAGE2_PARTICLES):
        seed = (seed * 1664525 + 1013904223) & 0xFFFFFFFF
        random_angle = seed / 4294967296.0
        seed = (seed * 1664525 + 1013904223) & 0xFFFFFFFF
        random_speed = seed / 4294967296.0
        seed = (seed * 1664525 + 1013904223) & 0xFFFFFFFF
        random_delay = seed / 4294967296.0
        _particle_angles.append(random_angle * math.pi * 2.0)
        _particle_speeds.append(0.72 + random_speed * 0.56)
        _particle_delays.append(random_delay * 0.18)
        _particle_hues.append((i % 8) * 0.125)


def _draw_explosion_stage1(progress: float) -> None:
    w, h = pf_canvas.W, pf_canvas.H
    cx = (w - 1) * 0.5
    cy = (h - 1) * 0.5
    min_side = min(w, h)
    blast_radius = progress ** 0.65 * min_side * EXPLOSION_STAGE1_SIZE
    ring_width = max(1.0, min_side * EXPLOSION_STAGE1_RING_WIDTH)
    ring_spacing = ring_width * 1.35
    fade = 1.0 - progress
    colors = [(255, 255, 255), (255, 24, 8), (135, 52, 18), (255, 205, 20)]
    for y in range(h):
        dy = y - cy
        for x in range(w):
            dx = x - cx
            distance = math.sqrt(dx * dx + dy * dy)
            best_intensity = 0.0
            best_ring = -1
            for ring_index in range(4):
                radius = blast_radius - ring_index * ring_spacing
                if radius < 0.0:
                    continue
                intensity = _clamp(1.0 - abs(distance - radius) / ring_width, 0.0, 1.0)
                if intensity > best_intensity:
                    best_intensity = intensity
                    best_ring = ring_index
            if best_ring >= 0:
                intensity = best_intensity * (0.65 + fade * 0.35)
                r, g, b = colors[best_ring]
                pf_canvas.set_pixel(x, y, int(r * intensity), int(g * intensity), int(b * intensity))


def _draw_explosion_stage2(progress: float) -> None:
    w, h = pf_canvas.W, pf_canvas.H
    cx = (w - 1) * 0.5
    cy = (h - 1) * 0.5
    travel_distance = max(w, h) * 0.72 * EXPLOSION_STAGE2_SPEED
    for y in range(h):
        for x in range(w):
            _set_background(x, y, w, h, _time_acc)
    for i in range(EXPLOSION_STAGE2_PARTICLES):
        local_progress = _clamp((progress - _particle_delays[i]) / (1.0 - _particle_delays[i]), 0.0, 1.0)
        if local_progress <= 0.0:
            continue
        eased_travel = local_progress * local_progress * (2.0 - local_progress)
        distance = eased_travel * travel_distance * _particle_speeds[i]
        angle = _particle_angles[i]
        direction_x = math.cos(angle)
        direction_y = math.sin(angle)
        px = math.floor(cx + direction_x * distance)
        py = math.floor(cy + direction_y * distance)
        brightness = _clamp(1.0 - local_progress * 0.72, 0.0, 1.0)
        hue = _hue_knob + _particle_hues[i] + local_progress * 0.08
        r, g, b = pf_color.hsv_to_rgb(hue, 0.72, brightness)
        for sy in range(EXPLOSION_STAGE2_FRAGMENT_SIZE):
            for sx in range(EXPLOSION_STAGE2_FRAGMENT_SIZE):
                _set_pixel_safe(px + sx, py + sy, r, g, b)
        tail_x = math.floor(px - direction_x * 3.0)
        tail_y = math.floor(py - direction_y * 3.0)
        _set_pixel_safe(tail_x, tail_y, int(r * 0.45), int(g * 0.45), int(b * 0.45))


def setup():
    global _time_acc, _band_time, _morph_time, _morph_mix, _explosion_time
    global _tilt_knob, _speed_knob, _tube_knob, _hue_knob
    global _shape_a, _shape_b, _palette_index, _torus_color_mode, _morphing, _explosion_active
    _time_acc = 0.0
    _band_time = 0.0
    _morph_time = 0.0
    _morph_mix = 0.0
    _explosion_time = 0.0
    _tilt_knob = 0.558
    _speed_knob = 4.799
    _tube_knob = 2.263
    _hue_knob = 0.447
    _shape_a = SHAPE_TORUS
    _shape_b = SHAPE_TORUS
    _palette_index = 0
    _torus_color_mode = 1
    _morphing = False
    _explosion_active = False
    _initialize_explosion_particles()


def update(dt: float, inp) -> None:
    global _time_acc, _band_time, _morph_time, _morph_mix, _explosion_time
    global _tilt_knob, _speed_knob, _tube_knob, _hue_knob
    global _shape_a, _shape_b, _palette_index, _torus_color_mode, _morphing, _explosion_active

    if inp.btn_pressed[0]: _tilt_knob = 0.558
    if inp.btn_pressed[1]: _speed_knob = 4.799
    if inp.btn_pressed[2]: _tube_knob = 2.263
    if inp.btn_pressed[3]:
        if _torus_color_mode >= 2:
            _palette_index = 0
        else:
            _hue_knob = 0.447

    if len(inp.btn_pressed) > 4 and inp.btn_pressed[4] and not _explosion_active and not _morphing:
        if _shape_b == SHAPE_TORUS:
            _shape_a = SHAPE_TORUS
            _shape_b = SHAPE_DIAMOND
            _morph_time = 0.0
            _morph_mix = 0.0
            _morphing = True
        else:
            _explosion_active = True
            _explosion_time = 0.0

    if len(inp.btn_pressed) > 5 and inp.btn_pressed[5]:
        _torus_color_mode = _torus_color_mode % TORUS_COLOR_MODE_COUNT + 1

    _tilt_knob = _wrap01(_tilt_knob + inp.knob_deltas[0] * 0.05)
    _speed_knob = _clamp(_speed_knob + inp.knob_deltas[1] * 0.1, KNOB2_MIN_VALUE, KNOB2_MAX_VALUE)
    _tube_knob = _clamp(_tube_knob + inp.knob_deltas[2] * 0.05, 0.0, KNOB3_MAX_VALUE)
    if _torus_color_mode >= 2:
        _palette_index = int(_clamp(_palette_index + inp.knob_deltas[3], 0, PALETTE_COUNT - 1))
    else:
        _hue_knob = _wrap01(_hue_knob + inp.knob_deltas[3] * 0.05)

    _time_acc += dt * _map_speed(_speed_knob)
    _band_time += dt

    if _explosion_active:
        _explosion_time += dt
        if _explosion_time >= EXPLOSION_STAGE1_SECONDS + EXPLOSION_STAGE2_SECONDS:
            _explosion_active = False
            _shape_a = SHAPE_TORUS
            _shape_b = SHAPE_TORUS
            _morph_mix = 0.0
            _morphing = False
        return

    if _morphing:
        _morph_time += dt
        _morph_mix = _smooth01(_morph_time / max(0.1, MORPH_TRANSITION_SECONDS))
        if _morph_mix >= 1.0:
            _shape_a = _shape_b
            _morph_mix = 0.0
            _morphing = False


def draw() -> None:
    w, h = pf_canvas.W, pf_canvas.H
    stage1_progress = -1.0
    if _explosion_active:
        if _explosion_time < EXPLOSION_STAGE1_SECONDS:
            stage1_progress = _clamp(_explosion_time / max(0.01, EXPLOSION_STAGE1_SECONDS), 0.0, 1.0)
        else:
            stage2_progress = _clamp((_explosion_time - EXPLOSION_STAGE1_SECONDS) / max(0.01, EXPLOSION_STAGE2_SECONDS), 0.0, 1.0)
            _draw_explosion_stage2(stage2_progress)
            pf_canvas.present()
            return

    aspect = w / max(1.0, h)
    tube_radius = _map_tube_radius(_tube_knob)
    diamond = _build_diamond_cache(tube_radius)
    t = _time_acc
    morph_mix = _morph_mix if _morphing else 0.0
    settled_torus = not _morphing and _shape_a == SHAPE_TORUS and _shape_b == SHAPE_TORUS
    settled_diamond = not _morphing and _shape_a == SHAPE_DIAMOND and _shape_b == SHAPE_DIAMOND
    view_tilt = (_tilt_knob - 0.5) * math.pi * 0.95
    ax = t * 0.73 + view_tilt
    ay = t * 1.03
    az = t * 0.31
    cx = math.cos(ax); sx = math.sin(ax)
    cy = math.cos(ay); sy = math.sin(ay)
    cz = math.cos(az); sz = math.sin(az)
    light_x, light_y, light_z = -0.38, -0.58, 0.72

    scale = _render_scale
    sample_offset = scale * 0.5
    for y in range(0, h, scale):
        sample_y = min(y + sample_offset, h - 0.5)
        py = 1.0 - sample_y * 2.0 / h
        for x in range(0, w, scale):
            sample_x = min(x + sample_offset, w - 0.5)
            px = (sample_x * 2.0 / w - 1.0) * aspect
            rox = px * 1.75
            roy = py * 1.75
            dist_along_ray = 0.0
            hx = hy = hz = 0.0
            hit = False
            step = 0
            for step in range(MAX_STEPS):
                vx = rox
                vy = roy
                vz = 3.2 - dist_along_ray
                x1 = vx * cy - vz * sy
                z1 = vx * sy + vz * cy
                y1 = vy
                y2 = y1 * cx + z1 * sx
                z2 = -y1 * sx + z1 * cx
                x2 = x1
                hx = x2 * cz + y2 * sz
                hy = -x2 * sz + y2 * cz
                hz = z2
                if settled_torus:
                    d = _torus_distance(hx, hy, hz, tube_radius)
                elif settled_diamond:
                    d = _diamond_distance(hx, hy, hz, diamond)
                else:
                    d = _morph_distance(hx, hy, hz, tube_radius, t, _shape_a, _shape_b, morph_mix, diamond)
                if d < HIT_DISTANCE:
                    hit = True
                    break
                dist_along_ray += d
                if dist_along_ray > MAX_DISTANCE:
                    break

            if not hit:
                if scale == 1:
                    _set_background(x, y, w, h, t)
                else:
                    _fill_block(x, y, scale, *_background_rgb(int(sample_x), int(sample_y), w, h, t))
                continue

            ring_len = math.sqrt(hx * hx + hy * hy)
            qx = ring_len - MAJOR_RADIUS
            if settled_torus:
                safe_ring_len = max(0.0001, ring_len)
                q_len = max(0.0001, math.sqrt(qx * qx + hz * hz))
                nx = hx / safe_ring_len * qx / q_len
                ny = hy / safe_ring_len * qx / q_len
                nz = hz / q_len
            else:
                eps = NORMAL_EPSILON
                if settled_diamond:
                    n1 = _diamond_distance(hx + eps, hy - eps, hz - eps, diamond)
                    n2 = _diamond_distance(hx - eps, hy - eps, hz + eps, diamond)
                    n3 = _diamond_distance(hx - eps, hy + eps, hz - eps, diamond)
                    n4 = _diamond_distance(hx + eps, hy + eps, hz + eps, diamond)
                else:
                    n1 = _morph_distance(hx + eps, hy - eps, hz - eps, tube_radius, t, _shape_a, _shape_b, morph_mix, diamond)
                    n2 = _morph_distance(hx - eps, hy - eps, hz + eps, tube_radius, t, _shape_a, _shape_b, morph_mix, diamond)
                    n3 = _morph_distance(hx - eps, hy + eps, hz - eps, tube_radius, t, _shape_a, _shape_b, morph_mix, diamond)
                    n4 = _morph_distance(hx + eps, hy + eps, hz + eps, tube_radius, t, _shape_a, _shape_b, morph_mix, diamond)
                dx = n1 - n2 - n3 + n4
                dy = -n1 - n2 + n3 + n4
                dz = -n1 + n2 - n3 + n4
                normal_len = max(0.0001, math.sqrt(dx * dx + dy * dy + dz * dz))
                nx = dx / normal_len
                ny = dy / normal_len
                nz = dz / normal_len

            diffuse = _clamp(nx * light_x + ny * light_y + nz * light_z, 0.0, 1.0)
            rim = _clamp(1.0 + nz, 0.0, 1.0)
            stripe = math.sin(math.atan2(hy, hx) * 14.0 + t * 3.0) * 0.5 + 0.5
            tube_stripe = math.sin(math.atan2(hz, qx) * 8.0 - t * 4.0) * 0.5 + 0.5
            depth_fade = _clamp(1.0 - dist_along_ray / MAX_DISTANCE, 0.0, 1.0)
            surface_brightness = _clamp(0.13 + diffuse * 0.82 + rim * rim * 0.28, 0.0, 1.0)
            shade = (DARK_SIDE_BRIGHTNESS + surface_brightness * (1.0 - DARK_SIDE_BRIGHTNESS)) * depth_fade
            hue = _hue_knob + stripe * 0.25 + tube_stripe * 0.05 + nz * 0.04
            palette_band_mode = _torus_color_mode >= 2 and (settled_torus or settled_diamond)

            if palette_band_mode and settled_diamond:
                girdle_z = diamond["size"] * 0.10
                diamond_z = hz + diamond["size"] * 0.20
                value = 1.0 if diamond_z >= girdle_z else 0.80
            elif palette_band_mode:
                smooth_rim = rim * rim
                torus_lighting = TORUS_BAND_AMBIENT + diffuse * TORUS_BAND_DIFFUSE + smooth_rim * TORUS_BAND_RIM
                value = _clamp(torus_lighting * depth_fade, 0.0, 1.0)
            else:
                value = _clamp((shade + stripe * tube_stripe * 0.20) * 1.15, 0.0, 1.0)

            if palette_band_mode:
                if settled_diamond:
                    ring_position = _wrap01((math.atan2(hy, hx) + math.pi + math.pi * 2.0 * 0.0625) / (math.pi * 2.0))
                    band_count = 8
                else:
                    ring_position = _wrap01(math.atan2(hy, hx) / (math.pi * 2.0))
                    band_count = max(1, math.ceil(1.0 / max(0.001, TORUS_BAND_WIDTH)))
                if _torus_color_mode == 3:
                    ring_position = _wrap01(ring_position - _band_time * TORUS_BAND_ROTATION_SPEED)
                band_index = min(band_count - 1, math.floor(ring_position * band_count))
                palette_position = band_index / (band_count - 1) if band_count > 1 else 0.0
                r, g, b = _palette_to_rgb(_palette_index, palette_position, value)
            else:
                r, g, b = pf_color.hsv_to_rgb(hue, 1.0, value)

            if not palette_band_mode and diffuse > 0.86 and tube_stripe > 0.48:
                sparkle = math.floor((diffuse - 0.86) * 260.0)
                r = min(255, r + sparkle)
                g = min(255, g + sparkle)
                b = min(255, b + sparkle)
            if step > MAX_STEPS - 5:
                fade = _clamp((MAX_STEPS - step) * 0.2, 0.0, 1.0)
                r = int(r * fade); g = int(g * fade); b = int(b * fade)
            if scale == 1:
                pf_canvas.set_pixel(x, y, r, g, b)
            else:
                _fill_block(x, y, scale, r, g, b)

    if stage1_progress >= 0.0:
        _draw_explosion_stage1(stage1_progress)
    pf_canvas.present()
