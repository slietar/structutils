import builtins
import inspect
import itertools
import types
import typing
from enum import Enum, EnumType, Flag
from inspect import Parameter
from types import GenericAlias, UnionType
from typing import Any, TypeAliasType

from typeutils.format import format_type

from .annotations import ExactAnn
from .error import SchemaError


def check(schema, /, *, _annotations: tuple[Any, ...] = (), _path: str = ''):
  if schema is None:
    return


  match typing.get_origin(schema):
    case builtins.dict:
      key_schema, value_schema = typing.get_args(schema)

      if key_schema not in (int, str):
        raise SchemaError(f'Unsupported key type {format_type(key_schema)}')

      check(value_schema, _path=f'{_path}[]')
      return

    case typing.Annotated:
      check(typing.get_args(schema)[0], _annotations=schema.__metadata__, _path=_path)
      return

    case typing.Literal:
      return

    case typing.Union:
      for arg in typing.get_args(schema):
        check(arg, _path=_path)

      return

    case TypeAliasType(__value__=value):
      check(value[*typing.get_args(schema)])
      return


  match schema:
    case builtins.bool | builtins.float | builtins.int | builtins.str | types.NoneType | typing.Any:
      pass

    case GenericAlias(__origin__=builtins.list):
      check(schema.__args__[0], _path=f'{_path}[]')

    case TypeAliasType():
      check(schema.__value__)

    # Not strictly necessary
    case typing.Any:
      return

    case UnionType(__args__=args):
      for arg in args:
        check(arg, _path=_path)

    # Not strictly necessary as enums are classes anyway
    case EnumType() if issubclass(schema, (Enum, Flag)):
      pass

    case _ if inspect.isclass(schema):
      exact_ann = any(ann is ExactAnn for ann in _annotations)

      if inspect.isabstract(schema) or typing.is_protocol(schema):
        if exact_ann:
          raise SchemaError(f'Exact annotation is not allowed for abstract or protocol class {format_type(schema)} at {_path or "<root>"}')
      else:
        if hasattr(schema.__init__, '__module__'):
          functions = typing.get_overloads(schema.__init__) or [schema.__init__]
          skip_self = True
        else:
          functions = [schema]
          skip_self = False

        for function in functions:
          type_hints = typing.get_type_hints(function, include_extras=True)
          signature = inspect.signature(function)

          for parameter in itertools.islice(signature.parameters.values(), 1 if skip_self else 0, None):
            if parameter.kind is Parameter.POSITIONAL_ONLY:
              if parameter.default is Parameter.empty:
                raise SchemaError(f'Positional-only parameter "{parameter.name}" of {format_type(schema)} at {_path or '<root>'} has no default value')

              continue

            if parameter.kind is Parameter.VAR_POSITIONAL:
              continue

            # Type hints can also be missing in other cases such as @no_type_check
            if not parameter.name in type_hints:
              if parameter.default is Parameter.empty:
                raise SchemaError(f'Parameter "{parameter.name}" of {format_type(schema)} at {_path or '<root>'} is missing a type annotation or a default value')

              continue

            check(type_hints[parameter.name], _path=f'{_path}.{parameter.name}')

    case _:
      raise SchemaError(f'Unsupported type {format_type(schema)} at {_path or '<root>'}')
