import builtins
import dataclasses
import functools
import inspect
import types
import typing
from dataclasses import InitVar
from enum import Enum, EnumType, Flag
from inspect import Parameter
from types import GenericAlias, UnionType
from typing import Any, Optional, TypeAliasType

from ..types.resolve import resolve
from .attr_docs import get_attr_docs
from .check import check
from .utils import optional_dict


def generate(schema, /, *, _parent_doc: Optional[str] = None, _root: bool = True) -> Any:
  if _root and __debug__:
    check(schema)

  doc_dict = optional_dict(description=_parent_doc)
  local_generate = functools.partial(generate, _root=False)

  if schema is None:
    return dict(type='null') | doc_dict

  match typing.get_origin(schema):
    case builtins.dict:
      key_schema, value_schema = typing.get_args(schema)
      resolved_key_schema = resolve(key_schema)
      print(schema, key_schema, value_schema)

      if typing.get_origin(resolved_key_schema) is typing.Literal:
        return dict(
          type='object',
          properties=({
            arg: local_generate(value_schema) for arg in typing.get_args(resolved_key_schema.value)
          }),
          additionalProperties=False,
        ) | doc_dict

      return dict(
        type='object',
        additionalProperties=local_generate(value_schema),
      ) | doc_dict

    case typing.Literal:
      args = typing.get_args(schema)

      return dict(anyOf=[
        dict(const=value, title=str(value)) | optional_dict(description=str(value)) for value in args
      ]) | doc_dict

    case typing.Union:
      match typing.get_args(schema):
        case ((other_type, types.NoneType) | (types.NoneType, other_type)):
          return dict(anyOf=[
            local_generate(other_type),
            dict(type='null'),
          ]) | doc_dict

    case TypeAliasType(__value__=value):
      return local_generate(value, _parent_doc=_parent_doc)

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

    case EnumType() if issubclass(schema, Flag):
      member_docs = get_attr_docs(schema)

      return dict(
        type='array',
        uniqueItems=True,
        items=dict(anyOf=[
          dict(const=member.name, title=member.name) | optional_dict(description=member_docs.get(member.name)) for member in schema # type: ignore
        ]),
      ) | doc_dict

    case EnumType() if issubclass(schema, Enum):
      member_docs = get_attr_docs(schema)

      return dict(anyOf=[
        dict(const=member.name, title=member.name) | optional_dict(description=member_docs.get(member.name)) for member in schema
      ]) | doc_dict

    case GenericAlias(__origin__=builtins.list):
      return dict(
        type='array',
        items=local_generate(schema.__args__[0]),
      ) | doc_dict

    case TypeAliasType():
      return local_generate(schema.__value__)

    case UnionType(__args__=((other_type, types.NoneType) | (types.NoneType, other_type))):
      return dict(anyOf=[
        local_generate(other_type),
        dict(type='null'),
      ]) | doc_dict

    case UnionType(__args__=args):
      return dict(
        anyOf=[local_generate(arg) for arg in args],
      ) | doc_dict

    case _ if inspect.isclass(schema):
      # TODO: If @final, do not allow $schema


      variants = list[dict]()

      for subclass in schema.__subclasses__():
        signature = inspect.signature(subclass)

        abort_subclass = False
        subclass_params = dict[str, dict]()

        for parameter in signature.parameters.values():
          if (parameter.kind is Parameter.POSITIONAL_ONLY) and (parameter.default is Parameter.empty):
            abort_subclass = True
            break

          subclass_params[parameter.name] = local_generate(
            parameter.annotation,
          ) if parameter.annotation is not Parameter.empty else dict()

        if abort_subclass:
          continue

        variants.append(dict(
          type='object',
          properties=(subclass_params | {
            '_target_': dict(
              const=f'{subclass.__module__}:{subclass.__qualname__}',
            ),
          }),
          title=subclass.__name__,
          additionalProperties=False,
          # required=[parameter.name for parameter in signature.parameters.values() if parameter.default is Parameter.empty and parameter.kind is Parameter.POSITIONAL_OR_KEYWORD],
        ) | optional_dict(description=subclass.__doc__))

      extra_props = {
        '$schema': dict(type='string'),
      } if _root else {}

      if dataclasses.is_dataclass(schema):
        fields = dataclasses.fields(schema)
        field_docs = get_attr_docs(schema)

        variants.append(dict(
          type='object',
          properties=(extra_props | { field.name: local_generate(field.type, _parent_doc=field_docs.get(field.name)) for field in fields }),
          title=schema.__name__,
          additionalProperties=False,
          required=[field.name for field in fields if field.default is dataclasses.MISSING and not isinstance(field, InitVar)],
        ) | optional_dict(description=schema.__doc__))
      else:
        variants.append(dict(
          type='object',
          properties=extra_props,
          title=schema.__name__,
        ) | optional_dict(description=schema.__doc__))

      if len(variants) == 1:
        return variants[0]

      return dict(
        anyOf=variants,
      )

    case _:
      print(type(schema), type(typing.get_origin(schema)))
      raise TypeError(f'Unsupported schema type: {schema!r}')
      return dict()
