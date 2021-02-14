import os
import subprocess

from motee.net import get_address, get_mac, hostname, PORT
from motee.scope import ScopeHandler
from pynput.mouse import Button, Controller as MouseController
from pynput.keyboard import Key, Controller as KeyboardController
from Xlib import X
from Xlib.display import Display
from Xlib.ext.xtest import fake_input
import Xlib.XK

KEYBOARD = KeyboardController()
MOUSE = MouseController()

DISPLAY = Display()
Xlib.XK.load_keysym_group("xf86")


def _keycode(name):
    keysym_num = Xlib.XK.string_to_keysym(name)
    if keysym_num == Xlib.XK.NoSymbol:
        raise ValueError(name)
    keycode = DISPLAY.keysym_to_keycode(keysym_num)
    if not keycode:
        raise RuntimeError(f'Unable to map key "{name}" to a keycode')
    return keycode


VOLUME_UP = _keycode("XF86_AudioRaiseVolume")
VOLUME_DOWN = _keycode("XF86_AudioLowerVolume")
MUTE = _keycode("XF86_AudioMute")


class Device:
    def launch(self, command):
        return subprocess.Popen([command], start_new_session=True)

    def shutdown(self):
        os.system("systemctl poweroff -i")

    def reboot(self):
        os.system("systemctl reboot -i")

    def move_cursor(self, dx, dy):
        MOUSE.move(dx, dy)

    def _key_event(self, event, key):
        fake_input(DISPLAY, event, key)
        DISPLAY.sync()

    def _key_press(self, key):
        self._key_event(X.KeyPress, key)

    def _key_release(self, key):
        self._key_event(X.KeyRelease, key)

    def _keystroke(self, key):
        self._key_press(key)
        self._key_release(key)

    def keystroke(self, key):
        KEYBOARD.press(key)
        KEYBOARD.release(key)

    def lclick(self):
        MOUSE.press(Button.left)
        MOUSE.release(Button.left)

    def rclick(self):
        MOUSE.press(Button.right)
        MOUSE.release(Button.right)

    def mute(self):
        self._keystroke(MUTE)

    def scroll_down(self):
        MOUSE.scroll(0, -4)

    def scroll_up(self):
        MOUSE.scroll(0, 4)

    def zoom_in(self):
        KEYBOARD.press(Key.ctrl)
        self.scroll_up()
        KEYBOARD.release(Key.ctrl)

    def zoom_out(self):
        KEYBOARD.press(Key.ctrl)
        self.scroll_down()
        KEYBOARD.release(Key.ctrl)

    def volume_up(self):
        self._keystroke(VOLUME_UP)

    def volume_down(self):
        self._keystroke(VOLUME_DOWN)


class DeviceHandler(ScopeHandler):
    def discover():
        inet = get_address()
        mac = get_mac(inet)
        return {"host": hostname(), "inet": inet, "port": PORT, "mac": mac}

    def volume(direction):
        getattr(Device(), f"volume_{direction}")()
        return True

    def mute():
        Device().mute()
        return True

    def cursor(dx, dy):
        Device().move_cursor(dx, dy)
        return True

    def click(button):
        getattr(Device(), f"{button}click")()
        return True

    def keystroke(unicode):
        Device().keystroke(chr(unicode))
        return True

    def poweroff():
        Device().shutdown()
        return True

    def reboot():
        Device().reboot()
        return True

    def launch(command):
        Device().launch(command)
        return True

    def scroll(direction):
        getattr(Device(), f"scroll_{direction}")()
        return True

    def zoom(direction):
        getattr(Device(), f"zoom_{direction}")()
        return True
