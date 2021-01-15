from .plain import Plain
from .tcpssl import TcpSsl

__all__ = [
    'PlainTcpSsl',
]


class PlainTcpSsl(Plain, TcpSsl):
    pass
