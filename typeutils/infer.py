import functools
import inspect
import operator
from types import EllipsisType
from typing import Any, Callable


# TODO: Use TypeForm in Python 3.15 (PEP 747)
# TODO: Recursive values
# TODO: Callables

def infer_type(value: Any, /):
  value_type = type(value)

  if value is None:
    return None

  for collection_type in (frozenset, list, set):
    if value_type is collection_type:
      if value:
        return collection_type[ # type: ignore
          functools.reduce(operator.or_, (infer_type(item) for item in value))
        ]
      else:
        return collection_type

  if value_type is dict:
    if value:
      return dict[
        functools.reduce(operator.or_, (infer_type(key) for key in value.keys())),
        functools.reduce(operator.or_, (infer_type(value) for value in value.values())),
      ]
    else:
      return dict

  if value_type is tuple:
    return tuple[*(map(infer_type, value))]

  # For generics
  if hasattr(value, '__orig_class__'):
    return value.__orig_class__

  if inspect.isfunction(value):
    signature = inspect.signature(value)
    return Callable[..., Any]

  return type(value)


assert infer_type([3, 4]) == list[int]
assert infer_type([3, 'a']) == list[int | str]
assert infer_type([]) == list
assert infer_type(None) == None
assert infer_type(Ellipsis) == EllipsisType
assert infer_type(3) == int
assert infer_type('foo') == str
assert infer_type({3, 4}) == set[int]
assert infer_type(frozenset({3, 4})) == frozenset[int]
assert infer_type({}) == dict
assert infer_type({3: 'a', 4: 'b'}) == dict[int, str]
assert infer_type({3: 'a', 4: 5}) == dict[int, int | str]
assert infer_type((3, 'a')) == tuple[int, str]
assert infer_type(lambda x: x) == Callable[..., Any]

# x = []
# x.append(x)

# print(infer_type(x))
# assert infer_type(x) == list[list[A]]
