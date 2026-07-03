import time
from functools import lru_cache
from PIL import Image, ImageDraw, ImageFont
from modes.base import BaseMode, image_to_canvas


def _paste_text(img, pos, text, color, font):
    """Draw text via grayscale mask to avoid FreeType sub-pixel color artifacts."""
    mask = Image.new('L', img.size, 0)
    ImageDraw.Draw(mask).text(pos, text, fill=255, font=font)
    img.paste(color, mask=mask)

FONT_PATH = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'


@lru_cache(maxsize=8)
def load_font(size=8):
    try:
        return ImageFont.truetype(FONT_PATH, size)
    except Exception:
        try:
            return ImageFont.load_default(size=size)
        except Exception:
            return ImageFont.load_default()


class TextMode(BaseMode):
    def __init__(self, config):
        super().__init__(config)
        self.scroll_x = 64.0
        self.last_frame = time.time()
        self._cfg = {}
        self._last_cfg_load = 0.0
        self._layout_key = None
        self._font = None
        self._text_w = 0
        self._text_y = 0

    def start(self):
        super().start()
        self.scroll_x = 64.0
        self.last_frame = time.time()
        self._last_cfg_load = 0.0

    def _load_runtime(self):
        now = time.time()
        if now - self._last_cfg_load >= 0.25 or not self._cfg:
            self._cfg = self.config.get_section('text')
            self._last_cfg_load = now

        content = self._cfg.get('content', 'Hello World!')
        size = int(self._cfg.get('size', 1))
        font_size = min(30, max(6, size * 8))
        layout_key = (content, font_size)
        if layout_key != self._layout_key:
            self._font = load_font(font_size)
            bbox = self._font.getbbox(content)
            self._text_w = bbox[2] - bbox[0]
            text_h = bbox[3] - bbox[1]
            self._text_y = max(0, (32 - text_h) // 2)
            self._layout_key = layout_key

        return self._cfg, content, self._font, self._text_w, self._text_y

    def render(self, canvas):
        cfg, content, font, text_w, text_y = self._load_runtime()
        color = tuple(cfg.get('color', [255, 255, 255]))
        speed = cfg.get('speed', 30)      # pixels per second
        scroll = cfg.get('scroll', True)

        img = Image.new('RGB', (64, 32), (0, 0, 0))

        if scroll:
            now = time.time()
            elapsed = now - self.last_frame
            self.last_frame = now
            self.scroll_x -= speed * elapsed

            if self.scroll_x < -text_w:
                self.scroll_x = 64.0

            _paste_text(img, (int(self.scroll_x), text_y), content, color, font)
        else:
            text_x = max(0, (64 - text_w) // 2)
            _paste_text(img, (text_x, text_y), content, color, font)

        image_to_canvas(canvas, img)
