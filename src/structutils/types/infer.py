import functools
import inspect
import operator
from typing import Any, Callable


# TODO: Use TypeForm in Python 3.15 (PEP 747)

def infer_type(value: Any, /) -> Any:
  cache = set[int]()

  def infer(value: Any, /):
    value_id = id(value)

    if value_id in cache:
      return Any

    cache.add(value_id)

    value_type = type(value)

    if value is None:
      return None

    for collection_type in (frozenset, list, set):
      if value_type is collection_type:
        if value:
          return collection_type[ # type: ignore
            functools.reduce(operator.or_, (infer(item) for item in value))
          ]
        else:
          return collection_type

    if value_type is dict:
      if value:
        return dict[
          functools.reduce(operator.or_, (infer(key) for key in value.keys())),
          functools.reduce(operator.or_, (infer(value) for value in value.values())),
        ]
      else:
        return dict

    if value_type is tuple:
      return tuple[*(map(infer, value))]

    if value_type is type:
      return type[value]

    # For generics
    if hasattr(value, '__orig_class__'):
      return value.__orig_class__

    if inspect.isfunction(value):
      return Callable[..., Any]

    return value_type

  return infer(value)
