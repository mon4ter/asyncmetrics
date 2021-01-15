from .plain import Plain
from .tcp import Tcp

__all__ = [
    'PlainTcp'
]


class PlainTcp(Plain, Tcp):
    pass
