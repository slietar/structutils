import builtins
import dataclasses
import types
from dataclasses import dataclass
from types import EllipsisType, GenericAlias, UnionType
from typing import (Any, Generic, NewType, Optional, TypeAlias, TypeGuard,
                    TypeVar, Union, get_args, get_origin)

from .attr_docs import get_attr_docs


def generate(type_, /, *, _parent_doc: Optional[str] = None):
	doc_dict = dict(description=_parent_doc) if _parent_doc is not None else {}

	match type_:
		case builtins.float:
			return dict(type='number') | doc_dict
		case builtins.int:
			# TODO: Use markdownDecsription (only supported by VS Code)
			return dict(type='integer') | doc_dict
		case builtins.str:
			return dict(type='string') | doc_dict

		case GenericAlias(__origin__=builtins.list):
			return dict(
				type='array',
				items=generate(type_.__args__[0])
			) | doc_dict

		case _ if dataclasses.is_dataclass(type_):
			fields = dataclasses.fields(type_)
			field_docs = get_attr_docs(type_)

			return dict(
				type='object',
				properties={ field.name: generate(field.type, _parent_doc=field_docs[field.name]) for field in fields },
				title=type_.__name__,
				description=type_.__doc__,
			)
