from .gzip import Gzip
from .tcpssl import TcpSsl

__all__ = [
    'GzipTcpSsl',
]


class GzipTcpSsl(Gzip, TcpSsl):
    pass
