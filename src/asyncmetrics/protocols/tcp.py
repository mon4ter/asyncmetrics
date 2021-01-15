from asyncio import StreamWriter, open_connection

from .protocol import Protocol

__all__ = [
    'Tcp',
]


# noinspection PyAbstractClass
class Tcp(Protocol):
    async def _connect(self) -> StreamWriter:
        _, writer = await open_connection(self._host, self._port)
        return writer
