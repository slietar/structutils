import builtins
import contextlib
import inspect
import types
import typing
from dataclasses import dataclass
from inspect import Parameter
from types import GenericAlias, UnionType
from typing import Any, Optional, Protocol, Union, override

from typeutils import format_type, infer_type

from .error import InstantiationError
from .load import load


def instantiate(schema, first_data, /, *datas) -> Any:
  """
  Instantiate a structure from a type and JSON-serializable corresponding data.

  The data is deep-copied and no reference to the original object is retained.
  """

  datas = (first_data, *datas)

  print(f'Instantiating \033[31m{format_type(schema)}\033[0m with ' + ' and '.join(f'\033[31m{data}\033[0m' for data in datas))

  if typing.get_origin(schema) is Union:
    match typing.get_args(schema):
      case ((other_type, types.NoneType) | (types.NoneType, other_type)):
        if first_data is None:
          return None

        return instantiate(other_type, *(data for data in datas if data is not None))


  data_types = [type(data) for data in datas]

  match schema:
    case builtins.float:
      for data_type, data in zip(data_types, datas):
        if not (data_type is int) | (data_type is float):
          raise InstantiationError(f'Expected float, got {format_type(infer_type(data))}')

      return float(first_data)

    case builtins.int | builtins.str:
      for data_type, data in zip(data_types, datas):
        if data_type is not schema:
          raise InstantiationError(f'Expected {format_type(schema)}, got {format_type(infer_type(data))}')

      return first_data

    case GenericAlias(__origin__=builtins.list):
      for data_type, data in zip(data_types, datas):
        if data_type is not list:
          raise InstantiationError(f'Expected list, got {format_type(infer_type(data))}')

      return [instantiate(schema.__args__[0], item) for item in first_data]

    case UnionType(__args__=((other_type, types.NoneType) | (types.NoneType, other_type))):
      # Alternative
      #
      # nonnone_datas = list(itertools.takewhile(lambda data: data is not None, datas))
      #
      # if not nonnone_datas:
      #   return None
      #
      # return instantiate(other_type, *nonnone_datas)

      if first_data is None:
        return None

      return instantiate(other_type, *(data for data in datas if data is not None))

    case _ if inspect.isclass(schema):
      explicit_targets = list[Optional[type]]()

      for data_type, data in zip(data_types, datas):
        if data_type is not dict:
          raise InstantiationError(f'Expected dict, got {format_type(infer_type(data))}')

        # Possibly change the target
        if '_target_' in data:
          data_target = data['_target_']

          if ':' in data_target:
            try:
              target = load(data_target, allow_modules=False)
            except ImportError as e:
              raise InstantiationError(f'Cannot load target "{data_target}"') from e

            if not inspect.isclass(target):
              raise InstantiationError(f'Target {format_type(target)} is not a class')

            if not issubclass(target, schema):
              raise InstantiationError(f'Target {format_type(target)} is not a subclass of {format_type(schema)}')
          else:
            matching_subclass = None

            for subclass in schema.__subclasses__():
              if subclass.__name__ == data_target:
                if matching_subclass is not None:
                  raise InstantiationError(f'Multiple subclasses of {schema.__name__} match "{data_target}"')

                matching_subclass = subclass

            if matching_subclass is None:
              raise InstantiationError(f'Cannot find subclass "{data_target}" of {format_type(schema)}')

            target = matching_subclass
        else:
          target = None

        explicit_targets.append(target)


      first_target = explicit_targets[0] if explicit_targets[0] is not None else schema

      if explicit_targets[0] is not None:
        relevant_datas = [first_data]
        SchemaError = ValueError
      else:
        relevant_datas = [data for data, target in zip(datas, explicit_targets) if target is None]
        SchemaError = InstantiationError

      signature = inspect.signature(first_target)

      arguments = dict[str, Any]()
      has_var = False

      for parameter in signature.parameters.values():
        if parameter.kind is Parameter.POSITIONAL_ONLY:
          if parameter.default is Parameter.empty:
            raise InstantiationError(f'Positional-only parameter "{parameter.name}" of {format_type(first_target)} is not supported')

          continue

        if parameter.kind is Parameter.VAR_POSITIONAL:
          continue

        if parameter.kind is Parameter.VAR_KEYWORD:
          has_var = True
          continue

        if parameter.annotation is Parameter.empty:
          raise SchemaError(f'Parameter "{parameter.name}" of {format_type(schema)} is missing a type annotation')

        found_argument = False

        for data in relevant_datas:
          if parameter.name not in data:
            continue

          value = instantiate(parameter.annotation, data[parameter.name])

          if not found_argument:
            arguments[parameter.name] = value
            found_argument = True

        if (not found_argument) and (parameter.default is Parameter.empty):
          raise SchemaError(f'Missing required argument "{parameter.name}" for {format_type(first_target)}')

      for data in relevant_datas:
        for name, value in data.items():
          if (name in arguments) or (name == '_target_'):
            continue

          if has_var:
            arguments[name] = instantiate(signature.parameters[name].annotation, value)
            continue

          raise InstantiationError(f'Unexpected argument "{name}" for {format_type(first_target)}')

      try:
        return first_target(**arguments)
      except Exception as e:
        raise InstantiationError(f'Failed to instantiate {format_type(first_target)}: {e}') from e

    case _:
      raise ValueError(f'Unsupported type {format_type(infer_type(schema))}')


@contextlib.contextmanager
def assert_raises(exception_type: type[Exception], /):
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

class C:
  def __init__(self, p: int, /):
    pass

class D:
  def __init__(self, p: int = 5):
    self.p = p

  @override
  def __eq__(self, other):
    return isinstance(other, D) and (self.p == other.p)

assert instantiate(int, 3) == 3
assert instantiate(list[int], [3, 4]) == [3, 4]
assert instantiate(float, 3) == 3.0
assert isinstance(instantiate(float, 3), float)
assert instantiate(int | None, None) is None
assert instantiate(int | None, 3) == 3
assert instantiate(Optional[int], None) is None
assert instantiate(A, dict(x=3, y='4')) == A(3, '4')
assert instantiate(A, dict(_target_='B', x=3, y='4')) == B(3, '4')
assert instantiate(D, dict()) == D()
assert instantiate(D, dict(p=6)) == D(p=6)
assert instantiate(A, dict(x=5), dict(x=3, y='4')) == A(5, '4')
assert instantiate(Optional[A], dict(x=5), None, dict(x=3, y='4')) == A(5, '4')
assert instantiate(Optional[A], None, dict(x=3, y='4')) is None


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

# Maybe change to ValueError?
with assert_raises(InstantiationError):
  instantiate(C, dict())


class E(Protocol):
  x: int
  y: str
