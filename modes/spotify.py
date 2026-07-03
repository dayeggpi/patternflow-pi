import os
import time
import threading
import io
import requests
from PIL import Image, ImageDraw, ImageFont
from modes.base import BaseMode

try:
    import spotipy
    from spotipy.oauth2 import SpotifyOAuth
    SPOTIPY_AVAILABLE = True
except ImportError:
    SPOTIPY_AVAILABLE = False

FONT_PATH = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
FONT_BOLD_PATH = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
ART_SIZE = 22
PANEL_X = ART_SIZE + 2
PANEL_W = 64 - PANEL_X
SCROLL_SPEED = 12   # px/sec
SCROLL_GAP = 16     # blank px between text end and restart

TEXT_GLYPHS = {
    ' ': ['000', '000', '000', '000', '000', '000', '000'],
    '!': ['1', '1', '1', '1', '1', '0', '1'],
    '"': ['101', '101', '000', '000', '000', '000', '000'],
    '#': ['01010', '11111', '01010', '01010', '11111', '01010', '00000'],
    '$': ['01110', '10100', '10100', '01110', '00101', '00101', '11110'],
    '%': ['11001', '11010', '00100', '01000', '10110', '00110', '00000'],
    '&': ['01100', '10010', '10100', '01000', '10101', '10010', '01101'],
    "'": ['1', '1', '0', '0', '0', '0', '0'],
    '(': ['01', '10', '10', '10', '10', '10', '01'],
    ')': ['10', '01', '01', '01', '01', '01', '10'],
    '*': ['00000', '10101', '01110', '11111', '01110', '10101', '00000'],
    '+': ['000', '010', '010', '111', '010', '010', '000'],
    ',': ['00', '00', '00', '00', '00', '10', '10'],
    '-': ['0000', '0000', '0000', '1111', '0000', '0000', '0000'],
    '.': ['0', '0', '0', '0', '0', '0', '1'],
    '/': ['00001', '00010', '00100', '01000', '10000', '00000', '00000'],
    '0': ['01110', '10001', '10011', '10101', '11001', '10001', '01110'],
    '1': ['00100', '01100', '00100', '00100', '00100', '00100', '01110'],
    '2': ['01110', '10001', '00001', '00010', '00100', '01000', '11111'],
    '3': ['11110', '00001', '00001', '01110', '00001', '00001', '11110'],
    '4': ['00010', '00110', '01010', '10010', '11111', '00010', '00010'],
    '5': ['11111', '10000', '10000', '11110', '00001', '00001', '11110'],
    '6': ['01110', '10000', '10000', '11110', '10001', '10001', '01110'],
    '7': ['11111', '00001', '00010', '00100', '01000', '01000', '01000'],
    '8': ['01110', '10001', '10001', '01110', '10001', '10001', '01110'],
    '9': ['01110', '10001', '10001', '01111', '00001', '00001', '01110'],
    ':': ['0', '1', '0', '0', '0', '1', '0'],
    ';': ['0', '1', '0', '0', '0', '1', '1'],
    '<': ['001', '010', '100', '010', '001', '000', '000'],
    '=': ['0000', '1111', '0000', '1111', '0000', '0000', '0000'],
    '>': ['100', '010', '001', '010', '100', '000', '000'],
    '?': ['01110', '10001', '00001', '00010', '00100', '00000', '00100'],
    '@': ['01110', '10001', '10111', '10101', '10111', '10000', '01110'],
    'A': ['01110', '10001', '10001', '11111', '10001', '10001', '10001'],
    'B': ['11110', '10001', '10001', '11110', '10001', '10001', '11110'],
    'C': ['01111', '10000', '10000', '10000', '10000', '10000', '01111'],
    'D': ['11110', '10001', '10001', '10001', '10001', '10001', '11110'],
    'E': ['11111', '10000', '10000', '11110', '10000', '10000', '11111'],
    'F': ['11111', '10000', '10000', '11110', '10000', '10000', '10000'],
    'G': ['01111', '10000', '10000', '10011', '10001', '10001', '01111'],
    'H': ['10001', '10001', '10001', '11111', '10001', '10001', '10001'],
    'I': ['111', '010', '010', '010', '010', '010', '111'],
    'J': ['00111', '00010', '00010', '00010', '10010', '10010', '01100'],
    'K': ['10001', '10010', '10100', '11000', '10100', '10010', '10001'],
    'L': ['10000', '10000', '10000', '10000', '10000', '10000', '11111'],
    'M': ['10001', '11011', '10101', '10101', '10001', '10001', '10001'],
    'N': ['10001', '11001', '10101', '10011', '10001', '10001', '10001'],
    'O': ['01110', '10001', '10001', '10001', '10001', '10001', '01110'],
    'P': ['11110', '10001', '10001', '11110', '10000', '10000', '10000'],
    'Q': ['01110', '10001', '10001', '10001', '10101', '10010', '01101'],
    'R': ['11110', '10001', '10001', '11110', '10100', '10010', '10001'],
    'S': ['01111', '10000', '10000', '01110', '00001', '00001', '11110'],
    'T': ['11111', '00100', '00100', '00100', '00100', '00100', '00100'],
    'U': ['10001', '10001', '10001', '10001', '10001', '10001', '01110'],
    'V': ['10001', '10001', '10001', '10001', '10001', '01010', '00100'],
    'W': ['10001', '10001', '10001', '10101', '10101', '10101', '01010'],
    'X': ['10001', '10001', '01010', '00100', '01010', '10001', '10001'],
    'Y': ['10001', '10001', '01010', '00100', '00100', '00100', '00100'],
    'Z': ['11111', '00001', '00010', '00100', '01000', '10000', '11111'],
    '[': ['11', '10', '10', '10', '10', '10', '11'],
    '\\': ['10000', '01000', '00100', '00010', '00001', '00000', '00000'],
    ']': ['11', '01', '01', '01', '01', '01', '11'],
    '^': ['00100', '01010', '10001', '00000', '00000', '00000', '00000'],
    '_': ['0000', '0000', '0000', '0000', '0000', '0000', '1111'],
    '`': ['10', '01', '00', '00', '00', '00', '00'],
}

TIME_GLYPHS = {
    '0': ['111', '101', '101', '101', '111'],
    '1': ['010', '110', '010', '010', '111'],
    '2': ['111', '001', '111', '100', '111'],
    '3': ['111', '001', '111', '001', '111'],
    '4': ['101', '101', '111', '001', '001'],
    '5': ['111', '100', '111', '001', '111'],
    '6': ['111', '100', '111', '101', '111'],
    '7': ['111', '001', '010', '010', '010'],
    '8': ['111', '101', '111', '101', '111'],
    '9': ['111', '101', '111', '001', '111'],
    ':': ['0', '1', '0', '1', '0'],
    '/': ['001', '001', '010', '100', '100'],
}


def load_font(size=7):
    try:
        return ImageFont.truetype(FONT_PATH, size)
    except Exception:
        try:
            return ImageFont.load_default(size=size)
        except Exception:
            return ImageFont.load_default()


def load_font_bold(size=7):
    try:
        return ImageFont.truetype(FONT_BOLD_PATH, size)
    except Exception:
        return load_font(size)


def _text_w(text, font):
    try:
        bb = font.getbbox(text)
        return bb[2] - bb[0]
    except Exception:
        return len(text) * 4


def _display_text(text):
    return ''.join(char if char.upper() in TEXT_GLYPHS else '?' for char in text)


def _glyph_width(text, glyphs, spacing=1):
    width = 0
    for char in text.upper():
        glyph = glyphs.get(char, glyphs.get('?'))
        width += len(glyph[0]) + spacing
    return max(0, width - spacing)


def _draw_glyph_text(draw, x, y, text, fill, glyphs, spacing=1):
    cursor = int(x)
    for char in text.upper():
        glyph = glyphs.get(char, glyphs.get('?'))
        for gy, row in enumerate(glyph):
            py = y + gy
            for gx, pixel in enumerate(row):
                px = cursor + gx
                if pixel == '1' and px >= 0 and py >= 0:
                    draw.point((px, py), fill=fill)
        cursor += len(glyph[0]) + spacing


class SpotifyMode(BaseMode):
    def __init__(self, config):
        super().__init__(config)
        self.sp = None
        self.track = None
        self.album_art = None
        self.rotation = 0.0
        self._update_thread = None
        self._lock = threading.Lock()
        self.last_render = time.time()
        self._artist_scroll = 0.0
        self._track_scroll = 0.0
        self._cd_mask = None
        self._rendered_art = None
        self._rendered_art_key = None
        self._last_art_render = 0.0
        self._font = None

    def start(self):
        super().start()
        self._init_spotify()
        self._update_thread = threading.Thread(target=self._update_loop, daemon=True)
        self._update_thread.start()

    def stop(self):
        super().stop()

    def _init_spotify(self):
        if not SPOTIPY_AVAILABLE:
            return
        cfg = self.config.get_section('spotify')
        cid = cfg.get('client_id', '')
        secret = cfg.get('client_secret', '')
        redirect = cfg.get('redirect_uri', 'http://localhost:8080/spotiup')

        if not cid or not secret:
            return
        try:
            auth = SpotifyOAuth(
                client_id=cid,
                client_secret=secret,
                redirect_uri=redirect,
                scope='user-read-currently-playing user-read-playback-state',
                cache_path=os.path.join(os.path.dirname(__file__), '..', '.spotify_token_cache'),
                open_browser=False,
            )
            self.sp = spotipy.Spotify(auth_manager=auth)
        except Exception as e:
            print(f"Spotify init error: {e}")

    def reinit(self):
        self.sp = None
        self._init_spotify()

    def _update_loop(self):
        while self.active:
            try:
                self._fetch()
            except Exception as e:
                print(f"Spotify fetch error: {e}")
            with self._lock:
                track = self.track
            if track and track.get('is_playing'):
                time.sleep(4)    # active playback
            elif track:
                time.sleep(15)   # paused
            else:
                time.sleep(30)   # nothing playing

    def _fetch(self):
        if not self.sp:
            return
        result = self.sp.current_playback()
        if not result:
            with self._lock:
                self.track = None
            return

        item = result.get('item') or {}
        if not item:
            with self._lock:
                self.track = None
            return

        name = item.get('name', '')
        artist = ', '.join(a['name'] for a in item.get('artists', []))
        progress = result.get('progress_ms', 0)
        duration = item.get('duration_ms', 1)
        is_playing = result.get('is_playing', False)

        images = item.get('album', {}).get('images', [])
        art_url = images[-1]['url'] if images else None

        old_url = (self.track or {}).get('art_url')
        if art_url and art_url != old_url:
            self._load_art(art_url)

        with self._lock:
            self.track = {
                'name': name,
                'artist': artist,
                'progress': progress,
                'duration': duration,
                'is_playing': is_playing,
                'art_url': art_url,
            }

    def _load_art(self, url):
        try:
            r = requests.get(url, timeout=5)
            r.raise_for_status()
            art = Image.open(io.BytesIO(r.content)).convert('RGB')
            art = art.resize((ART_SIZE, ART_SIZE), Image.LANCZOS)
            with self._lock:
                self.album_art = art
        except Exception as e:
            print(f"Album art error: {e}")

    # ── CD mask ──────────────────────────────────────────────────────────────

    def _get_cd_mask(self):
        if self._cd_mask is None:
            mask = Image.new('L', (ART_SIZE, ART_SIZE), 0)
            d = ImageDraw.Draw(mask)
            d.ellipse([1, 1, ART_SIZE - 2, ART_SIZE - 2], fill=255)
            center = ART_SIZE // 2
            d.ellipse([center - 2, center - 2, center + 2, center + 2], fill=0)
            self._cd_mask = mask
        return self._cd_mask

    def _apply_cd_mask(self, art):
        result = Image.new('RGB', (ART_SIZE, ART_SIZE), (0, 0, 0))
        result.paste(art, mask=self._get_cd_mask())
        center = ART_SIZE // 2
        ImageDraw.Draw(result).ellipse([center - 3, center - 3, center + 3, center + 3],
                                       outline=(55, 55, 55))
        return result

    # ── Scrolling ─────────────────────────────────────────────────────────────

    @staticmethod
    def _advance_scroll(offset, text_w, panel_w, elapsed):
        if text_w <= panel_w:
            return 0.0
        return (offset + SCROLL_SPEED * elapsed) % (text_w + SCROLL_GAP)

    @staticmethod
    def _draw_scrolling(panel, y, text, text_w, offset, fill):
        d = ImageDraw.Draw(panel)
        px = -int(offset)
        _draw_glyph_text(d, px, y, text, fill, TEXT_GLYPHS)
        if text_w > PANEL_W:
            _draw_glyph_text(d, px + text_w + SCROLL_GAP, y, text, fill, TEXT_GLYPHS)

    # ── Formatting ────────────────────────────────────────────────────────────

    @staticmethod
    def _fmt(ms):
        s = ms // 1000
        return f"{s // 60}:{s % 60:02d}"

    # ── Render ────────────────────────────────────────────────────────────────

    def render(self, canvas):
        now = time.time()
        elapsed = now - self.last_render
        self.last_render = now

        img = Image.new('RGB', (64, 32), (0, 0, 0))
        draw = ImageDraw.Draw(img)

        with self._lock:
            track = self.track
            art = self.album_art

        if not track:
            if self._font is None:
                self._font = load_font(7)
            msg = "No Spotify" if SPOTIPY_AVAILABLE else "Install spotipy"
            mask = Image.new('L', img.size, 0)
            ImageDraw.Draw(mask).text((2, 12), msg, fill=255, font=self._font)
            img.paste((80, 80, 80), mask=mask)
            canvas.SetImage(img)
            return

        # --- Left 32px: rotating CD ---
        art_y = (32 - ART_SIZE) // 2
        if art:
            speed_deg = 20 if track.get('is_playing') else 0
            self.rotation = (self.rotation + speed_deg * elapsed) % 360
            art_key = (id(art), int(self.rotation / 3) if speed_deg else 0)
            if (self._rendered_art is None or art_key != self._rendered_art_key or
                    now - self._last_art_render >= 0.12):
                rotated = art.rotate(-self.rotation, resample=Image.BILINEAR)
                self._rendered_art = self._apply_cd_mask(rotated)
                self._rendered_art_key = art_key
                self._last_art_render = now
            img.paste(self._rendered_art, (0, art_y))
        else:
            cx, cy = ART_SIZE // 2, 16
            draw.ellipse([cx-10, cy-10, cx+10, cy+10], outline=(60, 60, 60))
            draw.ellipse([cx-2, cy-2, cx+2, cy+2], outline=(60, 60, 60))

        # --- Right 31px panel (x=33..63) ---
        panel = Image.new('RGB', (PANEL_W, 32), (0, 0, 0))
        pdraw = ImageDraw.Draw(panel)

        artist = _display_text(track['artist'])
        name = _display_text(track['name'])
        artist_w = _glyph_width(artist, TEXT_GLYPHS)
        track_w = _glyph_width(name, TEXT_GLYPHS)

        self._artist_scroll = self._advance_scroll(self._artist_scroll, artist_w, PANEL_W, elapsed)
        self._track_scroll = self._advance_scroll(self._track_scroll, track_w, PANEL_W, elapsed)

        # Artist (y=1)
        self._draw_scrolling(panel, 1, artist, artist_w, self._artist_scroll,
                             (170, 220, 255))
        # Track name (y=10)
        self._draw_scrolling(panel, 10, name, track_w, self._track_scroll,
                             (255, 255, 255))

        # Progress bar (y=21, 2px tall)
        progress_ratio = track['progress'] / max(track['duration'], 1)
        pdraw.rectangle([0, 20, PANEL_W - 1, 21], fill=(40, 40, 40))
        fill_w = int((PANEL_W - 1) * progress_ratio)
        if fill_w > 0:
            pdraw.rectangle([0, 20, fill_w, 21], fill=(30, 215, 96))

        # Time string (y=25) — mode '1' forces PIL into binary pixel rendering, no anti-aliasing
        time_str = f"{self._fmt(track['progress'])}/{self._fmt(track['duration'])}"
        time_w = _glyph_width(time_str, TIME_GLYPHS)
        _draw_glyph_text(pdraw, max(0, (PANEL_W - time_w) // 2), 25, time_str,
                         (210, 210, 210), TIME_GLYPHS)

        img.paste(panel, (PANEL_X, 0))
        canvas.SetImage(img)
