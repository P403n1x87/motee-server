import dbus

DBUS_MPRIS = "org.mpris.MediaPlayer2"
BUS = dbus.SessionBus()


class Player:
    MPRIS_INTERFACE = "org.mpris.MediaPlayer2"
    PLAYER_INTERFACE = "org.mpris.MediaPlayer2.Player"
    PROPERTY_INTERFACE = "org.freedesktop.DBus.Properties"

    def __init__(self, service):
        self.proxy = BUS.get_object(service, "/org/mpris/MediaPlayer2")

        self.service = service
        self.name = service[len(DBUS_MPRIS) + 1 :]
        self.interface = dbus.Interface(
            self.proxy,
            dbus_interface=self.PLAYER_INTERFACE,
        )
        self.properties = dbus.Interface(
            self.proxy, dbus_interface=self.PROPERTY_INTERFACE
        )
        self.base = dbus.Interface(self.proxy, dbus_interface=self.MPRIS_INTERFACE)

    def _get_property(self, name):
        try:
            return self.properties.Get(
                self.PLAYER_INTERFACE, name, self.PROPERTY_INTERFACE
            )
        except TypeError:
            return self.properties.Get(self.PLAYER_INTERFACE, name)

    def _get_base_property(self, name):
        return self.properties.Get(self.MPRIS_INTERFACE, name, self.PROPERTY_INTERFACE)

    def _set_base_property(self, name, value):
        return self.properties.Set(
            self.MPRIS_INTERFACE, name, value, self.PROPERTY_INTERFACE
        )

    @property
    def status(self):
        return self._get_property("PlaybackStatus")

    @property
    def metadata(self):
        metadata = self._get_property("Metadata")
        return {k.partition(":")[2]: v for k, v in metadata.items()}

    def set_fullscreen(self, state=True):
        return self._set_base_property("Fullscreen", state)

    def play(self):
        return self.interface.Play()

    def pause(self):
        return self.interface.Pause()

    def stop(self):
        return self.interface.Stop()

    def play_pause(self):
        return self.interface.PlayPause()

    def next(self):
        return self.interface.Next()

    def previous(self):
        return self.interface.Previous()

    def get_properties(self):
        return self.properties.GetAll(self.PLAYER_INTERFACE)

    def get_base_properties(self):
        return self.properties.GetAll(self.MPRIS_INTERFACE)


def get_player(name):
    return Player(DBUS_MPRIS + "." + name)


def players():
    return (Player(_) for _ in BUS.list_names() if _.startswith(DBUS_MPRIS))
