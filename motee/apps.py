from ewmh import EWMH
from io import BytesIO
from PIL import Image
from Xlib import Xatom


_EWMH = EWMH()


class App:

    ICON_SIZE = 64

    def __init__(self, win):
        self.win = win
        self._icon = False

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
        if self._icon is False:
            self._icon = None
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
                buffer = BytesIO()
                Image.frombytes("RGBA", (w, h), array).save(buffer, format="PNG")
                self._icon = buffer.getvalue()

        return self._icon

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


if __name__ == "__main__":
    for app in apps():
        print(app.name, app.pid)
