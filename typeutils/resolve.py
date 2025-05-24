import functools
import operator
import typing
from dataclasses import dataclass
from typing import Annotated, Any, Optional, TypeAlias, TypeAliasType, TypeVar


@dataclass(frozen=True, slots=True)
class ResolvedType:
  annotations: tuple[Any, ...]
  value: Any

def resolve(schema, /):
  match typing.get_origin(schema):
    case typing.Annotated:
      resolved = resolve(typing.get_args(schema)[0])

      return ResolvedType(
        annotations=(*resolved.annotations, *schema.__metadata__),
        value=resolved.value,
      )

    # case typing.Union:
    #   return resolve(
    #     functools.reduce(operator.or_, typing.get_args(schema)),
    #   )

    case TypeAliasType(__value__=value):
      return resolve(value[*typing.get_args(schema)])

  match schema:
    case TypeAliasType():
      return resolve(schema.__value__)

    # case TypeVar():
    #   raise TypeError(f'TypeVar {schema} cannot be resolved')

  return ResolvedType(
    annotations=(),
    value=schema,
  )
