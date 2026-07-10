"""
REST API + Web UI for LED Matrix Controller.
All endpoints return JSON. Web UI served at /.
"""

import io
import os
import threading
from flask import Flask, abort, jsonify, request, render_template
from PIL import Image as _PILImage

try:
    import spotipy
    from spotipy.oauth2 import SpotifyOAuth
    SPOTIPY_AVAILABLE = True
except ImportError:
    SPOTIPY_AVAILABLE = False

_IMAGE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
IMAGE_PNG = os.path.join(_IMAGE_DIR, 'matrix_image.png')
IMAGE_GIF = os.path.join(_IMAGE_DIR, 'matrix_image.gif')

SPOTIFY_CACHE_PATH = os.environ.get(
    'SPOTIFY_CACHE_PATH',
    os.path.join(os.path.dirname(__file__), '.spotify_token_cache'),
)


def create_app(get_controller_fn):
    app = Flask(
        __name__,
        template_folder=os.path.join(os.path.dirname(__file__), 'templates'),
        static_folder=os.path.join(os.path.dirname(__file__), 'static'),
    )

    def ctrl():
        return get_controller_fn()

    def spotify_callback_path(cfg):
        path = str(cfg.get('callback_path', '/callback') or '/callback').strip()
        if not path.startswith('/'):
            path = '/' + path
        return '/' + path.strip('/')

    def spotify_redirect_uri(cfg):
        redirect = str(cfg.get('redirect_uri', '') or '').strip()
        if redirect:
            return redirect
        return request.host_url.rstrip('/') + spotify_callback_path(cfg)

    # ── Web UI ────────────────────────────────────────────────────────────────

    @app.route('/')
    def index():
        return render_template('index.html')

    # ── Status ────────────────────────────────────────────────────────────────

    @app.route('/api/status')
    def status():
        c = ctrl()
        if not c:
            return jsonify(error='controller not ready'), 503
        return jsonify(
            mode=c.get_mode(),
            modes=c.get_mode_names(),
            brightness=c.config.get('brightness', 50),
            screen_on=c.get_screen(),
            night_mode_active=c.night_mode_active(),
            config=c.config.get_all(),
        )

    @app.route('/api/screen', methods=['GET', 'POST'])
    def screen():
        c = ctrl()
        if not c:
            return jsonify(error='controller not ready'), 503
        if request.method == 'GET':
            return jsonify(screen_on=c.get_screen())
        data = request.get_json(force=True, silent=True) or {}
        c.set_screen(bool(data.get('on', True)))
        return jsonify(screen_on=c.get_screen(), status='ok')

    # ── Mode ─────────────────────────────────────────────────────────────────

    @app.route('/api/mode', methods=['GET', 'POST'])
    def mode():
        c = ctrl()
        if not c:
            return jsonify(error='controller not ready'), 503

        if request.method == 'GET':
            return jsonify(mode=c.get_mode(), modes=c.get_mode_names())

        data = request.get_json(force=True, silent=True) or {}
        name = data.get('mode', '').strip()
        if not name:
            return jsonify(error='mode field required'), 400

        ok = c.set_mode(name)
        if not ok:
            return jsonify(error=f'unknown mode: {name}'), 400
        return jsonify(mode=name, status='ok')

    # ── Brightness ────────────────────────────────────────────────────────────

    @app.route('/api/brightness', methods=['POST'])
    def brightness():
        c = ctrl()
        if not c:
            return jsonify(error='controller not ready'), 503
        data = request.get_json(force=True, silent=True) or {}
        value = int(data.get('value', 50))
        c.set_brightness(value)
        return jsonify(brightness=c.config.get('brightness'), status='ok')

    # ── Text ──────────────────────────────────────────────────────────────────

    @app.route('/api/text', methods=['GET', 'POST'])
    def text():
        c = ctrl()
        if not c:
            return jsonify(error='controller not ready'), 503

        if request.method == 'GET':
            return jsonify(c.config.get_section('text'))

        data = request.get_json(force=True, silent=True) or {}
        c.config.set_section('text', data)
        # Switch to text mode automatically
        if c.get_mode() != 'text':
            c.set_mode('text')
        return jsonify(status='ok', config=c.config.get_section('text'))

    # ── Generic section config ────────────────────────────────────────────────

    @app.route('/api/config/<section>', methods=['GET', 'POST'])
    def config_section(section):
        c = ctrl()
        if not c:
            return jsonify(error='controller not ready'), 503

        allowed = {'clock', 'spotify', 'gameoflife', 'text', 'patternflow', 'matrix', 'carousel', 'draw', 'pomodoro', 'reminders', 'night_mode'}
        if section not in allowed:
            return jsonify(error=f'unknown section: {section}'), 400

        if request.method == 'GET':
            return jsonify(c.config.get_section(section))

        data = request.get_json(force=True, silent=True) or {}
        c.config.set_section(section, data)

        # Reinit Spotify only when OAuth settings change.
        if section == 'spotify' and any(
            key in data for key in ('client_id', 'client_secret', 'redirect_uri', 'callback_path')
        ):
            spotify_mode = c.modes.get('spotify')
            if spotify_mode:
                spotify_mode.reinit()

        if section == 'night_mode':
            c.refresh_brightness()

        return jsonify(status='ok', config=c.config.get_section(section))

    @app.route('/api/draw', methods=['GET', 'POST'])
    def draw():
        c = ctrl()
        if not c:
            return jsonify(error='controller not ready'), 503

        if request.method == 'GET':
            return jsonify(c.config.get_section('draw'))

        data = request.get_json(force=True, silent=True) or {}
        c.config.set_section('draw', data)
        if c.get_mode() != 'draw':
            c.set_mode('draw')
        return jsonify(status='ok', config=c.config.get_section('draw'))

    # ── Image ─────────────────────────────────────────────────────────────────

    @app.route('/api/image', methods=['GET', 'DELETE'])
    def image_endpoint():
        if request.method == 'GET':
            has_gif = os.path.exists(IMAGE_GIF)
            has_png = os.path.exists(IMAGE_PNG)
            return jsonify(has_image=has_gif or has_png, is_gif=has_gif)
        # DELETE — remove both files and return to clock
        try:
            for path in (IMAGE_PNG, IMAGE_GIF):
                if os.path.exists(path):
                    os.remove(path)
        except Exception as e:
            return jsonify(error=str(e)), 500
        c = ctrl()
        if c and c.get_mode() == 'image':
            c.set_mode('clock')
        return jsonify(status='ok')

    @app.route('/api/image/upload', methods=['POST'])
    def image_upload():
        if 'file' not in request.files:
            return jsonify(error='no file provided'), 400
        f = request.files['file']
        if not f.filename:
            return jsonify(error='empty filename'), 400

        is_gif = (f.content_type or '').lower() == 'image/gif' or f.filename.lower().endswith('.gif')

        try:
            raw = f.read()
            if is_gif:
                ox = int(float(request.form.get('ox', 0)))
                oy = int(float(request.form.get('oy', 0)))
                cw = int(float(request.form.get('cropW', -1)))
                ch = int(float(request.form.get('cropH', -1)))
                src = _PILImage.open(io.BytesIO(raw))
                n = getattr(src, 'n_frames', 1)
                frames, durations = [], []
                for i in range(n):
                    src.seek(i)
                    frame = src.convert('RGBA')
                    fw, fh = frame.size
                    if cw > 0 and ch > 0:
                        left = max(0, min(ox, fw - 1))
                        top = max(0, min(oy, fh - 1))
                        right = min(fw, left + cw)
                        bottom = min(fh, top + ch)
                        frame = frame.crop((left, top, right, bottom))
                    frame = frame.resize((64, 32), _PILImage.LANCZOS).convert('RGB')
                    frames.append(frame)
                    ms = max(20, src.info.get('duration', 100))
                    durations.append(ms)
                # Remove old files before saving
                for p in (IMAGE_PNG, IMAGE_GIF):
                    if os.path.exists(p):
                        os.remove(p)
                frames[0].save(
                    IMAGE_GIF, format='GIF', save_all=True,
                    append_images=frames[1:], loop=0,
                    duration=durations, optimize=False,
                )
            else:
                img = _PILImage.open(io.BytesIO(raw)).convert('RGB')
                if img.size != (64, 32):
                    img = img.resize((64, 32), _PILImage.LANCZOS)
                for p in (IMAGE_PNG, IMAGE_GIF):
                    if os.path.exists(p):
                        os.remove(p)
                img.save(IMAGE_PNG, 'PNG')
        except Exception as e:
            return jsonify(error=str(e)), 400

        c = ctrl()
        if c:
            image_mode = c.modes.get('image')
            if image_mode:
                image_mode._last_check = 0.0
            if c.get_mode() != 'image':
                c.set_mode('image')
        return jsonify(status='ok')

    @app.route('/api/pomodoro', methods=['GET', 'POST'])
    def pomodoro():
        c = ctrl()
        if not c:
            return jsonify(error='controller not ready'), 503

        mode = c.modes.get('pomodoro')
        if not mode:
            return jsonify(error='pomodoro mode not loaded'), 404

        if request.method == 'GET':
            return jsonify(config=c.config.get_section('pomodoro'))

        data = request.get_json(force=True, silent=True) or {}
        required = ('event', 'state')
        missing = [key for key in required if key not in data]
        if missing:
            return jsonify(error=f'missing fields: {", ".join(missing)}'), 400

        try:
            timer_state = mode.update_timer(data)
        except (TypeError, ValueError) as e:
            return jsonify(error=str(e)), 400

        should_show_pomodoro = timer_state != 'elapsed_ignored'
        if should_show_pomodoro and c.get_mode() != 'pomodoro':
            c.set_mode('pomodoro')
        active = timer_state not in ('stopped', 'elapsed_ignored')
        return jsonify(status='ok', mode='pomodoro', active=active, timer_state=timer_state)

    # ── Spotify OAuth ─────────────────────────────────────────────────────────

    @app.route('/api/spotify/auth_url')
    def spotify_auth_url():
        c = ctrl()
        if not c:
            return jsonify(error='controller not ready'), 503
        if not SPOTIPY_AVAILABLE:
            return jsonify(error='spotipy not installed'), 500

        cfg = c.config.get_section('spotify')
        cid = cfg.get('client_id', '')
        secret = cfg.get('client_secret', '')
        redirect = spotify_redirect_uri(cfg)

        if not cid or not secret:
            return jsonify(error='spotify client_id/secret not configured'), 400

        try:
            if not cfg.get('redirect_uri'):
                c.config.set_section('spotify', {'redirect_uri': redirect})
                cfg = c.config.get_section('spotify')
            auth = SpotifyOAuth(
                client_id=cid,
                client_secret=secret,
                redirect_uri=redirect,
                scope='user-read-currently-playing user-read-playback-state',
                cache_path=SPOTIFY_CACHE_PATH,
                open_browser=False,
            )
            url = auth.get_authorize_url()
            return jsonify(url=url)
        except Exception as e:
            return jsonify(error=str(e)), 500

    def handle_spotify_callback():
        code = request.args.get('code')
        if not code:
            return 'Missing code parameter', 400

        c = ctrl()
        if not c:
            return 'Controller not ready', 503

        cfg = c.config.get_section('spotify')
        redirect = spotify_redirect_uri(cfg)
        try:
            if not cfg.get('redirect_uri'):
                c.config.set_section('spotify', {'redirect_uri': redirect})
                cfg = c.config.get_section('spotify')
            auth = SpotifyOAuth(
                client_id=cfg.get('client_id', ''),
                client_secret=cfg.get('client_secret', ''),
                redirect_uri=redirect,
                scope='user-read-currently-playing user-read-playback-state',
                cache_path=SPOTIFY_CACHE_PATH,
                open_browser=False,
            )
            auth.get_access_token(code, as_dict=False)
            spotify_mode = c.modes.get('spotify')
            if spotify_mode:
                spotify_mode.reinit()
            return '<h2>Spotify connected!</h2><p>You can close this tab.</p>'
        except Exception as e:
            return f'Error: {e}', 500

    @app.route('/callback')
    @app.route('/spotiup')
    def spotify_callback():
        return handle_spotify_callback()

    # ── Patternflow ───────────────────────────────────────────────────────────

    @app.route('/api/patternflow/patterns')
    def pf_patterns():
        c = ctrl()
        if not c:
            return jsonify(error='controller not ready'), 503
        pf = c.modes.get('patternflow')
        if not pf:
            return jsonify(error='patternflow mode not loaded'), 404
        current = pf.get_current_pattern()
        return jsonify(patterns=pf.get_pattern_names(), **current)

    @app.route('/api/patternflow/pattern', methods=['POST'])
    def pf_set_pattern():
        c = ctrl()
        if not c:
            return jsonify(error='controller not ready'), 503
        pf = c.modes.get('patternflow')
        if not pf:
            return jsonify(error='patternflow mode not loaded'), 404

        data = request.get_json(force=True, silent=True) or {}
        if 'index' in data:
            idx = int(data['index'])
        elif 'name' in data:
            names = pf.get_pattern_names()
            name = data['name'].strip()
            if name not in names:
                return jsonify(error=f'unknown pattern: {name}'), 400
            idx = names.index(name)
        else:
            return jsonify(error='index or name required'), 400

        pf.set_pattern(idx)
        if c.get_mode() != 'patternflow':
            c.set_mode('patternflow')
        return jsonify(status='ok', **pf.get_current_pattern())

    @app.route('/api/patternflow/knob', methods=['POST'])
    def pf_knob():
        c = ctrl()
        if not c:
            return jsonify(error='controller not ready'), 503
        pf = c.modes.get('patternflow')
        if not pf:
            return jsonify(error='patternflow mode not loaded'), 404
        data = request.get_json(force=True, silent=True) or {}
        knob  = int(data.get('knob', 0))
        delta = int(data.get('delta', 0))
        if not (0 <= knob <= 3):
            return jsonify(error='knob must be 0-3'), 400
        pf.web_knob(knob, delta)
        return jsonify(status='ok')

    @app.route('/api/patternflow/button', methods=['POST'])
    def pf_button():
        c = ctrl()
        if not c:
            return jsonify(error='controller not ready'), 503
        pf = c.modes.get('patternflow')
        if not pf:
            return jsonify(error='patternflow mode not loaded'), 404
        data = request.get_json(force=True, silent=True) or {}
        button = int(data.get('button', data.get('knob', 0)))
        if not (0 <= button <= 5):
            return jsonify(error='button must be 0-5'), 400
        pf.web_button(button)
        return jsonify(status='ok')

    # ── Shutdown ──────────────────────────────────────────────────────────────

    @app.route('/api/patternflow/options', methods=['POST'])
    def pf_options():
        c = ctrl()
        if not c:
            return jsonify(error='controller not ready'), 503
        pf = c.modes.get('patternflow')
        if not pf:
            return jsonify(error='patternflow mode not loaded'), 404
        data = request.get_json(force=True, silent=True) or {}
        pf.set_options(
            show_fps=data.get('show_fps') if 'show_fps' in data else None,
            donut_fast_render=data.get('donut_fast_render') if 'donut_fast_render' in data else None,
            fast_image_push=data.get('fast_image_push') if 'fast_image_push' in data else None,
        )
        return jsonify(status='ok', **pf.get_current_pattern())

    @app.route('/api/shutdown', methods=['POST'])
    def shutdown():
        c = ctrl()
        if c:
            t = threading.Thread(target=c.trigger_shutdown, daemon=True)
            t.start()
        return jsonify(status='shutting down')

    # ── Restart (restart the service, not the Pi) ─────────────────────────────

    @app.route('/api/restart', methods=['POST'])
    def restart():
        os.system("sudo systemctl restart led-matrix")
        return jsonify(status='restarting')

    @app.route('/api/service/stop', methods=['POST'])
    def stop_service():
        def _stop():
            os.system("systemctl stop led-matrix")

        threading.Timer(0.5, _stop).start()
        return jsonify(status='stopping')

    @app.route('/api/service/disable', methods=['POST'])
    def disable_service():
        os.system("systemctl disable led-matrix")
        return jsonify(status='autostart disabled')

    @app.route('/<path:path>')
    def configured_spotify_callback(path):
        c = ctrl()
        if not c:
            abort(404)
        configured_path = spotify_callback_path(c.config.get_section('spotify')).strip('/')
        if path.strip('/') != configured_path:
            abort(404)
        return handle_spotify_callback()

    return app
