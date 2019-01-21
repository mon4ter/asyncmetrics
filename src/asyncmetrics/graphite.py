from asyncio import Queue, get_event_loop
from time import time
from typing import Optional

from aiographite import AIOGraphite, connect

__all__ = [
    'Graphite',
    'get_graphite',
    'setup',
]

_graphite = None


class Graphite:
    def __init__(self, conn: AIOGraphite):
        self._conn = conn
        self._queue = Queue()
        self._sender_task = get_event_loop().create_task(self._sender())
        self._running = True

    async def _sender(self):
        queue = self._queue

        while True:
            metrics = [await queue.get()]

            while not queue.empty():
                metrics.append(queue.get_nowait())

            await self._conn.send_multiple(metrics)

            if not self._running:
                break

    async def close(self):
        self._running = False
        await self._sender_task
        await self._conn.close()

    def send(self, metric: str, value: int, timestamp: Optional[int] = None):
        if timestamp is None:
            timestamp = int(time())

        self._queue.put_nowait((metric, value, timestamp))


async def setup(*args, **kwargs) -> Graphite:
    global _graphite

    if _graphite is not None:
        raise RuntimeError("asyncmetrics must be set up only once")

    conn = await connect(*args, **kwargs)
    _graphite = Graphite(conn)
    return _graphite


def get_graphite() -> Graphite:
    if _graphite is None:
        raise RuntimeError("asyncmetrics must be set up before sending metrics")

    return _graphite
