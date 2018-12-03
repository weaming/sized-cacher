import time
import os
import hashlib
from threading import Lock
from collections import namedtuple

version = "1.1"
CacheValue = namedtuple("CacheValue", ["ts", "value"])


class Cache:
    def __init__(self, maxsize=100, ttl=60 * 60 * 24):
        """use ttl to control expire"""
        self.maxsize = maxsize
        self.ttl = ttl

        self.cache = {}
        self._lock = Lock()

    @staticmethod
    def timestamp():
        """timestamp to determine the freshness of a key"""
        return time.time()

    @staticmethod
    def _get_key(*args, **kwargs):
        """parse the call parameters to a hashable dict key"""
        return str((args, kwargs))

    def _is_expire(self, key, pop=True):
        """return false if the key is fresh enough, else remove the key from cache dict if exist"""
        if key in self.cache:
            ts, v = self.cache[key]
            if self.timestamp() - ts <= self.ttl:
                return False
            else:
                if pop:
                    self.cache.pop(key)
        return True

    def fake_value(self, value):
        """override this to add more actions"""
        return value

    def real_value(self, value):
        """override this to add more actions"""
        return value

    def clean_value(self, value):
        """override this to add more actions"""
        pass

    def save(self, value, *args, **kwargs):
        """parse the value a shorter key, then stored it in cache dict"""
        value = self.fake_value(value)

        key = self._get_key(*args, **kwargs)
        old_value = self._refresh(key, value)
        if old_value:
            return old_value
        else:
            self.cache[key] = CacheValue(self.timestamp(), value)

        if len(self.cache) > self.maxsize:
            self._gc()

    def _refresh(self, key, new_value=None):
        """update the timestamp of key, optional new_value to replace the old one"""
        if key in self.cache:
            v = self.cache[key].value
            self.cache[key] = CacheValue(self.timestamp(), new_value or v)
            return v

    def _gc(self):
        """clean cache dict, and other actions if needed"""
        with self._lock:
            old_values = list(self.cache.values())
            cache = [
                (k, v)
                for k, v in self.cache.items()
                if not self._is_expire(k, pop=False)
            ]
            cache.sort(key=lambda x: x[1].ts)
            self.cache = dict(cache[-self.maxsize :])

            # clean keys
            current_values = list(self.cache.values())
            for v in old_values:
                if v not in current_values:
                    self.clean_value(v.value)

    def get(self, *args, **kwargs):
        """get the value cached"""
        key = self._get_key(*args, **kwargs)
        if not self._is_expire(key):
            fake_value = self._refresh(key)
            return self.real_value(fake_value)
        return None

    def debug(self):
        print("cache", self.cache)

    def caching(self, fn):
        """decorator to cache function calls"""

        def _new_fn(*args, **kwargs):
            c = self.get(*args, **kwargs)
            if c is not None:
                return c

            rv = fn(*args, **kwargs)
            self.save(rv, *args, **kwargs)
            return rv

        return _new_fn


def sha256(bin):
    m = hashlib.sha256()
    m.update(bin)
    return m.hexdigest()


def prepare_dir(path):
    if not path.endswith("/"):
        path = os.path.dirname(path)

    if not os.path.isdir(path):
        os.makedirs(path)


class DiskCache(Cache):
    def __init__(self, cache_dir, *args, **kwargs):
        self.cache_dir = "./caches"
        super(DiskCache, self).__init__(*args, **kwargs)

    @staticmethod
    def bytes_to_key(bin):
        return sha256(bin)

    def name_to_path(self, name):
        return os.path.join(self.cache_dir, name)

    def ensure_bytes(self, value):
        if not isinstance(value, bytes):
            value = str(value).encode()
        return value

    def fake_value(self, value):
        value = self.ensure_bytes(value)
        name = self.bytes_to_key(value)
        path = self.name_to_path(name)
        prepare_dir(path)
        with open(path, "wb") as f:
            f.write(value)
        return name

    def real_value(self, value):
        path = self.name_to_path(value)
        if os.path.isfile(path):
            with open(path, "rb") as f:
                return f.read()
        return None

    def clean_value(self, value):
        print(value)
        path = self.name_to_path(value)
        if os.path.isfile(path):
            os.remove(path)
