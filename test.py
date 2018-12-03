import time
from sized_cacher import Cache, DiskCache


def test_cache():
    c = Cache(3, 5)
    for i in range(20):
        c.save(i, i, a=i)
        time.sleep(1)
        _i = i - 1
        x = c.get(_i, a=_i)
        c.debug()
        # assert x == i - 1 if i > 0 else x is None


def test_disk_cache():
    disk_cache = DiskCache("./caches", maxsize=3)

    @disk_cache.caching
    def fn(a):
        return a

    for i in range(10):
        print(fn(i))


test_disk_cache()
test_cache()
