from functools import wraps
import time
from datetime import datetime, timedelta

from walrus import Cache


class RefreshCache(Cache):
    def conditional_cached(self, key_fn=Cache._key_fn, timeout=None, metrics=False, refresh=None, rate_limit=None):
        def decorator(fn):
            def make_key(args, kwargs):
                return '%s:%s' % (fn.__name__, key_fn(args, kwargs))

            def bust(*args, **kwargs):
                return self.delete(make_key(args, kwargs))

            _metrics = {
                'hits': 0,
                'misses': 0,
                'avg_hit_time': 0,
                'avg_miss_time': 0}

            @wraps(fn)
            def inner(*args, **kwargs):
                start = time.time()
                is_cache_hit = True
                key = make_key(args, kwargs)
                res = self.get(key)
                res_bup = None
                if refresh:
                    try:
                        cache_set_dt = res['dt']
                    except (TypeError, KeyError) as e:
                        cache_set_dt = None
                    if cache_set_dt and datetime.utcnow() - cache_set_dt > timedelta(seconds=int(refresh)):
                        res_bup = res
                        res = None
                # print(res)
                # print(res_bup)
                if res is None:
                    if rate_limit is not None and rate_limit.limit(key):
                        is_valid = False
                    else:
                        res, is_valid = fn(*args, **kwargs)
                    if is_valid:
                        if refresh:
                            res['dt'] = datetime.utcnow()
                        self.set(key, res, timeout)
                    elif res_bup:
                        res = res_bup
                    is_cache_hit = False

                if metrics:
                    dur = time.time() - start
                    if is_cache_hit:
                        _metrics['hits'] += 1
                        _metrics['avg_hit_time'] += (dur / _metrics['hits'])
                    else:
                        _metrics['misses'] += 1
                        _metrics['avg_miss_time'] += (dur / _metrics['misses'])

                return res

            inner.bust = bust
            inner.make_key = make_key
            if metrics:
                inner.metrics = _metrics
            return inner
        return decorator
