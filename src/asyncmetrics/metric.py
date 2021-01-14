from asyncio import iscoroutinefunction
from functools import wraps
from time import monotonic
from typing import Callable, Optional, Union

from .graphite import Graphite

__all__ = [
    'AvgMetric',
    'AvgMsMetric',
    'AvgNsMetric',
    'AvgUsMetric',
    'CountMetric',
    'MaxMetric',
    'MaxMsMetric',
    'MaxNsMetric',
    'MaxUsMetric',
    'Metric',
    'MinMetric',
    'MinMsMetric',
    'MinNsMetric',
    'MinUsMetric',
    'MsMetric',
    'NsMetric',
    'SumMetric',
    'SumMsMetric',
    'SumNsMetric',
    'SumUsMetric',
    'UsMetric',
    'count',
    'time',
]


class _MetricMeta(type):
    def __new__(mcs, name, bases, namespace):
        graphite = namespace.pop('graphite', None)
        prefix = namespace.pop('prefix', None)
        cls = super().__new__(mcs, name, bases, namespace)

        if graphite:
            cls.graphite = graphite

        if prefix:
            cls.prefix = prefix

        return cls

    @property
    def graphite(cls) -> Graphite:
        graphite = getattr(cls, '_graphite', None)

        if not graphite:
            graphite = Graphite()
            setattr(cls, '_graphite', graphite)

        return graphite

    @graphite.setter
    def graphite(cls, value: Graphite):
        if not isinstance(value, Graphite):
            raise TypeError("graphite must be Graphite, not {}", type(value).__name__)

        setattr(cls, '_graphite', value)

    @property
    def prefix(cls) -> str:
        return getattr(cls, '_prefix', '')

    @prefix.setter
    def prefix(cls, value: str):
        if not isinstance(value, str):
            raise TypeError("prefix must be str, not {}", type(value).__name__)

        setattr(cls, '_prefix', value)

    @prefix.deleter
    def prefix(cls):
        if hasattr(cls, '_prefix'):
            delattr(cls, '_prefix')


class Metric(metaclass=_MetricMeta):
    def __init__(self, metric: str, *, graphite: Optional[Graphite] = None):
        if not isinstance(metric, str):
            raise TypeError("metric must be str, not {}", type(metric).__name__)

        if graphite and not isinstance(graphite, Graphite):
            raise TypeError("graphite must be Graphite, not {}", type(graphite).__name__)

        self._metric = metric
        self._graphite = graphite

    @property
    def metric(self) -> str:
        return '.'.join(x for x in (type(self).prefix, self._metric) if x)

    def _calculate_time(self, start: float, stop: float) -> int:
        if isinstance(self, MsMetric):
            threshold = 3
        elif isinstance(self, UsMetric):
            threshold = 6
        else:
            threshold = 9

        return int(round(stop - start, threshold) * 10 ** threshold)

    def send(self, value: int, timestamp: Optional[int] = None):
        graphite = self._graphite or type(self).graphite
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
                start = monotonic()
                ret = await func(*args, **kwargs)
                stop = monotonic()
                self.send(self._calculate_time(start, stop))
                return ret
        else:
            @wraps(func)
            def deco(*args, **kwargs):
                start = monotonic()
                ret = func(*args, **kwargs)
                stop = monotonic()
                self.send(self._calculate_time(start, stop))
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


class _TimeMetric(Metric):
    @property
    def metric(self) -> str:
        return super().metric + '.time'


class MsMetric(_TimeMetric):
    @property
    def metric(self) -> str:
        return super().metric + '.ms'


class UsMetric(_TimeMetric):
    @property
    def metric(self) -> str:
        return super().metric + '.us'


class NsMetric(_TimeMetric):
    @property
    def metric(self) -> str:
        return super().metric + '.ns'


class MaxMsMetric(MsMetric, MaxMetric):
    pass


class MinMsMetric(MsMetric, MinMetric):
    pass


class AvgMsMetric(MsMetric, AvgMetric):
    pass


class SumMsMetric(MsMetric, SumMetric):
    pass


class MaxUsMetric(UsMetric, MaxMetric):
    pass


class MinUsMetric(UsMetric, MinMetric):
    pass


class AvgUsMetric(UsMetric, AvgMetric):
    pass


class SumUsMetric(UsMetric, SumMetric):
    pass


class MaxNsMetric(NsMetric, MaxMetric):
    pass


class MinNsMetric(NsMetric, MinMetric):
    pass


class AvgNsMetric(NsMetric, AvgMetric):
    pass


class SumNsMetric(NsMetric, SumMetric):
    pass


def count(func: Union[Callable, str], *, klass: _MetricMeta = CountMetric) -> Callable[[Callable], Callable]:
    if isinstance(func, Callable):
        return klass('{}.{}'.format(func.__module__, func.__qualname__)).count(func)
    else:
        return klass(func).count


def time(func: Union[Callable, str], *, klass: _MetricMeta = NsMetric) -> Callable[[Callable], Callable]:
    if isinstance(func, Callable):
        return klass('{}.{}'.format(func.__module__, func.__qualname__)).time(func)
    else:
        return klass(func).time
