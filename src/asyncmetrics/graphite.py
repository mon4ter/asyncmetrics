from asyncio import CancelledError, Queue, ensure_future, shield, sleep
from logging import getLogger
from time import time
from typing import Optional

from .protocols import PlainTcp, ProtocolError
from .protocols.protocol import Protocol

__all__ = [
    'Graphite',
]

logger = getLogger(__package__)


class Graphite:
    def __init__(self, protocol: Protocol = PlainTcp(), *,
                 queue_size: int = 1000000, flush_interval: float = 1., fail_wait: float = 60.):
        self._protocol = protocol
        self._queue = Queue()
        self._sender_task = ensure_future(self._sender())
        self._running = True
        self._queue_size = queue_size
        self._flush_interval = flush_interval
        self._fail_wait = fail_wait

    async def _sender(self):
        protocol = self._protocol
        queue = self._queue
        flushing = False
        send_failed = False

        while self._running or flushing:
            metrics = []

            try:
                if send_failed:
                    logger.debug("Sleeping for %s seconds", self._fail_wait)
                    await sleep(self._fail_wait)
                else:
                    await sleep(self._flush_interval)

                if not flushing:
                    metrics.append(await queue.get())
            except CancelledError:
                self._running = False

            while not queue.empty():
                metrics.append(queue.get_nowait())

            metrics_len = len(metrics)
            off_limit = metrics_len - self._queue_size

            if off_limit > 0:
                logger.warning("Dropping %s metrics over the limit", off_limit)
                metrics = metrics[-self._queue_size:]

            try:
                await shield(protocol.send(metrics))
            except CancelledError:
                self._running = False
                flushing = True
            except ProtocolError as exc:
                logger.error("%s", exc)

                for metric in metrics:
                    queue.put_nowait(metric)

                send_failed = True
            else:
                if metrics_len:
                    logger.debug("Sent %s metrics", metrics_len)

                send_failed = False
                flushing = False

    async def close(self):
        self._sender_task.cancel()

        try:
            await self._sender_task
        except CancelledError:
            pass
        except Exception as exc:
            logger.error("Error at %s sender task: %s", self.__class__.__name__, exc, exc_info=exc)

        self._protocol.close()

    def send(self, metric: str, value: int, timestamp: Optional[int] = None):
        if not self._running:
            logger.warning("Sender is not running, not sending")
            return

        try:
            self._queue.put_nowait((str(metric), int(value), int(timestamp or time())))
        except ValueError as exc:
            logger.error("Invalid metric %r: %s", (metric, value, timestamp), exc)
