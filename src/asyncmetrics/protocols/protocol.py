from asyncio import StreamWriter
from typing import Iterable, Tuple

from .protocolerror import ProtocolError

__all__ = [
    'Protocol',
]


class Protocol:
    def __init__(self, host: str = '127.0.0.1', port: int = 2003):
        self._host = host
        self._port = port
        self._writer = None

    async def send(self, dataset: Iterable[Tuple[str, int, int]]):
        try:
            if not self._writer:
                self._writer = await self._connect()

            data = self._encode(dataset)
            self._writer.write(data)
            await self._writer.drain()
        except Exception as exc:
            raise ProtocolError(*exc.args) from exc

    def close(self):
        if self._writer:
            self._writer.close()

    async def _connect(self) -> StreamWriter:
        raise NotImplementedError

    def _encode(self, dataset: Iterable[Tuple[str, int, int]]) -> bytes:
        raise NotImplementedError