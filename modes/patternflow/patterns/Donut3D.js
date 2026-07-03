// Rotating 3D torus / diamond for Patternflow.
// Knob 1: rotate view
// Knob 2: animation speed 
// Knob 3: body size
// Knob 4: hue or palette color

// JS API has no buttons, so select the modes here:
const ANIMATION_MODE = 1; // 1 = torus, 2 = diamond
const COLOR_MODE = 1;     // 1 = hue, 2 = static palette bands, 3 = moving palette bands

const KNOB2_MIN_VALUE = 0.1;
const KNOB2_MAX_VALUE = 10.0;
const KNOB3_MAX_VALUE = 4.9;
const MIN_SPEED = 1.0;
const MAX_SPEED = 5.0;
const MAX_STEPS = 34;
const MAX_DISTANCE = 7.0;
const HIT_DISTANCE = 0.018;
const MAJOR_RADIUS = 1.1;
const DARK_SIDE_BRIGHTNESS = 0.80;
const NORMAL_EPSILON = 0.035;
const MORPH_TRANSITION_SECONDS = 4.0;
const SHAPE_TORUS = 0;
const SHAPE_DIAMOND = 1;
const INV_SQRT_2 = 0.70710678;

// Stage 1 controls: fast central bomb blast.
const EXPLOSION_STAGE1_SECONDS = 0.55;
const EXPLOSION_STAGE1_SIZE = 1;       // Fraction of the shortest screen side.
const EXPLOSION_STAGE1_RING_WIDTH = 0.20; // Fraction of the shortest screen side.

// Stage 2 controls: diamond fragments flying outwards.
const EXPLOSION_STAGE2_SECONDS = 3;
const EXPLOSION_STAGE2_PARTICLES = 50;
const EXPLOSION_STAGE2_SPEED = 5;
const EXPLOSION_STAGE2_FRAGMENT_SIZE = 3;

const TORUS_BAND_WIDTH = 0.04;       // Band width around the ring: 0.01 to 1.0.
const TORUS_BAND_ROTATION_SPEED = 0.7; // Band rotations around the torus per second.
const TORUS_BAND_AMBIENT = 0.7;     // Minimum brightness on the dark side.
const TORUS_BAND_DIFFUSE = 1;     // Directional light strength.
const TORUS_BAND_RIM = 0.8;         // Soft edge light for stronger curvature.
const PALETTE_SIZE = 16;
const PALETTE_COUNT = 5;
// Knob 4 order matches ACTIVE_PALETTES in pattern_505_Donut3D.h.
const PALETTE_BRIGHTNESS = [1.0, 1.0, 1.0, 1.0, 1.0];

const RAINBOW_PALETTE = [
  255, 0, 0, 213, 42, 0, 171, 85, 0, 171, 127, 0,
  171, 171, 0, 86, 213, 0, 0, 255, 0, 0, 213, 42,
  0, 171, 85, 0, 86, 170, 0, 0, 255, 42, 0, 213,
  85, 0, 171, 127, 0, 129, 171, 0, 85, 213, 0, 43
];
const PARTY_PALETTE = [
  85, 0, 171, 132, 0, 124, 181, 0, 75, 229, 0, 27,
  232, 23, 0, 184, 71, 0, 171, 119, 0, 171, 171, 0,
  171, 85, 0, 221, 34, 0, 242, 0, 14, 194, 0, 62,
  143, 0, 113, 95, 0, 161, 47, 0, 208, 0, 7, 249
];
const GREEN_ROUND_PALETTE = [
  230, 255, 170, 135, 220, 90, 75, 180, 65, 35, 135, 48,
  12, 95, 36, 0, 120, 28, 20, 155, 45, 50, 190, 65,
  100, 225, 90, 43, 223, 43, 10, 229, 10, 0, 230, 0,
  20, 155, 45, 50, 190, 65, 100, 225, 90, 170, 255, 130
];
const HEAT_ROUND_PALETTE = [
  255, 0, 0, 255, 36, 0, 255, 73, 0, 255, 109, 0,
  255, 146, 0, 255, 182, 0, 255, 219, 0, 255, 255, 0,
  255, 255, 34, 255, 255, 68, 255, 255, 102, 255, 255, 122,
  255, 255, 143, 255, 255, 163, 255, 255, 184, 255, 255, 204
];
const OCEAN_ROUND_PALETTE = [
  0, 92, 210, 24, 115, 215, 49, 139, 220, 73, 162, 225,
  97, 185, 230, 121, 208, 235, 146, 232, 240, 170, 255, 245,
  149, 235, 241, 128, 214, 236, 106, 194, 232, 85, 174, 228,
  64, 153, 223, 43, 133, 219, 21, 112, 214, 0, 92, 210
];
const PALETTES = [
  RAINBOW_PALETTE,
  PARTY_PALETTE,
  GREEN_ROUND_PALETTE,
  HEAT_ROUND_PALETTE,
  OCEAN_ROUND_PALETTE
];

function clamp(v, lo, hi) {
  return Math.max(lo, Math.min(hi, v));
}

function wrap01(v) {
  v -= Math.floor(v);
  if (v < 0.0) v += 1.0;
  return v;
}

function mapKnob2ToSpeed(v) {
  let n = (clamp(v, KNOB2_MIN_VALUE, KNOB2_MAX_VALUE) - KNOB2_MIN_VALUE) /
    (KNOB2_MAX_VALUE - KNOB2_MIN_VALUE);
  return MIN_SPEED + n * (MAX_SPEED - MIN_SPEED);
}

function mapKnob3ToTubeRadius(v) {
  let n = clamp(v / KNOB3_MAX_VALUE, 0.0, 1.0);
  return 0.20 + n * 0.24;
}

function torusDistance(x, y, z, tubeRadius) {
  let qx = Math.sqrt(x * x + y * y) - MAJOR_RADIUS;
  return Math.sqrt(qx * qx + z * z) - tubeRadius;
}

function buildDiamondCache(tubeRadius, diamond) {
  diamond.size = 0.6 + tubeRadius * 0.9;
  diamond.topZ = diamond.size * 0.65;
  let girdleZ = diamond.size * 0.10;
  let pointZ = -diamond.size * 1.4;
  let topRadius = diamond.size * 0.6;
  let girdleRadius = diamond.size * 1.05;
  diamond.crownSlope = (girdleRadius - topRadius) / (diamond.topZ - girdleZ);
  diamond.pavilionSlope = girdleRadius / (girdleZ - pointZ);
  diamond.crownScale = 1.0 / Math.sqrt(1.0 + diamond.crownSlope * diamond.crownSlope);
  diamond.pavilionScale = 1.0 / Math.sqrt(1.0 + diamond.pavilionSlope * diamond.pavilionSlope);
  diamond.crownOffset = topRadius + diamond.crownSlope * diamond.topZ;
  diamond.pavilionOffset = diamond.pavilionSlope * pointZ;
}

function diamondDistance(x, y, z, diamond) {
  let zz = z + diamond.size * 0.20;
  let d = zz - diamond.topZ;
  let radius = Math.max(
    Math.max(Math.abs(x), Math.abs(y)),
    Math.max(Math.abs(x + y), Math.abs(x - y)) * INV_SQRT_2
  );
  let crown = (radius + diamond.crownSlope * zz - diamond.crownOffset) * diamond.crownScale;
  let pavilion = (radius - diamond.pavilionSlope * zz + diamond.pavilionOffset) * diamond.pavilionScale;
  return Math.max(d, Math.max(crown, pavilion));
}

function shapeDistance(shape, x, y, z, tubeRadius, diamond) {
  if (shape === SHAPE_TORUS) return torusDistance(x, y, z, tubeRadius);
  return diamondDistance(x, y, z, diamond);
}

function smooth01(v) {
  v = clamp(v, 0.0, 1.0);
  return v * v * (3.0 - 2.0 * v);
}

function morphDistance(x, y, z, tubeRadius, t, shapeA, shapeB, morphMix, diamond) {
  if (morphMix <= 0.0 || shapeA === shapeB) {
    return shapeDistance(shapeA, x, y, z, tubeRadius, diamond);
  }

  let dA = shapeDistance(shapeA, x, y, z, tubeRadius, diamond);
  let dB = shapeDistance(shapeB, x, y, z, tubeRadius, diamond);
  let swirl = Math.sin((x + y + z) * 4.2 + t * 2.0) * 0.035 * morphMix * (1.0 - morphMix);
  return dA + (dB - dA) * morphMix + swirl;
}

function hsvToRgb(h, s, v, out) {
  h = wrap01(h);
  let i = Math.floor(h * 6.0);
  let f = h * 6.0 - i;
  let p = v * (1.0 - s);
  let q = v * (1.0 - f * s);
  let t = v * (1.0 - (1.0 - f) * s);
  let r;
  let g;
  let b;

  switch (i % 6) {
    case 0: r = v; g = t; b = p; break;
    case 1: r = q; g = v; b = p; break;
    case 2: r = p; g = v; b = t; break;
    case 3: r = p; g = q; b = v; break;
    case 4: r = t; g = p; b = v; break;
    default: r = v; g = p; b = q; break;
  }

  out[0] = Math.floor(clamp(r * 255.0, 0.0, 255.0));
  out[1] = Math.floor(clamp(g * 255.0, 0.0, 255.0));
  out[2] = Math.floor(clamp(b * 255.0, 0.0, 255.0));
}

function paletteToRgb(paletteIndex, position, brightness, out) {
  let palette = PALETTES[paletteIndex];
  position = clamp(position, 0.0, 1.0) * (PALETTE_SIZE - 1);
  let colorIndex = Math.floor(position);
  let mix = position - colorIndex;
  let nextColorIndex = Math.min(colorIndex + 1, PALETTE_SIZE - 1);
  let offsetA = colorIndex * 3;
  let offsetB = nextColorIndex * 3;
  let inverseMix = 1.0 - mix;
  let level = brightness * PALETTE_BRIGHTNESS[paletteIndex];

  out[0] = Math.floor(
    (palette[offsetA] * inverseMix + palette[offsetB] * mix) * level
  );
  out[1] = Math.floor(
    (palette[offsetA + 1] * inverseMix + palette[offsetB + 1] * mix) * level
  );
  out[2] = Math.floor(
    (palette[offsetA + 2] * inverseMix + palette[offsetB + 2] * mix) * level
  );
}

function setBackground(display, x, y, w, h, t) {
  let nx = x / Math.max(1.0, w - 1.0);
  let ny = y / Math.max(1.0, h - 1.0);
  let dx = nx - 0.5;
  let dy = ny - 0.5;
  let vignette = 1.0 - Math.sqrt(dx * dx + dy * dy) * 1.7;
  let pulse = Math.sin(t * 0.55 + nx * 5.0 - ny * 3.0) * 0.5 + 0.5;
  let v = Math.floor(clamp(vignette, 0.0, 1.0) * (3.0 + pulse * 5.0));
  display.setPixel(x, y, 0, v, Math.min(255, v + 2));
}

function setPixelSafe(display, x, y, r, g, b) {
  if (x >= 0 && x < display.width && y >= 0 && y < display.height) {
    display.setPixel(x, y, r, g, b);
  }
}

function initializeExplosionParticles(params) {
  params.particleAngles = [];
  params.particleSpeeds = [];
  params.particleDelays = [];
  params.particleHues = [];

  let seed = 505;
  for (let i = 0; i < EXPLOSION_STAGE2_PARTICLES; i++) {
    seed = (seed * 1664525 + 1013904223) >>> 0;
    let randomAngle = seed / 4294967296.0;
    seed = (seed * 1664525 + 1013904223) >>> 0;
    let randomSpeed = seed / 4294967296.0;
    seed = (seed * 1664525 + 1013904223) >>> 0;
    let randomDelay = seed / 4294967296.0;

    params.particleAngles[i] = randomAngle * Math.PI * 2.0;
    params.particleSpeeds[i] = 0.72 + randomSpeed * 0.56;
    params.particleDelays[i] = randomDelay * 0.18;
    params.particleHues[i] = (i % 8) * 0.125;
  }
}

function drawExplosionStage1(display, params, progress) {
  let w = display.width;
  let h = display.height;
  let cx = (w - 1) * 0.5;
  let cy = (h - 1) * 0.5;
  let minSide = Math.min(w, h);
  let blastRadius = Math.pow(progress, 0.65) * minSide * EXPLOSION_STAGE1_SIZE;
  let ringWidth = Math.max(1.0, minSide * EXPLOSION_STAGE1_RING_WIDTH);
  let ringSpacing = ringWidth * 1.35;
  let fade = 1.0 - progress;

  for (let y = 0; y < h; y++) {
    let dy = y - cy;
    for (let x = 0; x < w; x++) {
      let dx = x - cx;
      let distance = Math.sqrt(dx * dx + dy * dy);
      let bestIntensity = 0.0;
      let bestRing = -1;

      for (let ringIndex = 0; ringIndex < 4; ringIndex++) {
        let radius = blastRadius - ringIndex * ringSpacing;
        if (radius < 0.0) continue;

        let intensity = clamp(
          1.0 - Math.abs(distance - radius) / ringWidth,
          0.0,
          1.0
        );
        if (intensity > bestIntensity) {
          bestIntensity = intensity;
          bestRing = ringIndex;
        }
      }

      if (bestRing >= 0) {
        let intensity = bestIntensity * (0.65 + fade * 0.35);
        let r;
        let g;
        let b;

        if (bestRing === 0) {        // White outer circle.
          r = 255;
          g = 255;
          b = 255;
        } else if (bestRing === 1) { // Red circle.
          r = 255;
          g = 24;
          b = 8;
        } else if (bestRing === 2) { // Brown circle.
          r = 135;
          g = 52;
          b = 18;
        } else {                     // Yellow inner circle.
          r = 255;
          g = 205;
          b = 20;
        }

        display.setPixel(
          x,
          y,
          Math.floor(r * intensity),
          Math.floor(g * intensity),
          Math.floor(b * intensity)
        );
      }
    }
  }
}

function drawExplosionStage2(display, params, progress) {
  let w = display.width;
  let h = display.height;
  let cx = (w - 1) * 0.5;
  let cy = (h - 1) * 0.5;
  let travelDistance = Math.max(w, h) * 0.72 * EXPLOSION_STAGE2_SPEED;
  let rgb = params.rgb;

  for (let y = 0; y < h; y++) {
    for (let x = 0; x < w; x++) {
      setBackground(display, x, y, w, h, params.timeAcc);
    }
  }

  for (let i = 0; i < EXPLOSION_STAGE2_PARTICLES; i++) {
    let localProgress = clamp(
      (progress - params.particleDelays[i]) / (1.0 - params.particleDelays[i]),
      0.0,
      1.0
    );
    if (localProgress <= 0.0) continue;

    let easedTravel = localProgress * localProgress * (2.0 - localProgress);
    let distance = easedTravel * travelDistance * params.particleSpeeds[i];
    let angle = params.particleAngles[i];
    let directionX = Math.cos(angle);
    let directionY = Math.sin(angle);
    let px = Math.floor(cx + directionX * distance);
    let py = Math.floor(cy + directionY * distance);
    let brightness = clamp(1.0 - localProgress * 0.72, 0.0, 1.0);
    let hue = params.hueKnob + params.particleHues[i] + localProgress * 0.08;
    hsvToRgb(hue, 0.72, brightness, rgb);

    for (let sy = 0; sy < EXPLOSION_STAGE2_FRAGMENT_SIZE; sy++) {
      for (let sx = 0; sx < EXPLOSION_STAGE2_FRAGMENT_SIZE; sx++) {
        setPixelSafe(display, px + sx, py + sy, rgb[0], rgb[1], rgb[2]);
      }
    }

    let tailX = Math.floor(px - directionX * 3.0);
    let tailY = Math.floor(py - directionY * 3.0);
    setPixelSafe(
      display,
      tailX,
      tailY,
      Math.floor(rgb[0] * 0.45),
      Math.floor(rgb[1] * 0.45),
      Math.floor(rgb[2] * 0.45)
    );
  }
}

export function setup(params) {
  params.timeAcc = 0.0;
  params.bandTime = 0.0;
  params.morphTime = 0.0;
  params.morphMix = 0.0;
  params.tiltKnob = 0.558;
  params.speedKnob = 4.799;
  params.tubeKnob = 2.263;
  params.hueKnob = 0.447;
  params.paletteIndex = 0;
  params.shapeA = ANIMATION_MODE === 2 ? SHAPE_DIAMOND : SHAPE_TORUS;
  params.shapeB = params.shapeA;
  params.morphing = false;
  params.explosionActive = false;
  params.explosionTime = 0.0;
  params.rgb = [0, 0, 0];
  params.diamond = {};
  initializeExplosionParticles(params);
}

export function update(dt, input, params) {

  if (input && input.knobValues) {
    params.tiltKnob = wrap01(input.knobValues[0]);
    params.speedKnob = clamp(input.knobValues[1], KNOB2_MIN_VALUE, KNOB2_MAX_VALUE);
    params.tubeKnob = clamp(input.knobValues[2], 0.0, KNOB3_MAX_VALUE);
    if (COLOR_MODE >= 2) {
      params.paletteIndex = Math.floor(clamp(input.knobValues[3], 0.0, 0.999) * PALETTE_COUNT);
    } else {
      params.hueKnob = wrap01(input.knobValues[3]);
    }
  } else if (input && input.knobDeltas) {
    params.tiltKnob = wrap01(params.tiltKnob + input.knobDeltas[0] * 0.05);
    params.speedKnob = clamp(params.speedKnob + input.knobDeltas[1] * 0.1, KNOB2_MIN_VALUE, KNOB2_MAX_VALUE);
    params.tubeKnob = clamp(params.tubeKnob + input.knobDeltas[2] * 0.05, 0.0, KNOB3_MAX_VALUE);
    if (COLOR_MODE >= 2) {
      params.paletteIndex = Math.floor(clamp(
        params.paletteIndex + input.knobDeltas[3],
        0,
        PALETTE_COUNT - 1
      ));
    } else {
      params.hueKnob = wrap01(params.hueKnob + input.knobDeltas[3] * 0.05);
    }
  }

  params.timeAcc += dt * mapKnob2ToSpeed(params.speedKnob);
  params.bandTime += dt;

  if (params.explosionActive) {
    params.explosionTime += dt;
    if (params.explosionTime >= EXPLOSION_STAGE1_SECONDS + EXPLOSION_STAGE2_SECONDS) {
      params.explosionActive = false;
      params.shapeA = SHAPE_TORUS;
      params.shapeB = SHAPE_TORUS;
      params.morphMix = 0.0;
      params.morphing = false;
    }
    return;
  }

  if (params.morphing) {
    params.morphTime += dt;
    params.morphMix = smooth01(params.morphTime / Math.max(0.1, MORPH_TRANSITION_SECONDS));
    if (params.morphMix >= 1.0) {
      params.shapeA = params.shapeB;
      params.morphMix = 0.0;
      params.morphing = false;
    }
  }
}

export function draw(display, params, time) {
  let w = display.width;
  let h = display.height;
  let stage1Progress = -1.0;

  if (params.explosionActive) {
    if (params.explosionTime < EXPLOSION_STAGE1_SECONDS) {
      stage1Progress = clamp(
        params.explosionTime / Math.max(0.01, EXPLOSION_STAGE1_SECONDS),
        0.0,
        1.0
      );
    } else {
      let stage2Progress = clamp(
        (params.explosionTime - EXPLOSION_STAGE1_SECONDS) /
          Math.max(0.01, EXPLOSION_STAGE2_SECONDS),
        0.0,
        1.0
      );
      drawExplosionStage2(display, params, stage2Progress);
      return;
    }
  }

  let aspect = w / Math.max(1.0, h);
  let tubeRadius = mapKnob3ToTubeRadius(params.tubeKnob);
  let diamond = params.diamond;
  buildDiamondCache(tubeRadius, diamond);

  let t = params.timeAcc;
  let shapeA = params.shapeA;
  let shapeB = params.shapeB;
  let morphMix = params.morphing ? params.morphMix : 0.0;
  let settledTorus = !params.morphing && shapeA === SHAPE_TORUS && shapeB === SHAPE_TORUS;
  let settledDiamond = !params.morphing && shapeA === SHAPE_DIAMOND && shapeB === SHAPE_DIAMOND;
  let viewTilt = (params.tiltKnob - 0.5) * Math.PI * 0.95;
  let ax = t * 0.73 + viewTilt;
  let ay = t * 1.03;
  let az = t * 0.31;
  let cx = Math.cos(ax);
  let sx = Math.sin(ax);
  let cy = Math.cos(ay);
  let sy = Math.sin(ay);
  let cz = Math.cos(az);
  let sz = Math.sin(az);
  let lightX = -0.38;
  let lightY = -0.58;
  let lightZ = 0.72;
  let rgb = params.rgb;

  for (let y = 0; y < h; y++) {
    let py = 1.0 - (y + 0.5) * 2.0 / h;

    for (let x = 0; x < w; x++) {
      let px = ((x + 0.5) * 2.0 / w - 1.0) * aspect;
      let rox = px * 1.75;
      let roy = py * 1.75;
      let distAlongRay = 0.0;
      let hx = 0.0;
      let hy = 0.0;
      let hz = 0.0;
      let hit = false;
      let step = 0;

      for (step = 0; step < MAX_STEPS; step++) {
        let vx = rox;
        let vy = roy;
        let vz = 3.2 - distAlongRay;

        let x1 = vx * cy - vz * sy;
        let z1 = vx * sy + vz * cy;
        let y1 = vy;
        let y2 = y1 * cx + z1 * sx;
        let z2 = -y1 * sx + z1 * cx;
        let x2 = x1;
        hx = x2 * cz + y2 * sz;
        hy = -x2 * sz + y2 * cz;
        hz = z2;

        let d;
        if (settledTorus) {
          d = torusDistance(hx, hy, hz, tubeRadius);
        } else if (settledDiamond) {
          d = diamondDistance(hx, hy, hz, diamond);
        } else {
          d = morphDistance(hx, hy, hz, tubeRadius, t, shapeA, shapeB, morphMix, diamond);
        }

        if (d < HIT_DISTANCE) {
          hit = true;
          break;
        }

        distAlongRay += d;
        if (distAlongRay > MAX_DISTANCE) break;
      }

      if (!hit) {
        setBackground(display, x, y, w, h, t);
        continue;
      }

      let ringLen = Math.sqrt(hx * hx + hy * hy);
      let qx = ringLen - MAJOR_RADIUS;
      let nx;
      let ny;
      let nz;

      if (settledTorus) {
        let safeRingLen = Math.max(0.0001, ringLen);
        let qLen = Math.max(0.0001, Math.sqrt(qx * qx + hz * hz));
        nx = hx / safeRingLen * qx / qLen;
        ny = hy / safeRingLen * qx / qLen;
        nz = hz / qLen;
      } else {
        let eps = NORMAL_EPSILON;
        let n1;
        let n2;
        let n3;
        let n4;

        if (settledDiamond) {
          n1 = diamondDistance(hx + eps, hy - eps, hz - eps, diamond);
          n2 = diamondDistance(hx - eps, hy - eps, hz + eps, diamond);
          n3 = diamondDistance(hx - eps, hy + eps, hz - eps, diamond);
          n4 = diamondDistance(hx + eps, hy + eps, hz + eps, diamond);
        } else {
          n1 = morphDistance(hx + eps, hy - eps, hz - eps, tubeRadius, t, shapeA, shapeB, morphMix, diamond);
          n2 = morphDistance(hx - eps, hy - eps, hz + eps, tubeRadius, t, shapeA, shapeB, morphMix, diamond);
          n3 = morphDistance(hx - eps, hy + eps, hz - eps, tubeRadius, t, shapeA, shapeB, morphMix, diamond);
          n4 = morphDistance(hx + eps, hy + eps, hz + eps, tubeRadius, t, shapeA, shapeB, morphMix, diamond);
        }

        let dx = n1 - n2 - n3 + n4;
        let dy = -n1 - n2 + n3 + n4;
        let dz = -n1 + n2 - n3 + n4;
        let normalLen = Math.max(0.0001, Math.sqrt(dx * dx + dy * dy + dz * dz));
        nx = dx / normalLen;
        ny = dy / normalLen;
        nz = dz / normalLen;
      }

      let diffuse = clamp(nx * lightX + ny * lightY + nz * lightZ, 0.0, 1.0);
      let rim = clamp(1.0 + nz, 0.0, 1.0);
      let stripe = Math.sin(Math.atan2(hy, hx) * 14.0 + t * 3.0) * 0.5 + 0.5;
      let tubeStripe = Math.sin(Math.atan2(hz, qx) * 8.0 - t * 4.0) * 0.5 + 0.5;
      let depthFade = clamp(1.0 - distAlongRay / MAX_DISTANCE, 0.0, 1.0);
      let surfaceBrightness = clamp(0.13 + diffuse * 0.82 + rim * rim * 0.28, 0.0, 1.0);
      let shade = (DARK_SIDE_BRIGHTNESS +
        surfaceBrightness * (1.0 - DARK_SIDE_BRIGHTNESS)) * depthFade;
      let hue = params.hueKnob + stripe * 0.25 + tubeStripe * 0.05 + nz * 0.04;

      let paletteBandMode = COLOR_MODE >= 2 && (settledTorus || settledDiamond);
      let value;
      if (paletteBandMode && settledDiamond) {
        let girdleZ = diamond.size * 0.10;
        let diamondZ = hz + diamond.size * 0.20;
        value = diamondZ >= girdleZ ? 1.0 : 0.80;
      } else if (paletteBandMode) {
        let smoothRim = rim * rim;
        let torusLighting =
          TORUS_BAND_AMBIENT +
          diffuse * TORUS_BAND_DIFFUSE +
          smoothRim * TORUS_BAND_RIM;
        value = clamp(torusLighting * depthFade, 0.0, 1.0);
      } else {
        value = clamp((shade + stripe * tubeStripe * 0.20) * 1.15, 0.0, 1.0);
      }

      if (paletteBandMode) {
        let ringPosition;
        let bandCount;
        if (settledDiamond) {
          ringPosition = wrap01(
            (Math.atan2(hy, hx) + Math.PI + Math.PI * 2.0 * 0.0625) /
              (Math.PI * 2.0)
          );
          bandCount = 8;
        } else {
          ringPosition = wrap01(Math.atan2(hy, hx) / (Math.PI * 2.0));
          let bandWidth = Math.max(0.001, TORUS_BAND_WIDTH);
          bandCount = Math.max(1, Math.ceil(1.0 / bandWidth));
        }
        if (COLOR_MODE === 3) {
          ringPosition = wrap01(
            ringPosition - params.bandTime * TORUS_BAND_ROTATION_SPEED
          );
        }
        let bandIndex = Math.min(bandCount - 1, Math.floor(ringPosition * bandCount));
        let palettePosition = bandCount > 1 ? bandIndex / (bandCount - 1) : 0.0;
        paletteToRgb(params.paletteIndex, palettePosition, value, rgb);
      } else {
        hsvToRgb(hue, 1, value, rgb);
      }

      if (!paletteBandMode && diffuse > 0.86 && tubeStripe > 0.48) {
        let sparkle = Math.floor((diffuse - 0.86) * 260.0);
        rgb[0] = Math.min(255, rgb[0] + sparkle);
        rgb[1] = Math.min(255, rgb[1] + sparkle);
        rgb[2] = Math.min(255, rgb[2] + sparkle);
      }

      if (step > MAX_STEPS - 5) {
        let fade = clamp((MAX_STEPS - step) * 0.2, 0.0, 1.0);
        rgb[0] = Math.floor(rgb[0] * fade);
        rgb[1] = Math.floor(rgb[1] * fade);
        rgb[2] = Math.floor(rgb[2] * fade);
      }

      display.setPixel(x, y, rgb[0], rgb[1], rgb[2]);
    }
  }

  if (stage1Progress >= 0.0) {
    drawExplosionStage1(display, params, stage1Progress);
  }
}
