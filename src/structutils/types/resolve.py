from annotationlib import ForwardRef
import functools
import operator
import typing
from dataclasses import dataclass
from types import UnionType
from typing import Any, NewType, TypeAliasType, TypeVar

from ..config.error import SchemaError
from .format import format_type


@dataclass(frozen=True, slots=True)
class ResolvedType:
  annotations: tuple[Any, ...]
  value: Any

def resolve(schema, /, *, allow_unspecialized: bool = False) -> ResolvedType:
  match typing.get_origin(schema):
    case typing.Annotated:
      resolved = resolve(typing.get_args(schema)[0])

      return ResolvedType(
        annotations=(*resolved.annotations, *schema.__metadata__),
        value=resolved.value,
      )

    case TypeAliasType(__value__=value):
      if isinstance(value, TypeVar):
        type_var_index = schema.__type_params__.index(value)

        return ResolvedType(
          annotations=(),
          value=typing.get_args(schema)[type_var_index],
        )

      return resolve(value[*typing.get_args(schema)])

  match schema:
    case ForwardRef():
      return resolve(schema.evaluate())

    case TypeAliasType(__value__=value):
      if not schema.__type_params__:
        return resolve(value)

      if not allow_unspecialized:
        raise SchemaError(f'Cannot resolve unspecialized type alias {format_type(schema)}')

      if isinstance(value, TypeVar):
        return ResolvedType(
          annotations=(),
          value=typing.Any,
        )

      return resolve(value[(typing.Any,) * len(schema.__type_params__)])
    case NewType():
      return resolve(schema.__supertype__)
    case UnionType(__args__=args):
      return ResolvedType(
        annotations=(),
        value=functools.reduce(
          operator.or_,
          (resolve(arg).value for arg in args),
        ),
      )

  return ResolvedType(
    annotations=(),
    value=schema,
  )
