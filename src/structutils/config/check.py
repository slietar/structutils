import builtins
import inspect
import itertools
import types
import typing
from enum import Enum, EnumType, Flag
from inspect import Parameter
from types import GenericAlias, UnionType

from src.structutils.types.format import format_type
from src.structutils.types.resolve import resolve

from .annotations import ExactAnn
from .error import SchemaError


def is_string_type(schema):
  match typing.get_origin(schema):
    case typing.Literal:
      return all(isinstance(arg, str) for arg in typing.get_args(schema))

  match schema:
    case builtins.str:
      return True

    case _:
      return False

def check(schema_raw, /, *, _path: str = ''):
  resolved = resolve(schema_raw)
  schema = resolved.value
  annotations = resolved.annotations

  if schema is None:
    return

  match typing.get_origin(schema):
    case typing.Literal:
      return

    case typing.Union:
      for arg in typing.get_args(schema):
        check(arg, _path=_path)

      return


  match schema:
    case builtins.bool | builtins.float | builtins.int | builtins.str | types.NoneType | typing.Any:
      pass

    case GenericAlias(__origin__=builtins.dict, __args__=(key_schema, value_schema)):
      resolved_key_schema = resolve(key_schema).value

      if not is_string_type(resolved_key_schema):
        raise SchemaError(f'Unsupported key type {format_type(key_schema)}')

      check(value_schema, _path=f'{_path}[]')
      return

    case GenericAlias(__origin__=builtins.list, __args__=(item_schema,)):
      check(item_schema, _path=f'{_path}[]')

    # Not strictly necessary
    case typing.Any:
      return

    case UnionType(__args__=args):
      for arg in args:
        check(arg, _path=_path)

    # Not strictly necessary as enums are classes anyway
    case EnumType() if issubclass(schema, (Enum, Flag)):
      pass

    case _ if inspect.isclass(schema):
      exact_ann = any(ann is ExactAnn for ann in annotations)

      if inspect.isabstract(schema) or typing.is_protocol(schema):
        if exact_ann:
          raise SchemaError(f'Exact annotation is not allowed for abstract or protocol class {format_type(schema)} at {_path or "<root>"}')
      else:
        if hasattr(schema.__init__, '__module__'):
          functions = typing.get_overloads(schema.__init__) or [schema.__init__]
          skip_self = True
        else:
          functions = [schema]
          skip_self = False

        for function in functions:
          type_hints = typing.get_type_hints(function, include_extras=True)
          signature = inspect.signature(function)

          for parameter in itertools.islice(signature.parameters.values(), 1 if skip_self else 0, None):
            if parameter.kind is Parameter.POSITIONAL_ONLY:
              if parameter.default is Parameter.empty:
                raise SchemaError(f'Positional-only parameter "{parameter.name}" of {format_type(schema)} at {_path or '<root>'} has no default value')

              continue

            if parameter.kind is Parameter.VAR_POSITIONAL:
              continue

            # Type hints can also be missing in other cases such as @no_type_check
            if parameter.name not in type_hints:
              if parameter.default is Parameter.empty:
                raise SchemaError(f'Parameter "{parameter.name}" of {format_type(schema)} at {_path or '<root>'} is missing a type annotation or a default value')

              continue

            check(type_hints[parameter.name], _path=f'{_path}.{parameter.name}')

    case _:
      raise SchemaError(f'Unsupported type {format_type(schema)} at {_path or '<root>'}')
