from .plain import Plain
from .udp import Udp

__all__ = [
    'PlainUdp',
]


class PlainUdp(Plain, Udp):
    pass
