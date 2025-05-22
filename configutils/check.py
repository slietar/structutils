import builtins
from enum import EnumType
import inspect
import types
import typing
from inspect import Parameter
from types import GenericAlias, UnionType
from typing import TypeAliasType

from typeutils.format import format_type

from .error import SchemaError


def check(schema, /, *, _path: str = ''):
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
      check(typing.get_args(schema)[0])
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
    case builtins.float | builtins.int | builtins.str | types.NoneType | typing.Any:
      pass

    case GenericAlias(__origin__=builtins.list):
      check(schema.__args__[0], _path=f'{_path}[]')

    case TypeAliasType():
      check(schema.__value__)

    case UnionType(__args__=((other_type, types.NoneType) | (types.NoneType, other_type))):
      check(other_type, _path=_path)

    # Not strictly necessary as enums are classes anyway
    case _ if type(schema) is EnumType:
      pass

    case _ if inspect.isclass(schema):
      signature = inspect.signature(schema)

      for parameter in signature.parameters.values():
        if parameter.kind is Parameter.POSITIONAL_ONLY:
          if parameter.default is Parameter.empty:
            raise SchemaError(f'Positional-only parameter "{parameter.name}" of {format_type(schema)} at {_path or '<root>'} is not supported')

        if parameter.kind is Parameter.VAR_POSITIONAL:
          continue

        if parameter.annotation is Parameter.empty:
          raise SchemaError(f'Parameter "{parameter.name}" of {format_type(schema)} at {_path or '<root>'} is missing a type annotation')

        check(parameter.annotation, _path=f'{_path}.{parameter.name}')

    case _:
      raise SchemaError(f'Unsupported type {format_type(schema)} at {_path or '<root>'}')
