import builtins
import inspect
import types
import typing
from enum import Enum, EnumType, Flag
from inspect import Parameter
from types import GenericAlias, UnionType
from typing import Any, TypeAliasType

from .annotations import ExactAnn
from typeutils.format import format_type

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
      match typing.get_args(schema):
        case ((other_type, types.NoneType) | (types.NoneType, other_type)):
          check(other_type, _path=_path)
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

    case UnionType(__args__=((other_type, types.NoneType) | (types.NoneType, other_type))):
      check(other_type, _path=_path)

    # Not strictly necessary as enums are classes anyway
    case EnumType() if issubclass(schema, (Enum, Flag)):
      pass

    case _ if inspect.isclass(schema):
      exact_ann = any(ann is ExactAnn for ann in _annotations)

      if inspect.isabstract(schema) or typing.is_protocol(schema):
        if exact_ann:
          raise SchemaError(f'Exact annotation is not allowed for abstract or protocol class {format_type(schema)} at {_path or "<root>"}')
      else:
        functions = typing.get_overloads(schema.__init__) or [schema]

        for function in functions:
          signature = inspect.signature(function)

          for parameter in signature.parameters.values():
            if parameter.kind is Parameter.POSITIONAL_ONLY:
              if parameter.default is Parameter.empty:
                raise SchemaError(f'Positional-only parameter "{parameter.name}" of {format_type(schema)} at {_path or '<root>'} has no default value')

              continue

            if parameter.kind is Parameter.VAR_POSITIONAL:
              continue

            if parameter.annotation is Parameter.empty:
              if parameter.default is Parameter.empty:
                raise SchemaError(f'Parameter "{parameter.name}" of {format_type(schema)} at {_path or '<root>'} is missing a type annotation or a default value')

              continue

            check(parameter.annotation, _path=f'{_path}.{parameter.name}')

    case _:
      raise SchemaError(f'Unsupported type {format_type(schema)} at {_path or '<root>'}')
