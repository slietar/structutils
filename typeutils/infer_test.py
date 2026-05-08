from types import EllipsisType
from typing import Any, Callable

from .infer import infer_type


x = []
x.append(x)

assert infer_type([3, 4]) == list[int]
assert infer_type([3, 'a']) == list[int | str]
assert infer_type([]) is list
assert infer_type(None) is None
assert infer_type(Ellipsis) == EllipsisType
assert infer_type(3) is int
assert infer_type('foo') is str
assert infer_type({3, 4}) == set[int]
assert infer_type(frozenset({3, 4})) == frozenset[int]
assert infer_type({}) is dict
assert infer_type({3: 'a', 4: 'b'}) == dict[int, str]
assert infer_type({3: 'a', 4: 5}) == dict[int, int | str]
assert infer_type((3, 'a')) == tuple[int, str]
assert infer_type(lambda x: x) == Callable[..., Any]
assert infer_type(x) == list[Any]
