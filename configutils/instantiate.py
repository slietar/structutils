import builtins
import contextlib
import dataclasses
import types
from types import GenericAlias, UnionType
from typing import Any, Optional, Union, get_args, get_origin

from ..typeutils import format_type, get_type
from .error import InstantiationError


def instantiate(type_, data, /) -> Any:
  """
  Instantiate a structure from a type and JSON-serializable corresponding data.

  The data is deep-copied and no reference to the original object is retained.
  """
  print(f'Instantiating \033[31m{format_type(type_)}\033[0m with \033[31m{data}\033[0m')

  if get_origin(type_) is Union:
    match get_args(type_):
      case ((other_type, types.NoneType) | (types.NoneType, other_type)):
        if data is None:
          return None

        return instantiate(other_type, data)

  match type_:
    case builtins.float:
      if not isinstance(data, (int, float)):
        raise InstantiationError(f'Expected float, got {format_type(get_type(data))}')

      return float(data)

    case builtins.int | builtins.str:
      if not isinstance(data, type_):
        raise InstantiationError(f'Expected {format_type(type_)}, got {format_type(get_type(data))}')

      return data

    case GenericAlias(__origin__=builtins.list):
      if not isinstance(data, list):
        raise InstantiationError(f'Expected list, got {format_type(get_type(data))}')

      return [instantiate(type_.__args__[0], item) for item in data]

    case UnionType(__args__=((other_type, types.NoneType) | (types.NoneType, other_type))):
      if data is None:
        return None

      return instantiate(other_type, data)

    case _:
      if isinstance(data, dict) and ('_target_' in data):
        subclasses = type_.__subclasses__()
        subclasses_by_name = { subclass.__name__: subclass for subclass in subclasses }

        if len(subclasses_by_name) == len(subclasses):
          target = subclasses_by_name[data['_target_']]
        else:
          raise InstantiationError(f'Cannot find subclass {data['_target_']} of {type_.__name__}')
      else:
        target = type_

      if not dataclasses.is_dataclass(target):
        raise InstantiationError(f'Expected dataclass, got {format_type(get_type(target))}')

      fields = dataclasses.fields(target)

      try:
        return target(**{ field.name: instantiate(field.type, data[field.name]) for field in fields if field.name in data }) # type: ignore
      except TypeError as e:
        raise InstantiationError from e


@contextlib.contextmanager
def assert_raises(exception_type: type[Exception]):
  try:
    yield
  except Exception as e:
    if not isinstance(e, exception_type):
      raise
  else:
    raise AssertionError(f'Expected {exception_type.__name__} to be raised, but no exception was raised.')


assert instantiate(int, 3) == 3
assert instantiate(list[int], [3, 4]) == [3, 4]
assert instantiate(float, 3) == 3.0
assert isinstance(instantiate(float, 3), float)
assert instantiate(int | None, None) is None
assert instantiate(int | None, 3) == 3
assert instantiate(Optional[int], None) is None

print()

with assert_raises(InstantiationError):
  instantiate(list[int], [3, 4.0])

with assert_raises(InstantiationError):
  assert instantiate(list[int | str], [3, '4']) == [3, '4']
