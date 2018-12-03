# Sized Cacher

Cache results of function call with expire and maxsize.

`pip3 install -U sized-cacher`

## Usage

```python
disk_cache = DiskCache("./caches", maxsize=3)

@disk_cache.caching
def fn(a):
    return a

for i in range(10):
    print(fn(i))
```

## API

* `self.save(value, *args, **kwargs)`
* `new_func = self.caching(func)`
