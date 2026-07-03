from abc import ABC, abstractmethod


def image_to_canvas(canvas, img):
    """Push a PIL RGB image via SetPixel. SetImage skips rows on some builds."""
    if img.mode != 'RGB':
        img = img.convert('RGB')
    pixels = img.load()
    w, h = img.size
    for y in range(h):
        for x in range(w):
            r, g, b = pixels[x, y]
            canvas.SetPixel(x, y, r, g, b)


class BaseMode(ABC):
    def __init__(self, config):
        self.config = config
        self.active = False

    def start(self):
        self.active = True

    def stop(self):
        self.active = False

    def update_config(self, kwargs):
        if kwargs:
            section = self.__class__.__name__.lower().replace('mode', '')
            self.config.set_section(section, kwargs)

    @abstractmethod
    def render(self, canvas):
        pass
