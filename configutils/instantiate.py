import builtins
import contextlib
import functools
import inspect
import types
import typing
from dataclasses import dataclass
from inspect import Parameter
from types import GenericAlias, UnionType
from typing import Annotated, Any, Literal, Optional, TypeAliasType, override

from typeutils import format_type, infer_type

from .error import InstantiationError, SchemaError
from .load import load


InheritedDictAnn = object()
type InheritedDict[K, V] = Annotated[dict[K, V], InheritedDictAnn]


def instantiate(schema, first_data, /, *other_datas, _partial: bool = False) -> Any:
  """
  Instantiate a structure from a type and JSON-serializable corresponding data.

  The data is deep-copied and no reference to the original object is retained.
  """

  datas = (first_data, *other_datas)
  local_instantiate = functools.partial(instantiate, _partial=_partial)

  # print(f'Instantiating \033[31m{format_type(schema)}\033[0m with ' + ' and '.join(f'\033[31m{data!r}\033[0m' for data in datas) + (' (partial)' if _partial else ''))
  # from .check import check
  # check(schema)


  match typing.get_origin(schema):
    case builtins.dict:
      inherit = False
      key_schema, value_schema = typing.get_args(schema)

      if key_schema not in (int, str):
        raise SchemaError(f'Unsupported key type {format_type(key_schema)}')

      for data in datas:
        if type(data) is not dict:
          raise InstantiationError(f'Expected dict, got {format_type(infer_type(data))}')

      result = dict()

      if inherit:
        values = dict[str, list[Any]]()

        for data in datas:
          for key, value in data.items():
            values.setdefault(local_instantiate(key_schema, key), []).append(value)

        for key, item_values in values.items():
          result[key] = local_instantiate(value_schema, *item_values)
      else:
        for key, value in first_data.items():
          result[local_instantiate(key_schema, key)] = local_instantiate(value_schema, value)

        for data in datas[1:]:
          for key, value in data.items():
            local_instantiate(key_schema, key, _partial=True)
            local_instantiate(value_schema, value, _partial=True)

      return result

    # Handles Optional[.]
    case typing.Union:
      match typing.get_args(schema):
        case ((other_type, types.NoneType) | (types.NoneType, other_type)):
          nonnone_datas = [data for data in datas if data is not None]

          if first_data is None:
            if nonnone_datas:
              local_instantiate(other_type, *nonnone_datas, _partial=True)

            return None

          return local_instantiate(other_type, *nonnone_datas)

    case typing.Literal:
      for data in datas:
        if data not in typing.get_args(schema):
          raise InstantiationError(f'Expected {format_type(schema)}, got {repr(data)}')

      return first_data


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

      return [local_instantiate(schema.__args__[0], item) for item in first_data]

    case TypeAliasType():
      return local_instantiate(schema.__value__, first_data)

    case typing.Any:
      return first_data

    # Handles . | None
    case UnionType(__args__=((other_type, types.NoneType) | (types.NoneType, other_type))):
      nonnone_datas = [data for data in datas if data is not None]

      if first_data is None:
        if nonnone_datas:
          local_instantiate(other_type, *nonnone_datas, _partial=True)

        return None

      return local_instantiate(other_type, *nonnone_datas)

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


      if explicit_targets[0] is not None:
        first_target = explicit_targets[0]
        relevant_datas = [first_data]
        Error = InstantiationError

        for data in datas[1:]:
          local_instantiate(schema, data, _partial=True)
      else:
        first_target = schema
        relevant_datas = [data for data, target in zip(datas, explicit_targets) if target is None]
        Error = SchemaError

        for data, target in zip(datas, explicit_targets):
          if target is not None:
            local_instantiate(target, data, _partial=True)

      signature = inspect.signature(first_target)

      arguments = dict[str, Any]()
      var_parameter = None

      # For now, all parameters are required to have a type annotation, even if
      # they are not used.

      for parameter in signature.parameters.values():
        if parameter.kind is Parameter.POSITIONAL_ONLY:
          if parameter.default is Parameter.empty:
            raise Error(f'Positional-only parameter "{parameter.name}" of {format_type(first_target)} is not supported')

          continue

        if parameter.annotation is Parameter.empty:
          raise Error(f'Parameter "{parameter.name}" of {format_type(schema)} is missing a type annotation')

        if parameter.kind is Parameter.VAR_POSITIONAL:
          continue

        if parameter.kind is Parameter.VAR_KEYWORD:
          var_parameter = parameter
          continue

        values = [data[parameter.name] for data in relevant_datas if parameter.name in data]

        if values:
          arguments[parameter.name] = local_instantiate(parameter.annotation, *values)
        elif (parameter.default is Parameter.empty) and (not _partial):
          raise InstantiationError(f'Missing required argument "{parameter.name}" for {format_type(first_target)}')

      extra_argument_names = {name for data in relevant_datas for name in data.keys() if name != '_target_'} - set(arguments.keys())

      for name in extra_argument_names:
        if var_parameter is not None:
          values = [data[name] for data in relevant_datas if name in data]
          arguments[name] = local_instantiate(var_parameter.annotation, *values)
        else:
          raise InstantiationError(f'Unexpected argument "{name}" for {format_type(first_target)}')

      if _partial:
        return None

      try:
        return first_target(**arguments)
      except Exception as e:
        raise InstantiationError(f'Failed to instantiate {format_type(first_target)}: {e}') from e

    case _:
      raise SchemaError(f'Unsupported type {format_type(schema)}')


@contextlib.contextmanager
def assert_raises(exception_type: type[Exception], /):
  try:
    yield
  except Exception as e:
    if not isinstance(e, exception_type):
      raise
  else:
    raise AssertionError(f'Expected {exception_type.__name__} to be raised, but no exception was raised')


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

class E:
  def __init__(self, a: int, **b: str):
    self.a = a
    self.b = b

  @override
  def __eq__(self, other):
    return isinstance(other, E) and (self.a == other.a) and (self.b == other.b)

@dataclass
class F:
  a: A

class G(A):
  def __init__(self, a: int, /):
    pass

type H = int

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
assert instantiate(Literal['a', 3], 'a') == 'a'
assert instantiate(A, dict(_target_='B', x=3, y='4'), dict(x=5)) == B(x=3, y='4')
assert instantiate(E, dict(a=3)) == E(a=3)
assert instantiate(E, dict(a=3, x='1')) == E(a=3, x='1')
assert instantiate(E, dict(a=3), dict(x='1')) == E(a=3, x='1')
assert instantiate(Optional[F], None, dict(a=dict(x=3))) is None
assert instantiate(Any, 3, 'a') == 3
assert instantiate(dict[str, int], {'a': 3, 'b': 4}, {'c': 5}) == {'a': 3, 'b': 4}
# assert instantiate(InheritedDict[str, int], {'a': 3, 'b': 4}, {'c': 5}) == {'a': 3, 'b': 4, 'c': 5}
assert instantiate(H, 3) == 3


with assert_raises(InstantiationError):
  instantiate(list[int], [3, 4.0])

with assert_raises(SchemaError):
  assert instantiate(list[int | str], [3, '4']) == [3, '4']

with assert_raises(InstantiationError):
  instantiate(A, dict(x=3))

with assert_raises(InstantiationError):
  instantiate(A, dict(x=3, y=4))

with assert_raises(InstantiationError):
  instantiate(A, dict(x=3, y='4', z=5))

with assert_raises(SchemaError):
  instantiate(C, dict())

with assert_raises(InstantiationError):
  instantiate(Literal['a', 3], 'b')

with assert_raises(InstantiationError):
  instantiate(Optional[int], None, 'a')

with assert_raises(InstantiationError):
  instantiate(A, dict(_target_='B', x=3, y='4'), dict(x='5'))

with assert_raises(InstantiationError):
  instantiate(E, dict(a=3, x=1))

with assert_raises(InstantiationError):
  instantiate(E, dict(a=3), dict(x=1))

with assert_raises(InstantiationError):
  instantiate(E, dict(a=3), dict(x='1'), dict(x=1))

with assert_raises(InstantiationError):
  instantiate(A, dict(_target_='B', x=3))

with assert_raises(InstantiationError):
  instantiate(A, dict(_target_='G'))

with assert_raises(SchemaError):
  instantiate(dict[A, int], {})

with assert_raises(InstantiationError):
  instantiate(dict[str, int], {3: 4})
