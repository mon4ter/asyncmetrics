from .gzip import Gzip
from .tcp import Tcp

__all__ = [
    'GzipTcp',
]


class GzipTcp(Gzip, Tcp):
    pass
