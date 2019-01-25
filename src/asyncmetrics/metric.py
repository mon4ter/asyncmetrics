from asyncio import iscoroutinefunction
from functools import wraps
from time import time as time_
from typing import Callable, Optional

from .graphite import Graphite, get_graphite

__all__ = [
    'AvgMetric',
    'CountMetric',
    'MaxMetric',
    'Metric',
    'MinMetric',
    'SumMetric',
    'count',
    'time',
]


class MetricMeta(type):
    def __new__(mcs, name, bases, namespace):
        prefix = namespace.pop('prefix', 'notset')
        klass = super().__new__(mcs, name, bases, namespace)

        if prefix != 'notset':
            klass.prefix = prefix

        return klass

    @property
    def prefix(self) -> str:
        return getattr(self, '_prefix', '')

    @prefix.setter
    def prefix(self, value: str):
        setattr(self, '_prefix', value)


class Metric(metaclass=MetricMeta):
    def __init__(self, metric: str, *, graphite: Graphite = None):
        self._metric = metric
        self._graphite = graphite

    @property
    def metric(self) -> str:
        return '.'.join(x for x in (type(self).prefix, self._metric) if x)

    def send(self, value: int, timestamp: Optional[int] = None):
        graphite = self._graphite or get_graphite()
        graphite.send(self.metric, value, timestamp)

    def count(self, func: Callable) -> Callable:
        @wraps(func)
        def deco(*args, **kwargs):
            self.send(1)
            return func(*args, **kwargs)
        return deco

    def time(self, func: Callable) -> Callable:
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
    @property
    def metric(self) -> str:
        return super().metric + '.max'


class MinMetric(Metric):
    @property
    def metric(self) -> str:
        return super().metric + '.min'


class AvgMetric(Metric):
    @property
    def metric(self) -> str:
        return super().metric + '.avg'


class SumMetric(Metric):
    @property
    def metric(self) -> str:
        return super().metric + '.sum'


class CountMetric(Metric):
    @property
    def metric(self) -> str:
        return super().metric + '.count'


def count(metric: str, *, klass: MetricMeta = CountMetric) -> Callable[[Callable], Callable]:
    return klass(metric).count


def time(metric: str, *, klass: MetricMeta = Metric) -> Callable[[Callable], Callable]:
    return klass(metric).time
