import builtins
import inspect
import types
import typing
from inspect import Parameter
from types import GenericAlias, UnionType
from typing import Union

from typeutils.format import format_type

from .error import SchemaError


def check(schema, /, *, _path: str = ''):
  match typing.get_origin(schema):
    case typing.Union:
      match typing.get_args(schema):
        case ((other_type, types.NoneType) | (types.NoneType, other_type)):
          check(other_type, _path=_path)
          return

    case typing.Literal:
      return

  match schema:
    case builtins.float | builtins.int | builtins.str | types.NoneType | typing.Any:
      pass

    case GenericAlias(__origin__=builtins.list):
      check(schema.__args__[0], _path=f'{_path}[]')

    case UnionType(__args__=((other_type, types.NoneType) | (types.NoneType, other_type))):
      check(other_type, _path=_path)

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
