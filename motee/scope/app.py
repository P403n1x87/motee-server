from base64 import b64encode
from io import BytesIO

from ewmh import EWMH
from motee.scope import ScopeHandler
from PIL import Image, ImageDraw, ImageFont
from Xlib import Xatom

_EWMH = EWMH()


def generate_icon(name):
    image = Image.new("RGBA", (64, 64), color=(70, 168, 231))
    d = ImageDraw.Draw(image)
    font = ImageFont.truetype("/usr/share/fonts/truetype/ubuntu/UbuntuMono-R.ttf", 24)
    d.text((10, 16), name[:4].upper(), font=font, fill=(192, 192, 255))
    return image


class App:

    ICON_SIZE = 64
    _icon_cache = {}

    def __init__(self, win):
        self.win = win
        self._icon = False

    @property
    def _key(self):
        return (self.name, self.pid)

    @property
    def name(self):
        name = _EWMH.getWmName(self.win)
        return name and name.decode() or self.win.get_wm_name()

    @property
    def pid(self):
        try:
            return _EWMH.getWmPid(self.win)
        except TypeError:
            pass

    @property
    def wid(self):
        return self.win.id

    def _setter(self, method, *args, **kwargs):
        method(*args, **kwargs)
        _EWMH.display.flush()

    @property
    def icon(self):
        key = self._key
        try:
            return self._icon_cache[key]
        except KeyError:
            icon_data = self.win.get_full_property(
                _EWMH.display.get_atom("_NET_WM_ICON"), Xatom.CARDINAL
            )
            if icon_data:
                w, h, *data = icon_data.value

                def argb_to_rgba(b):
                    return (b[2], b[1], b[0], b[3])

                array = bytes(
                    b for _ in data for b in argb_to_rgba(_.to_bytes(4, "little"))
                )
                image = Image.frombytes("RGBA", (w, h), array)
            else:
                image = generate_icon(self.name)

            buffer = BytesIO()
            image.save(buffer, format="PNG")
            icon = self._icon_cache[key] = buffer.getvalue()
            return icon

    def activate(self):
        self._setter(_EWMH.setActiveWindow, self.win)

    def set_fullscreen(self, state=True):
        self._setter(
            _EWMH.setWmState, self.win, state and 1 or 0, "_NET_WM_STATE_FULLSCREEN"
        )

    def toggle_fullscreen(self):
        self.set_fullscreen(
            "_NET_WM_STATE_FULLSCREEN" not in _EWMH.getWmState(self.win, True)
        )

    def close(self):
        self._setter(_EWMH.setCloseWindow, self.win)


def active_app():
    return App(_EWMH.getActiveWindow())


def app(wid):
    return App(_EWMH.display.create_resource_object("window", wid))


def apps():
    for w in _EWMH.getClientList():
        try:
            app = App(w)
            if app.name or _EWMH.getWmWindowType(w)[0] == 348:
                yield App(w)
        except TypeError:
            pass
        except IndexError:
            app = App(w)
            if app.icon is not None:
                yield app


class AppHandler(ScopeHandler):
    __scope__ = "app"

    @staticmethod
    def list():
        return {
            _.name: {"wid": _.wid, "icon": b64encode(_.icon or b"").decode()}
            for _ in apps()
            # if _.icon is not None
        }

    def activate(wid):
        aapp = active_app()
        if aapp.wid == wid:
            aapp.toggle_fullscreen()
        else:
            app(wid).activate()
        return True

    def close():
        active_app().close()
        return True
