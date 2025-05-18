import functools
import operator
from types import EllipsisType, NoneType
from typing import Any


# TODO: Use TypeForm in Python 3.15 (PEP 747)

def get_type(value: Any, /):
  for collection_type in (list, set):
    if isinstance(value, collection_type):
      if value:
        return collection_type[ # type: ignore
          functools.reduce(operator.or_, (get_type(item) for item in value))
        ]
      else:
        return collection_type

  match value:
    case None:
      return None
    case dict() if value:
      return dict[
        functools.reduce(operator.or_, (get_type(key) for key in value.keys())),
        functools.reduce(operator.or_, (get_type(value) for value in value.values())),
      ]
    case dict():
      return dict
    case tuple():
      return tuple[*(map(get_type, value))]
    case _ if hasattr(value, '__orig_class__'):
      return value.__orig_class__
    case _:
      return type(value)


assert get_type([3, 4]) == list[int]
assert get_type([3, 'a']) == list[int | str]
assert get_type([]) == list
assert get_type(None) == None
assert get_type(Ellipsis) == EllipsisType
assert get_type(3) == int
assert get_type('foo') == str
assert get_type({3, 4}) == set[int]
assert get_type({}) == dict
assert get_type({3: 'a', 4: 'b'}) == dict[int, str]
assert get_type({3: 'a', 4: 5}) == dict[int, int | str]
assert get_type((3, 'a')) == tuple[int, str]
