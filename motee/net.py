import psutil
import socket
from typing import Iterator


class NIC:
    def __init__(self, name, addrs):
        self.name = name
        self.addrs = {_.family: _.address for _ in addrs}

    @property
    def mac(self):
        return self.addrs[socket.AF_PACKET]

    @property
    def ip(self):
        return self.addrs.get(socket.AF_INET, None)

    @property
    def ip6(self):
        return self.addrs.get(socket.AF_INET6, None)

    @property
    def connected(self):
        return self.ip is not None


def hostname():
    return socket.gethostname()


def nics() -> Iterator[NIC]:
    return (NIC(n, addrs) for n, addrs in psutil.net_if_addrs().items() if n != "lo")
