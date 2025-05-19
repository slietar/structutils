import builtins
import dataclasses
import inspect
import json
from pprint import pprint
import sys
import types
import typing
from dataclasses import InitVar, dataclass
from types import EllipsisType, GenericAlias, UnionType
from typing import Any, Optional, Union, get_args, get_origin

from .attr_docs import get_attr_docs


def generate(type_, /, *, _parent_doc: Optional[str] = None) -> Any:
  doc_dict = dict(description=_parent_doc) if _parent_doc is not None else {}

  if get_origin(type_) is Union:
    match get_args(type_):
      case ((other_type, types.NoneType) | (types.NoneType, other_type)):
        return dict(anyOf=[
          generate(other_type),
          dict(type='null'),
        ]) | doc_dict

  match type_:
    case builtins.float:
      return dict(type='number') | doc_dict
    case builtins.int:
      # TODO: Use markdownDescription (only supported by VS Code)
      return dict(type='integer') | doc_dict
    case builtins.str:
      return dict(type='string') | doc_dict

    case types.NoneType:
      return dict(type='null') | doc_dict

    case GenericAlias(__origin__=builtins.list):
      return dict(
        type='array',
        items=generate(type_.__args__[0])
      ) | doc_dict

    case UnionType(__args__=((other_type, types.NoneType) | (types.NoneType, other_type))):
      return dict(anyOf=[
        generate(other_type),
        dict(type='null'),
      ]) | doc_dict

    case _ if inspect.isclass(type_):
      if dataclasses.is_dataclass(type_):
        fields = dataclasses.fields(type_)
        field_docs = get_attr_docs(type_)

        return dict(
          type='object',
          properties={ field.name: generate(field.type, _parent_doc=field_docs[field.name]) for field in fields },
          title=type_.__name__,
          additionalProperties=False,
          **(dict(description=type_.__doc__) if type_.__doc__ else {}),
          required=[field.name for field in fields if field.default is dataclasses.MISSING and not isinstance(field, InitVar)],
        )

      return dict(
        type='object',
        properties={},
        title=type_.__name__,
        **(dict(description=type_.__doc__) if type_.__doc__ else {}),
      )

    case _:
      return dict()


@dataclass
class A:
  x: str
  """Something"""

  y: int
  """Something else"""

  z: list[int]
  """A list of integers"""

  w: Optional[str]
  """An optional string"""

  v: Optional[list[Optional[str]]]
  """An optional list of optional strings"""

# pprint(generate(A))

json.dump(
  generate(A),
  sys.stdout,
  indent=2,
)
