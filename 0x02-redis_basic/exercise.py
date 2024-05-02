#!/usr/bin/env python3
"""
Redis module, Writing strings to Redis
Reading from Redis and recovering original type
Incrementing values, storing lists, Retrieving lists
"""
import redis
import uuid
from typing import Any, Union, Callable, Optional
from functools import wraps


def count_calls(method: Callable) -> Callable:
    """
    Prototype: def count_calls(method: Caallable) -> Callable:
    Returns a Callable
    """
    @wraps(method)
    def wrapper(self, *args, **kwds):
        """
        Prototype: def wrapper(self, *args, **kwds):
        Returns wrapper
        """
        key_m = method.__qualname__
        self._redis.incr(key_m)
        return method(self, *args, **kwds)
    return wrapper


def call_history(method: Callable) -> Callable:
    """
    Prototype: def call_history(method: Callable) -> Callable:
    Returns a Callable
    """
    @wraps(method)
    def wrapper(self, *args, **kwds):
        """
        Prototype: def wrapper(self, *args, **kwds):
        Returns wrapper
        """
        key_m = method.__qualname__
        inp_m = key_m + ':inputs'
        outp_m = key_m + ":outputs"
        data = str(args)
        self._redis.rpush(inp_m, data)
        fin = method(self, *args, **kwds)
        self._redis.rpush(outp_m, str(fin))
        return fin
    return wrapper


def replay(fn: Callable) -> None:
    """ Check redis for how many times a function was called and display:
            - How many times it was called
            - Function args and output for each call
    """
    client = redis.Redis()
    calls = client.get(fn.__qualname__).decode('utf-8')
    inputs = [input.decode('utf-8') for input in
              client.lrange(f'{fn.__qualname__}:inputs', 0, -1)]
    outputs = [output.decode('utf-8') for output in
               client.lrange(f'{fn.__qualname__}:outputs', 0, -1)]
    print(f'{fn.__qualname__} was called {calls} times:')
    for input, output in zip(inputs, outputs):
        print(f'{fn.__qualname__}(*{input}) -> {output}')


class Cache():
    """
    Store instance of Redis client as private variable _redis
    Flush the instance using flushdb
    """
    def __init__(self):
        """
        Prototype: def __init__(self):
        Store instance of Redis client as private variable _redis
        """
        self._redis = redis.Redis()
        self._redis.flushdb()

    @call_history
    @count_calls
    def store(self, data: Union[str, bytes, int, float]) -> str:
        """
        Store history of inputs and outputs for a particular function
        """
        gen = str(uuid.uuid4())
        self._redis.set(gen, data)
        return gen

    def get(self, key: str,
            fn: Optional[Callable] = None) -> Union[str, bytes, int, float]:
        """
        Convert data back to desired format
        """
        value = self._redis.get(key)
        return value if not fn else fn(value)

    def get_int(self, key):
        return self.get(key, int)

    def get_str(self, key):
        value = self._redis.get(key)
        return value.decode("utf-8")
