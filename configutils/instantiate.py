import builtins
import contextlib
import dataclasses
import inspect
import types
import typing
from dataclasses import dataclass
from types import GenericAlias, UnionType
from typing import Any, Optional, Union, get_args, get_origin

from typeutils import format_type, get_type

from .error import InstantiationError
from .load import load


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


  data_type = type(data)

  match type_:
    case builtins.float:
      if not (data_type is int) | (data_type is float):
        raise InstantiationError(f'Expected float, got {format_type(get_type(data))}')

      return float(data)

    case builtins.int | builtins.str:
      if data_type is not type_:
        raise InstantiationError(f'Expected {format_type(type_)}, got {format_type(get_type(data))}')

      return data

    case GenericAlias(__origin__=builtins.list):
      if data_type is not list:
        raise InstantiationError(f'Expected list, got {format_type(get_type(data))}')

      return [instantiate(type_.__args__[0], item) for item in data]

    case UnionType(__args__=((other_type, types.NoneType) | (types.NoneType, other_type))):
      if data is None:
        return None

      return instantiate(other_type, data)


  if not inspect.isclass(type_):
    raise ValueError(f'Unsupported type {format_type(get_type(type_))}')

  if data_type is not dict:
    raise InstantiationError(f'Expected dict, got {format_type(get_type(data))}')

  # Possibly change the target
  if '_target_' in data:
    data_target = data['_target_']

    if ':' in data_target:
      try:
        target = load(data_target, allow_modules=True)
      except ImportError as e:
        raise InstantiationError(f'Cannot load target "{data_target}"') from e

      if not inspect.isclass(target):
        raise InstantiationError(f'Target {format_type(target)} is not a class')

      if not issubclass(target, type_):
        raise InstantiationError(f'Target {format_type(target)} is not a subclass of {format_type(type_)}')
    else:
      matching_subclass = None

      for subclass in type_.__subclasses__():
        if subclass.__name__ == data_target:
          if matching_subclass is not None:
            raise InstantiationError(f'Multiple subclasses of {type_.__name__} match "{data_target}"')

          matching_subclass = subclass

      if matching_subclass is None:
        raise InstantiationError(f'Cannot find subclass "{data_target}" of {format_type(type_)}')

      target = matching_subclass
  else:
    target = type_


  signature = inspect.signature(target)

  arguments = dict[str, Any]()
  has_var = False

  for parameter in signature.parameters.values():
    if parameter.kind in (inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.VAR_POSITIONAL):
      continue

    if parameter.kind == inspect.Parameter.VAR_KEYWORD:
      has_var = True
      continue

    if parameter.name not in data:
      if parameter.default is inspect.Parameter.empty:
        raise InstantiationError(f'Missing required argument "{parameter.name}" for {format_type(target)}')

      continue

    arguments[parameter.name] = instantiate(parameter.annotation, data[parameter.name])

  for name, value in data.items():
    if (name in arguments) or (name == '_target_'):
      continue

    if has_var:
      arguments[name] = instantiate(signature.parameters[name].annotation, value)
      continue

    raise InstantiationError(f'Unexpected argument "{name}" for {format_type(target)}')

  return target(**arguments)


@contextlib.contextmanager
def assert_raises(exception_type: type[Exception]):
  try:
    yield
  except Exception as e:
    if not isinstance(e, exception_type):
      raise
  else:
    raise AssertionError(f'Expected {exception_type.__name__} to be raised, but no exception was raised.')


@dataclass
class A:
  x: int
  y: str

@dataclass
class B(A):
  pass

assert instantiate(int, 3) == 3
assert instantiate(list[int], [3, 4]) == [3, 4]
assert instantiate(float, 3) == 3.0
assert isinstance(instantiate(float, 3), float)
assert instantiate(int | None, None) is None
assert instantiate(int | None, 3) == 3
assert instantiate(Optional[int], None) is None
assert instantiate(A, dict(x=3, y='4')) == A(3, '4')
assert instantiate(A, dict(_target_='B', x=3, y='4')) == B(3, '4')

print()

with assert_raises(InstantiationError):
  instantiate(list[int], [3, 4.0])

with assert_raises(ValueError):
  assert instantiate(list[int | str], [3, '4']) == [3, '4']

with assert_raises(InstantiationError):
  instantiate(A, dict(x=3))

with assert_raises(InstantiationError):
  instantiate(A, dict(x=3, y=4))

with assert_raises(InstantiationError):
  instantiate(A, dict(x=3, y='4', z=5))
