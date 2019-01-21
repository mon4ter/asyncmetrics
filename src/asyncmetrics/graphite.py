from asyncio import CancelledError, LifoQueue, sleep
from logging import getLogger
from time import time
from typing import Optional

from aiographite.aiographite import AIOGraphite, AioGraphiteSendException, connect

__all__ = [
    'Graphite',
    'get_graphite',
    'setup',
]

_graphite = None

logger = getLogger(__package__)


class Graphite:
    def __init__(self, conn: AIOGraphite):
        self._conn = conn
        self._queue = LifoQueue()
        self._sender_task = conn.loop.create_task(self._sender())
        self._running = True

    async def _sender(self):
        queue = self._queue
        fail = None

        while self._running:
            try:
                if fail:
                    logger.error("%s Sleeping for 60 seconds.", fail)
                    await sleep(60)

                metrics = [await queue.get()]
            except CancelledError:
                metrics = []

            while not queue.empty():
                metrics.append(queue.get_nowait())

            try:
                await self._conn.send_multiple(metrics)
            except AioGraphiteSendException as exc:
                for metric in metrics:
                    queue.put_nowait(metric)

                fail = exc
            else:
                fail = None

    async def close(self):
        self._running = False
        self._sender_task.cancel()

        try:
            await self._sender_task
        except CancelledError:
            pass
        except Exception as exc:
            logger.error("Error at %s sender task: %s", self.__class__.__name__, exc, exc_info=exc)

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

    # noinspection PyTypeChecker
    return _graphite
