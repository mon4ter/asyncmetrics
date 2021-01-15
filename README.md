# asyncmetrics
[![PyPI version](https://img.shields.io/pypi/v/asyncmetrics.svg)](https://pypi.org/project/asyncmetrics)
[![Python version](https://img.shields.io/pypi/pyversions/asyncmetrics.svg)](https://pypi.org/project/asyncmetrics)
[![Build Status](https://travis-ci.org/mon4ter/asyncmetrics.svg?branch=master)](https://travis-ci.org/mon4ter/asyncmetrics)
[![codecov](https://codecov.io/gh/mon4ter/asyncmetrics/branch/master/graph/badge.svg)](https://codecov.io/gh/mon4ter/asyncmetrics)

Send metrics to Graphite asynchronously from your asyncio application

### Example
```python
from asyncmetrics import count, time

@count
async def get_something():
    """Every call will produce `<module>.get_something.count 1 <now>`""" 

@time
async def process_something():
    """Every call will produce `<module>.process_something.time.us <duration> <now>`""" 

```
