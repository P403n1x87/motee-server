from Xlib import X
from Xlib.display import Display
from Xlib.ext.xtest import fake_input
import Xlib.XK

d = Display()
Xlib.XK.load_keysym_group("xf86")


def _keycode(name):
    keysym_num = Xlib.XK.string_to_keysym(name)
    if keysym_num == Xlib.XK.NoSymbol:
        raise ValueError(name)
    keycode = d.keysym_to_keycode(keysym_num)
    if not keycode:
        raise RuntimeError(f'Unable to map key "{name}" to a keycode')
    return keycode


VOLUME_UP = _keycode("XF86_AudioRaiseVolume")
VOLUME_DOWN = _keycode("XF86_AudioLowerVolume")

fake_input(d, X.KeyPress, VOLUME_UP)
d.sync()
fake_input(d, X.KeyRelease, VOLUME_UP)
d.sync()
