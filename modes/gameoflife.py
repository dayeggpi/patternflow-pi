import time
import random
import numpy as np
from PIL import Image
from modes.base import BaseMode

W, H = 64, 32


class GameOfLifeMode(BaseMode):
    def __init__(self, config):
        super().__init__(config)
        self.grid = None
        self.last_step = 0
        self.generation = 0
        self._cfg = {}
        self._last_cfg_load = 0.0
        self._init_grid()

    def _init_grid(self):
        self.grid = np.random.choice(
            [0, 1], size=(H, W), p=[0.65, 0.35]
        ).astype(np.uint8)
        self.generation = 0

    def start(self):
        super().start()
        self._init_grid()
        self._last_cfg_load = 0.0

    def _get_cfg(self):
        now = time.time()
        if now - self._last_cfg_load >= 0.25 or not self._cfg:
            self._cfg = self.config.get_section('gameoflife')
            self._last_cfg_load = now
        return self._cfg

    def _step(self):
        wrap = self._get_cfg().get('wrap', True)

        if wrap:
            neighbors = np.zeros((H, W), dtype=np.uint8)
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    if dy == 0 and dx == 0:
                        continue
                    neighbors += np.roll(np.roll(self.grid, dy, axis=0), dx, axis=1)
        else:
            padded = np.pad(self.grid, 1, mode='constant')
            neighbors = (
                padded[:-2, :-2] + padded[:-2, 1:-1] + padded[:-2, 2:] +
                padded[1:-1, :-2] + padded[1:-1, 2:] +
                padded[2:, :-2] + padded[2:, 1:-1] + padded[2:, 2:]
            )

        birth = (self.grid == 0) & (neighbors == 3)
        survive = (self.grid == 1) & ((neighbors == 2) | (neighbors == 3))
        self.grid = (birth | survive).astype(np.uint8)
        self.generation += 1

        if self.grid.sum() < 5:
            self._init_grid()

    def render(self, canvas):
        cfg = self._get_cfg()
        speed = max(1, min(30, cfg.get('speed', 10)))
        color = tuple(cfg.get('color', [0, 255, 0]))
        dead_color = tuple(cfg.get('dead_color', [0, 0, 0]))

        now = time.time()
        if now - self.last_step >= 1.0 / speed:
            self._step()
            self.last_step = now

        frame = np.empty((H, W, 3), dtype=np.uint8)
        frame[:, :] = dead_color
        frame[self.grid == 1] = color
        img = Image.fromarray(frame, 'RGB')

        canvas.SetImage(img)
