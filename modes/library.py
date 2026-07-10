import os
import time
from PIL import Image
from modes.base import BaseMode, image_to_canvas

W, H = 64, 32
LIBRARY_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'static', 'library')


class LibraryMode(BaseMode):
    def __init__(self, config):
        super().__init__(config)
        self._items = []
        self._rotation_enabled = True
        self._interval = 10
        self._current_idx = 0
        self._item_start = 0.0
        self._frames = []
        self._durations = []
        self._frame_idx = 0
        self._frame_deadline = 0.0
        self._scroll_x = 0.0
        self._last_scroll_t = 0.0
        self._loaded_id = None
        self._last_cfg_check = 0.0

    def start(self):
        super().start()
        self._current_idx = 0
        self._item_start = time.time()
        self._scroll_x = 0.0
        self._last_scroll_t = time.time()
        self._loaded_id = None
        self._last_cfg_check = 0.0
        self._reload_cfg()

    def _reload_cfg(self):
        cfg = self.config.get_section('library')
        self._items = cfg.get('items', [])
        self._rotation_enabled = bool(cfg.get('rotation_enabled', True))
        self._interval = max(1, int(cfg.get('interval', 10) or 10))

    def _load_item(self, item):
        item_id = item.get('id')
        if item_id == self._loaded_id:
            return
        self._loaded_id = None
        self._frames = []
        self._durations = []

        filename = item.get('filename', '')
        if not filename:
            return
        path = os.path.join(LIBRARY_DIR, filename)
        if not os.path.exists(path):
            return

        try:
            img = Image.open(path)
            n = getattr(img, 'n_frames', 1)
            frames, durations = [], []
            for i in range(n):
                img.seek(i)
                frame = img.convert('RGB').copy()
                frames.append(frame)
                ms = img.info.get('duration', 100)
                durations.append(max(20, ms))
            self._frames = frames
            self._durations = durations
            self._frame_idx = 0
            self._frame_deadline = time.time() + durations[0] / 1000.0
            self._scroll_x = 0.0
            self._last_scroll_t = time.time()
            self._loaded_id = item_id
        except Exception:
            pass

    def render(self, canvas):
        now = time.time()

        if now - self._last_cfg_check >= 1.0:
            self._reload_cfg()
            self._last_cfg_check = now

        if not self._items:
            canvas.Clear()
            return

        if self._current_idx >= len(self._items):
            self._current_idx = 0
            self._item_start = now

        item = self._items[self._current_idx]
        duration = max(1, int(item.get('duration', self._interval) or self._interval))

        if self._rotation_enabled and len(self._items) > 1 and now - self._item_start >= duration:
            self._current_idx = (self._current_idx + 1) % len(self._items)
            self._item_start = now
            self._loaded_id = None
            item = self._items[self._current_idx]

        self._load_item(item)

        if not self._frames:
            canvas.Clear()
            return

        is_gif = len(self._frames) > 1
        if is_gif and now >= self._frame_deadline:
            self._frame_idx = (self._frame_idx + 1) % len(self._frames)
            self._frame_deadline = now + self._durations[self._frame_idx] / 1000.0

        source = self._frames[self._frame_idx]
        width = source.size[0]
        scroll = bool(item.get('scroll', False)) and width > W and not is_gif

        if scroll:
            elapsed = now - self._last_scroll_t
            self._last_scroll_t = now
            speed = max(1, min(120, int(item.get('scroll_speed', 20) or 20)))
            self._scroll_x = (self._scroll_x + speed * elapsed) % width
        else:
            self._scroll_x = 0.0
            self._last_scroll_t = now

        x = int(self._scroll_x)
        if width <= W:
            frame = source if source.size == (W, H) else source.resize((W, H), Image.LANCZOS)
        elif x + W <= width:
            frame = source.crop((x, 0, x + W, H))
        else:
            frame = Image.new('RGB', (W, H), (0, 0, 0))
            right_w = width - x
            frame.paste(source.crop((x, 0, width, H)), (0, 0))
            frame.paste(source.crop((0, 0, W - right_w, H)), (right_w, 0))

        image_to_canvas(canvas, frame)
