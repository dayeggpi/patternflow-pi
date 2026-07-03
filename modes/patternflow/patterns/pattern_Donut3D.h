// Knob 1: rotate view
// Knob 2: animation speed 
// Knob 3: body size
// Knob 4: hue or palette color
// Button 1: change animation mode 
// Button 2:  change color mode
// In simulation change ANIMATION_MODE and COLOR_MODE variables

#pragma once

#include <Arduino.h>
#include "config.h"
#include "src/core_display.h"
#include "src/core_encoders.h"
#include "src/core_canvas.h"
#include "src/core_math.h"
#include "src/core_color.h"
#include "color_palettes.h"

namespace Donut3DPattern {

const char* NAME = "Donut 3D";
const char* const KNOB_LABELS[4] = {"ROTATE", "SPEED", "BODY SIZE", "COLOR / PALETTE"};

constexpr float KNOB2_MIN_VALUE = 0.1f;
constexpr float KNOB2_MAX_VALUE = 10.0f;
constexpr float KNOB3_MAX_VALUE = 4.9f;
constexpr float MIN_SPEED = 1.0f;
constexpr float MAX_SPEED = 5.0f;
constexpr int MAX_STEPS = 34;
constexpr float MAX_DISTANCE = 7.0f;
constexpr float HIT_DISTANCE = 0.018f;
constexpr float MAJOR_RADIUS = 1.1f;
constexpr float DARK_SIDE_BRIGHTNESS = 0.80f;
constexpr float NORMAL_EPSILON = 0.035f;
constexpr float MORPH_TRANSITION_SECONDS = 4.0f;
constexpr int SHAPE_TORUS = 0;
constexpr int SHAPE_DIAMOND = 1;
constexpr float INV_SQRT_2 = 0.70710678f;
constexpr float EXPLOSION_STAGE1_SECONDS = 0.55f;
constexpr float EXPLOSION_STAGE1_SIZE = 1.0f;
constexpr float EXPLOSION_STAGE1_RING_WIDTH = 0.20f;
constexpr float EXPLOSION_STAGE2_SECONDS = 3.0f;
constexpr int EXPLOSION_STAGE2_PARTICLES = 50;
constexpr float EXPLOSION_STAGE2_SPEED = 5.0f;
constexpr int EXPLOSION_STAGE2_FRAGMENT_SIZE = 3;
constexpr int TORUS_COLOR_MODE_COUNT = 3;
constexpr float TORUS_BAND_WIDTH = 0.04f;
constexpr float TORUS_BAND_ROTATION_SPEED = 0.7f;
constexpr float TORUS_BAND_AMBIENT = 0.7f;
constexpr float TORUS_BAND_DIFFUSE = 1.0f;
constexpr float TORUS_BAND_RIM = 0.8f;

const uint8_t* const ACTIVE_PALETTES[] = {
  Cube3DPalettes::RAINBOW,
  Cube3DPalettes::PARTY,
  Cube3DPalettes::GreenRound,
  Cube3DPalettes::HeatRound,
  Cube3DPalettes::OceanRound
};

const float ACTIVE_PALETTE_BRIGHTNESS[] = {
  Cube3DPalettes::PALETTE_BRIGHTNESS[0], // Rainbow
  Cube3DPalettes::PALETTE_BRIGHTNESS[1], // Party
  Cube3DPalettes::PALETTE_BRIGHTNESS[7],  // GreenRound
  Cube3DPalettes::PALETTE_BRIGHTNESS[8],  // HeatRound
  Cube3DPalettes::PALETTE_BRIGHTNESS[9]  // OceanRound
};

const char* const ACTIVE_PALETTE_NAMES[] = {
  "Rainbow",
  "Party",
  "GreenRound",
  "HeatRound",
  "OceanRound"
};

constexpr int ACTIVE_PALETTE_COUNT = sizeof(ACTIVE_PALETTES) / sizeof(ACTIVE_PALETTES[0]);

struct Params {
  float timeAcc;
  float bandTime;
  float morphTime;
  float morphMix;
  float explosionTime;
  float tiltKnob;
  float speedKnob;
  float tubeKnob;
  float hueKnob;
  float particleAngles[EXPLOSION_STAGE2_PARTICLES];
  float particleSpeeds[EXPLOSION_STAGE2_PARTICLES];
  float particleDelays[EXPLOSION_STAGE2_PARTICLES];
  float particleHues[EXPLOSION_STAGE2_PARTICLES];
  int shapeA;
  int shapeB;
  int paletteIndex;
  int torusColorMode;
  bool morphing;
  bool explosionActive;
};

Params params;

struct DiamondCache {
  float size;
  float topZ;
  float crownSlope;
  float pavilionSlope;
  float crownScale;
  float pavilionScale;
  float crownOffset;
  float pavilionOffset;
};

inline float wrap01(float v) {
  v -= floorf(v);
  if (v < 0.0f) v += 1.0f;
  return v;
}

inline float mapKnob2ToSpeed(float v) {
  float n = (constrain(v, KNOB2_MIN_VALUE, KNOB2_MAX_VALUE) - KNOB2_MIN_VALUE) / (KNOB2_MAX_VALUE - KNOB2_MIN_VALUE);
  return MIN_SPEED + n * (MAX_SPEED - MIN_SPEED);
}

inline float mapKnob3ToTubeRadius(float v) {
  float n = constrain(v / KNOB3_MAX_VALUE, 0.0f, 1.0f);
  return 0.20f + n * 0.24f;
}

inline float torusDistance(float x, float y, float z, float tubeRadius) {
  float qx = sqrtf(x * x + y * y) - MAJOR_RADIUS;
  return sqrtf(qx * qx + z * z) - tubeRadius;
}

inline DiamondCache buildDiamondCache(float tubeRadius) {
  DiamondCache diamond;
  diamond.size = 0.6f + tubeRadius * 0.9f;
  diamond.topZ = diamond.size * 0.65f;
  float girdleZ = diamond.size * 0.10f;
  float pointZ = -diamond.size * 1.4f;
  float topRadius = diamond.size * 0.6f;
  float girdleRadius = diamond.size * 1.05f;
  diamond.crownSlope = (girdleRadius - topRadius) / (diamond.topZ - girdleZ);
  diamond.pavilionSlope = girdleRadius / (girdleZ - pointZ);
  diamond.crownScale = 1.0f / sqrtf(1.0f + diamond.crownSlope * diamond.crownSlope);
  diamond.pavilionScale = 1.0f / sqrtf(1.0f + diamond.pavilionSlope * diamond.pavilionSlope);
  diamond.crownOffset = topRadius + diamond.crownSlope * diamond.topZ;
  diamond.pavilionOffset = diamond.pavilionSlope * pointZ;
  return diamond;
}

inline float diamondDistance(float x, float y, float z, const DiamondCache& diamond) {
  float zz = z + diamond.size * 0.20f;
  float d = zz - diamond.topZ;
  float radius = max(max(fabsf(x), fabsf(y)), max(fabsf(x + y), fabsf(x - y)) * INV_SQRT_2);
  float crown = (radius + diamond.crownSlope * zz - diamond.crownOffset) * diamond.crownScale;
  float pavilion = (radius - diamond.pavilionSlope * zz + diamond.pavilionOffset) * diamond.pavilionScale;
  return max(d, max(crown, pavilion));
}

inline float shapeDistance(int shape, float x, float y, float z, float tubeRadius, float t, const DiamondCache& diamond) {
  if (shape == SHAPE_TORUS) return torusDistance(x, y, z, tubeRadius);
  return diamondDistance(x, y, z, diamond);
}

inline float smooth01(float v) {
  v = constrain(v, 0.0f, 1.0f);
  return v * v * (3.0f - 2.0f * v);
}

inline float morphDistance(float x, float y, float z, float tubeRadius, float t, int shapeA, int shapeB, float morphMix, const DiamondCache& diamond) {
  if (morphMix <= 0.0f || shapeA == shapeB) {
    return shapeDistance(shapeA, x, y, z, tubeRadius, t, diamond);
  }

  float dA = shapeDistance(shapeA, x, y, z, tubeRadius, t, diamond);
  float dB = shapeDistance(shapeB, x, y, z, tubeRadius, t, diamond);
  float swirl = PFMath::fastSin((x + y + z) * 4.2f + t * 2.0f) * 0.035f * morphMix * (1.0f - morphMix);
  return dA + (dB - dA) * morphMix + swirl;
}

inline uint8_t scaleByte(float v) {
  return (uint8_t)constrain((int)floorf(v), 0, 255);
}

inline void setPixelSafe(int x, int y, uint8_t r, uint8_t g, uint8_t b) {
  if (x >= 0 && x < PANEL_RES_W && y >= 0 && y < PANEL_RES_H) {
    PFCanvas::setPixel(x, y, r, g, b);
  }
}

inline void wrapIndex(int& value, int count) {
  while (value < 0) value += count;
  while (value >= count) value -= count;
}

inline void paletteToRgb(int paletteIndex, float position, float brightness, uint8_t& r, uint8_t& g, uint8_t& b) {
  paletteIndex = constrain(paletteIndex, 0, ACTIVE_PALETTE_COUNT - 1);
  position = constrain(position, 0.0f, 1.0f) * (float)(Cube3DPalettes::PALETTE_SIZE - 1);
  int colorIndex = (int)floorf(position);
  int nextColorIndex = min(colorIndex + 1, Cube3DPalettes::PALETTE_SIZE - 1);
  float mix = position - (float)colorIndex;
  float inverseMix = 1.0f - mix;
  float level = brightness * ACTIVE_PALETTE_BRIGHTNESS[paletteIndex];
  const uint8_t* palette = ACTIVE_PALETTES[paletteIndex];
  int offsetA = colorIndex * 3;
  int offsetB = nextColorIndex * 3;
  r = scaleByte((palette[offsetA] * inverseMix + palette[offsetB] * mix) * level);
  g = scaleByte((palette[offsetA + 1] * inverseMix + palette[offsetB + 1] * mix) * level);
  b = scaleByte((palette[offsetA + 2] * inverseMix + palette[offsetB + 2] * mix) * level);
}

inline void setBackground(int x, int y, int w, int h, float t) {
  float nx = (float)x / max(1.0f, (float)w - 1.0f);
  float ny = (float)y / max(1.0f, (float)h - 1.0f);
  float dx = nx - 0.5f;
  float dy = ny - 0.5f;
  float vignette = 1.0f - sqrtf(dx * dx + dy * dy) * 1.7f;
  float pulse = PFMath::fastSin(t * 0.55f + nx * 5.0f - ny * 3.0f) * 0.5f + 0.5f;
  uint8_t v = scaleByte(constrain(vignette, 0.0f, 1.0f) * (3.0f + pulse * 5.0f));
  PFCanvas::setPixel(x, y, 0, v, (uint8_t)min(255, (int)v + 2));
}

inline void initializeExplosionParticles() {
  uint32_t seed = 505;
  for (int i = 0; i < EXPLOSION_STAGE2_PARTICLES; i++) {
    seed = seed * 1664525UL + 1013904223UL;
    float randomAngle = (float)seed / 4294967296.0f;
    seed = seed * 1664525UL + 1013904223UL;
    float randomSpeed = (float)seed / 4294967296.0f;
    seed = seed * 1664525UL + 1013904223UL;
    float randomDelay = (float)seed / 4294967296.0f;
    params.particleAngles[i] = randomAngle * PFMath::TWO_PI_F;
    params.particleSpeeds[i] = 0.72f + randomSpeed * 0.56f;
    params.particleDelays[i] = randomDelay * 0.18f;
    params.particleHues[i] = (float)(i % 8) * 0.125f;
  }
}

inline void drawExplosionStage1(float progress) {
  const int w = PANEL_RES_W;
  const int h = PANEL_RES_H;
  const float cx = ((float)w - 1.0f) * 0.5f;
  const float cy = ((float)h - 1.0f) * 0.5f;
  const float minSide = (float)min(w, h);
  const float blastRadius = powf(progress, 0.65f) * minSide * EXPLOSION_STAGE1_SIZE;
  const float ringWidth = max(1.0f, minSide * EXPLOSION_STAGE1_RING_WIDTH);
  const float ringSpacing = ringWidth * 1.35f;
  const float fade = 1.0f - progress;

  for (int y = 0; y < h; y++) {
    float dy = (float)y - cy;
    for (int x = 0; x < w; x++) {
      float dx = (float)x - cx;
      float distance = sqrtf(dx * dx + dy * dy);
      float bestIntensity = 0.0f;
      int bestRing = -1;
      for (int ringIndex = 0; ringIndex < 4; ringIndex++) {
        float radius = blastRadius - (float)ringIndex * ringSpacing;
        if (radius < 0.0f) continue;
        float intensity = constrain(1.0f - fabsf(distance - radius) / ringWidth, 0.0f, 1.0f);
        if (intensity > bestIntensity) {
          bestIntensity = intensity;
          bestRing = ringIndex;
        }
      }
      if (bestRing < 0) continue;

      float intensity = bestIntensity * (0.65f + fade * 0.35f);
      uint8_t r = 255;
      uint8_t g = 255;
      uint8_t b = 255;
      if (bestRing == 1) { r = 255; g = 24; b = 8; }
      else if (bestRing == 2) { r = 135; g = 52; b = 18; }
      else if (bestRing == 3) { r = 255; g = 205; b = 20; }
      PFCanvas::setPixel(x, y, scaleByte(r * intensity), scaleByte(g * intensity), scaleByte(b * intensity));
    }
  }
}

inline void drawExplosionStage2(float progress) {
  const int w = PANEL_RES_W;
  const int h = PANEL_RES_H;
  const float cx = ((float)w - 1.0f) * 0.5f;
  const float cy = ((float)h - 1.0f) * 0.5f;
  const float travelDistance = (float)max(w, h) * 0.72f * EXPLOSION_STAGE2_SPEED;

  for (int y = 0; y < h; y++) {
    for (int x = 0; x < w; x++) setBackground(x, y, w, h, params.timeAcc);
  }

  for (int i = 0; i < EXPLOSION_STAGE2_PARTICLES; i++) {
    float localProgress = constrain(
      (progress - params.particleDelays[i]) / (1.0f - params.particleDelays[i]),
      0.0f, 1.0f
    );
    if (localProgress <= 0.0f) continue;

    float easedTravel = localProgress * localProgress * (2.0f - localProgress);
    float distance = easedTravel * travelDistance * params.particleSpeeds[i];
    float directionX = PFMath::fastCos(params.particleAngles[i]);
    float directionY = PFMath::fastSin(params.particleAngles[i]);
    int px = (int)floorf(cx + directionX * distance);
    int py = (int)floorf(cy + directionY * distance);
    float brightness = constrain(1.0f - localProgress * 0.72f, 0.0f, 1.0f);
    uint8_t r;
    uint8_t g;
    uint8_t b;
    PFColor::hsvToRgb(params.hueKnob + params.particleHues[i] + localProgress * 0.08f, 0.72f, brightness, r, g, b);

    for (int sy = 0; sy < EXPLOSION_STAGE2_FRAGMENT_SIZE; sy++) {
      for (int sx = 0; sx < EXPLOSION_STAGE2_FRAGMENT_SIZE; sx++) {
        setPixelSafe(px + sx, py + sy, r, g, b);
      }
    }
    setPixelSafe(
      (int)floorf((float)px - directionX * 3.0f),
      (int)floorf((float)py - directionY * 3.0f),
      scaleByte(r * 0.45f), scaleByte(g * 0.45f), scaleByte(b * 0.45f)
    );
  }
}

void setup() {
  PFMath::buildSinLUT();
  params.timeAcc = 0.0f;
  params.bandTime = 0.0f;
  params.morphTime = 0.0f;
  params.morphMix = 0.0f;
  params.explosionTime = 0.0f;
  params.tiltKnob = 0.558f;
  params.speedKnob = 4.799f;
  params.tubeKnob = 2.263f;
  params.hueKnob = 0.447f;
  params.paletteIndex = 0;
  params.torusColorMode = 1;
  params.shapeA = SHAPE_TORUS;
  params.shapeB = SHAPE_TORUS;
  params.morphing = false;
  params.explosionActive = false;
  initializeExplosionParticles();
}

void update(float dt, const InputFrame& input) {
  if (input.btnPressed[3]) {
    params.torusColorMode = params.torusColorMode % TORUS_COLOR_MODE_COUNT + 1;
  }

  if (!params.explosionActive && !params.morphing && input.btnPressed[0]) {
    if (params.shapeB == SHAPE_TORUS) {
      params.shapeA = SHAPE_TORUS;
      params.shapeB = SHAPE_DIAMOND;
      params.morphTime = 0.0f;
      params.morphMix = 0.0f;
      params.morphing = true;
    } else {
      params.explosionActive = true;
      params.explosionTime = 0.0f;
    }
  }

  params.tiltKnob = wrap01(params.tiltKnob + input.knobDeltas[0] * 0.05f);
  params.speedKnob = constrain(params.speedKnob + input.knobDeltas[1] * 0.1f, KNOB2_MIN_VALUE, KNOB2_MAX_VALUE);
  params.tubeKnob = constrain(params.tubeKnob + input.knobDeltas[2] * 0.05f, 0.0f, KNOB3_MAX_VALUE);
  if (params.torusColorMode >= 2) {
    params.paletteIndex += input.knobDeltas[3];
    wrapIndex(params.paletteIndex, ACTIVE_PALETTE_COUNT);
  } else {
    params.hueKnob = wrap01(params.hueKnob + input.knobDeltas[3] * 0.05f);
  }
  params.timeAcc += dt * mapKnob2ToSpeed(params.speedKnob);
  params.bandTime += dt;

  if (params.explosionActive) {
    params.explosionTime += dt;
    if (params.explosionTime >= EXPLOSION_STAGE1_SECONDS + EXPLOSION_STAGE2_SECONDS) {
      params.explosionActive = false;
      params.shapeA = SHAPE_TORUS;
      params.shapeB = SHAPE_TORUS;
      params.morphMix = 0.0f;
      params.morphing = false;
    }
    return;
  }

  if (params.morphing) {
    params.morphTime += dt;
    params.morphMix = smooth01(params.morphTime / max(0.1f, MORPH_TRANSITION_SECONDS));
    if (params.morphMix >= 1.0f) {
      params.shapeA = params.shapeB;
      params.morphMix = 0.0f;
      params.morphing = false;
    }
  }
}

void draw() {
  const int w = PANEL_RES_W;
  const int h = PANEL_RES_H;
  float stage1Progress = -1.0f;

  if (params.explosionActive) {
    if (params.explosionTime < EXPLOSION_STAGE1_SECONDS) {
      stage1Progress = constrain(params.explosionTime / max(0.01f, EXPLOSION_STAGE1_SECONDS), 0.0f, 1.0f);
    } else {
      float stage2Progress = constrain(
        (params.explosionTime - EXPLOSION_STAGE1_SECONDS) / max(0.01f, EXPLOSION_STAGE2_SECONDS),
        0.0f, 1.0f
      );
      drawExplosionStage2(stage2Progress);
      PFCanvas::present();
      return;
    }
  }

  const float aspect = (float)w / max(1.0f, (float)h);
  const float tubeRadius = mapKnob3ToTubeRadius(params.tubeKnob);
  const DiamondCache diamond = buildDiamondCache(tubeRadius);
  const float t = params.timeAcc;
  const int shapeA = params.shapeA;
  const int shapeB = params.shapeB;
  const float morphMix = params.morphing ? params.morphMix : 0.0f;
  const bool settledTorus = !params.morphing && shapeA == SHAPE_TORUS && shapeB == SHAPE_TORUS;
  const bool settledDiamond = !params.morphing && shapeA == SHAPE_DIAMOND && shapeB == SHAPE_DIAMOND;
  const float viewTilt = (params.tiltKnob - 0.5f) * PI * 0.95f;
  const float ax = t * 0.73f + viewTilt;
  const float ay = t * 1.03f;
  const float az = t * 0.31f;
  const float cx = PFMath::fastCos(ax);
  const float sx = PFMath::fastSin(ax);
  const float cy = PFMath::fastCos(ay);
  const float sy = PFMath::fastSin(ay);
  const float cz = PFMath::fastCos(az);
  const float sz = PFMath::fastSin(az);
  const float lightX = -0.38f;
  const float lightY = -0.58f;
  const float lightZ = 0.72f;

  for (int y = 0; y < h; y++) {
    float py = 1.0f - ((float)y + 0.5f) * 2.0f / (float)h;

    for (int x = 0; x < w; x++) {
      float px = (((float)x + 0.5f) * 2.0f / (float)w - 1.0f) * aspect;
      float rox = px * 1.75f;
      float roy = py * 1.75f;
      float distAlongRay = 0.0f;
      float hx = 0.0f;
      float hy = 0.0f;
      float hz = 0.0f;
      bool hit = false;
      int step = 0;

      for (step = 0; step < MAX_STEPS; step++) {
        float vx = rox;
        float vy = roy;
        float vz = 3.2f - distAlongRay;

        float x1 = vx * cy - vz * sy;
        float z1 = vx * sy + vz * cy;
        float y1 = vy;
        float y2 = y1 * cx + z1 * sx;
        float z2 = -y1 * sx + z1 * cx;
        float x2 = x1;
        hx = x2 * cz + y2 * sz;
        hy = -x2 * sz + y2 * cz;
        hz = z2;

        float d;
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
        setBackground(x, y, w, h, t);
        continue;
      }

      float ringLen = sqrtf(hx * hx + hy * hy);
      float qx = ringLen - MAJOR_RADIUS;
      float nx;
      float ny;
      float nz;
      if (settledTorus) {
        float safeRingLen = max(0.0001f, ringLen);
        float qLen = max(0.0001f, sqrtf(qx * qx + hz * hz));
        nx = hx / safeRingLen * qx / qLen;
        ny = hy / safeRingLen * qx / qLen;
        nz = hz / qLen;
      } else if (settledDiamond) {
        float eps = NORMAL_EPSILON;
        float n1 = diamondDistance(hx + eps, hy - eps, hz - eps, diamond);
        float n2 = diamondDistance(hx - eps, hy - eps, hz + eps, diamond);
        float n3 = diamondDistance(hx - eps, hy + eps, hz - eps, diamond);
        float n4 = diamondDistance(hx + eps, hy + eps, hz + eps, diamond);
        float dx = n1 - n2 - n3 + n4;
        float dy = -n1 - n2 + n3 + n4;
        float dz = -n1 + n2 - n3 + n4;
        float normalLen = max(0.0001f, sqrtf(dx * dx + dy * dy + dz * dz));
        nx = dx / normalLen;
        ny = dy / normalLen;
        nz = dz / normalLen;
      } else {
        float eps = NORMAL_EPSILON;
        float n1 = morphDistance(hx + eps, hy - eps, hz - eps, tubeRadius, t, shapeA, shapeB, morphMix, diamond);
        float n2 = morphDistance(hx - eps, hy - eps, hz + eps, tubeRadius, t, shapeA, shapeB, morphMix, diamond);
        float n3 = morphDistance(hx - eps, hy + eps, hz - eps, tubeRadius, t, shapeA, shapeB, morphMix, diamond);
        float n4 = morphDistance(hx + eps, hy + eps, hz + eps, tubeRadius, t, shapeA, shapeB, morphMix, diamond);
        float dx = n1 - n2 - n3 + n4;
        float dy = -n1 - n2 + n3 + n4;
        float dz = -n1 + n2 - n3 + n4;
        float normalLen = max(0.0001f, sqrtf(dx * dx + dy * dy + dz * dz));
        nx = dx / normalLen;
        ny = dy / normalLen;
        nz = dz / normalLen;
      }
      float diffuse = constrain(nx * lightX + ny * lightY + nz * lightZ, 0.0f, 1.0f);
      float rim = constrain(1.0f + nz, 0.0f, 1.0f);
      float stripe = PFMath::fastSin(atan2f(hy, hx) * 14.0f + t * 3.0f) * 0.5f + 0.5f;
      float tubeStripe = PFMath::fastSin(atan2f(hz, qx) * 8.0f - t * 4.0f) * 0.5f + 0.5f;
      float depthFade = constrain(1.0f - distAlongRay / MAX_DISTANCE, 0.0f, 1.0f);
      float surfaceBrightness = constrain(0.13f + diffuse * 0.82f + rim * rim * 0.28f, 0.0f, 1.0f);
      float shade = (DARK_SIDE_BRIGHTNESS + surfaceBrightness * (1.0f - DARK_SIDE_BRIGHTNESS)) * depthFade;
      float hue = params.hueKnob + stripe * 0.25f + tubeStripe * 0.05f + nz * 0.04f;
      bool paletteBandMode = params.torusColorMode >= 2 && (settledTorus || settledDiamond);
      float value;
      if (paletteBandMode && settledDiamond) {
        float girdleZ = diamond.size * 0.10f;
        float diamondZ = hz + diamond.size * 0.20f;
        float diamondLighting = diamondZ >= girdleZ ? 1.0f : 0.80f;
        value = diamondLighting;
      } else if (paletteBandMode) {
        float smoothRim = rim * rim;
        float torusLighting = TORUS_BAND_AMBIENT + diffuse * TORUS_BAND_DIFFUSE + smoothRim * TORUS_BAND_RIM;
        value = constrain(torusLighting * depthFade, 0.0f, 1.0f);
      } else {
        value = constrain((shade + stripe * tubeStripe * 0.20f)*1.15f, 0.0f, 1.0f);    // light change *1.0f
      }

      uint8_t r;
      uint8_t g;
      uint8_t b;
      if (paletteBandMode) {
        float ringPosition;
        int bandCount;
        if (settledDiamond) {
          ringPosition = wrap01((atan2f(hy, hx) + PI + PFMath::TWO_PI_F * 0.0625f) / PFMath::TWO_PI_F);
          bandCount = 8;
        } else {
          ringPosition = wrap01(atan2f(hy, hx) / PFMath::TWO_PI_F);
          float bandWidth = max(0.001f, TORUS_BAND_WIDTH);
          bandCount = max(1, (int)ceilf(1.0f / bandWidth));
        }
        if (params.torusColorMode == 3) {
          ringPosition = wrap01(ringPosition - params.bandTime * TORUS_BAND_ROTATION_SPEED);
        }
        int bandIndex = min(bandCount - 1, (int)floorf(ringPosition * (float)bandCount));
        float palettePosition = bandCount > 1 ? (float)bandIndex / (float)(bandCount - 1) : 0.0f;
        paletteToRgb(params.paletteIndex, palettePosition, value, r, g, b);
      } else {
        PFColor::hsvToRgb(hue, 1.0f, value, r, g, b);
      }

      if (!paletteBandMode && diffuse > 0.86f && tubeStripe > 0.48f) {
        int sparkle = (int)floorf((diffuse - 0.86f) * 260.0f);
        r = (uint8_t)min(255, (int)r + sparkle);
        g = (uint8_t)min(255, (int)g + sparkle);
        b = (uint8_t)min(255, (int)b + sparkle);
      }

      if (step > MAX_STEPS - 5) {
        float fade = constrain((MAX_STEPS - step) * 0.2f, 0.0f, 1.0f);
        r = scaleByte(r * fade);
        g = scaleByte(g * fade);
        b = scaleByte(b * fade);
      }

      PFCanvas::setPixel(x, y, r, g, b);
    }
  }

  if (stage1Progress >= 0.0f) drawExplosionStage1(stage1Progress);
  PFCanvas::present();
}

} // namespace Donut3DPattern
