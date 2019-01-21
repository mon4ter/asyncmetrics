from asyncio import iscoroutinefunction
from functools import wraps
from time import time as time_
from typing import Optional, Callable

from .graphite import get_graphite, Graphite

__all__ = [
    'Metric',
    'MaxMetric',
    'MinMetric',
    'AvgMetric',
    'SumMetric',
    'CountMetric',
    'count',
    'time',
]


class Metric:
    def __init__(self, path: str, *, graphite: Graphite = None):
        self._metric = None

        self._path = path
        self._graphite = graphite
        self._prefixes = []
        self._suffixes = []

    @property
    def metric(self) -> str:
        if self._metric is None:
            self._metric = '.'.join(p for p in (
                '.'.join(p for p in self._prefixes if p),
                self._path,
                '.'.join(s for s in self._suffixes if s)
            ) if p)

        return self._metric

    def send(self, value: int, timestamp: Optional[int] = None):
        graphite = self._graphite or get_graphite()
        graphite.send(self.metric, value, timestamp)

    def count(self, func) -> Callable:
        @wraps(func)
        def deco(*args, **kwargs):
            self.send(1)
            return func(*args, **kwargs)
        return deco

    def time(self, func) -> Callable:
        if iscoroutinefunction(func):
            @wraps(func)
            async def deco(*args, **kwargs):
                start = time_()
                ret = await func(*args, **kwargs)
                self.send(int(round(time_() - start, 6) * 1000000))
                return ret
        else:
            @wraps(func)
            def deco(*args, **kwargs):
                start = time_()
                ret = func(*args, **kwargs)
                self.send(int(round(time_() - start, 6) * 1000000))
                return ret

        return deco


class MaxMetric(Metric):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._suffixes.append('max')


class MinMetric(Metric):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._suffixes.append('min')


class AvgMetric(Metric):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._suffixes.append('avg')


class SumMetric(Metric):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._suffixes.append('sum')


class CountMetric(Metric):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._suffixes.append('count')


def count(metric: str) -> Callable:
    return Metric(metric).count


def time(metric: str) -> Callable:
    return Metric(metric).time
