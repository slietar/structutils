import builtins
import inspect
import types
import typing
from inspect import Parameter
from types import GenericAlias, UnionType
from typing import Union

from typeutils.format import format_type


def check(schema, /):
  if typing.get_origin(schema) is Union:
    match typing.get_args(schema):
      case ((other_type, types.NoneType) | (types.NoneType, other_type)):
        check(other_type)

  match schema:
    case builtins.float | builtins.int | builtins.str | types.NoneType:
      return

    case GenericAlias(__origin__=builtins.list):
      check(schema.__args__[0])

    case UnionType(__args__=((other_type, types.NoneType) | (types.NoneType, other_type))):
      check(other_type)

    case _ if inspect.isclass(schema):
      signature = inspect.signature(schema)

      for parameter in signature.parameters.values():
        if parameter.kind is Parameter.POSITIONAL_ONLY:
          if parameter.default is Parameter.empty:
            raise ValueError(f'Positional-only parameter "{parameter.name}" of {format_type(schema)} is not supported')

        if parameter.kind is Parameter.VAR_POSITIONAL:
          continue

        if parameter.annotation is Parameter.empty:
          raise ValueError(f'Parameter "{parameter.name}" of {format_type(schema)} is missing a type annotation')

        check(parameter.annotation)

    case _:
      raise ValueError(f'Unsupported type {format_type(schema)}')
