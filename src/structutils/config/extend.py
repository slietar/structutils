import builtins
import dataclasses
import types
from dataclasses import dataclass
from types import EllipsisType, GenericAlias, UnionType
from typing import (Any, Generic, NewType, Optional, TypeAlias, TypeGuard,
                    TypeVar, Union, get_args, get_origin)

from ..types import format_type
from .error import InstantiationError
from .instantiate import instantiate


def extend_out_of_place(type_, data, obj, /):
  match type_:
    case _ if dataclasses.is_dataclass(type_):
      if not data:
        return obj

      fields_by_name = { field.name: field for field in dataclasses.fields(type_) }

      def map_item(name: str, value: Any):
        field = fields_by_name.get(name)

        if field is None:
          raise InstantiationError(f'Field "{name}" missing in {format_type(type_)}')

        return extend_out_of_place(field.type, value, getattr(obj, field.name))

      return dataclasses.replace(obj, **({ name: map_item(name, value) for name, value in data.items() }))

    case _:
      return instantiate(type_, data)


EXTEND_IMPOSSIBLE_SENTINEL = object()

def extend_in_place(type_, data, obj, /, *, _internal: bool = False):
  match type_:
    case _ if dataclasses.is_dataclass(type_):
      fields_by_name = { field.name: field for field in dataclasses.fields(type_) }

      for name, value in data.items():
        field = fields_by_name.get(name)

        if field is None:
          raise InstantiationError(f'Field "{name}" missing in {format_type(type_)}')

        old_value = getattr(obj, field.name)

        if extend_in_place(field.type, value, old_value, _internal=True) is EXTEND_IMPOSSIBLE_SENTINEL:
          setattr(obj, field.name, extend_out_of_place(field.type, value, old_value))

    case GenericAlias(__origin__=builtins.list):
      if not isinstance(data, list):
        raise InstantiationError(f'Expected list, got {type(data)}')

      obj.clear()
      obj.extend(instantiate(type_.__args__[0], item) for item in data)

    case _ if _internal:
      return EXTEND_IMPOSSIBLE_SENTINEL

    case _:
      raise InstantiationError('Object cannot be extended in place')
