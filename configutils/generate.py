import builtins
import dataclasses
import inspect
import json
import sys
import types
import typing
from dataclasses import InitVar, dataclass
from types import GenericAlias, UnionType
from typing import Any, Optional, Union

from .attr_docs import get_attr_docs


def generate(schema, /, *, _parent_doc: Optional[str] = None) -> Any:
  doc_dict = dict(description=_parent_doc) if _parent_doc is not None else {}

  if typing.get_origin(schema) is Union:
    match typing.get_args(schema):
      case ((other_type, types.NoneType) | (types.NoneType, other_type)):
        return dict(anyOf=[
          generate(other_type),
          dict(type='null'),
        ]) | doc_dict

  match schema:
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
        items=generate(schema.__args__[0])
      ) | doc_dict

    case UnionType(__args__=((other_type, types.NoneType) | (types.NoneType, other_type))):
      return dict(anyOf=[
        generate(other_type),
        dict(type='null'),
      ]) | doc_dict

    case _ if inspect.isclass(schema):
      if dataclasses.is_dataclass(schema):
        fields = dataclasses.fields(schema)
        field_docs = get_attr_docs(schema)

        return dict(
          type='object',
          properties={ field.name: generate(field.type, _parent_doc=field_docs[field.name]) for field in fields },
          title=schema.__name__,
          additionalProperties=False,
          **(dict(description=schema.__doc__) if schema.__doc__ else {}),
          required=[field.name for field in fields if field.default is dataclasses.MISSING and not isinstance(field, InitVar)],
        )

      return dict(
        type='object',
        properties={},
        title=schema.__name__,
        **(dict(description=schema.__doc__) if schema.__doc__ else {}),
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
