import builtins
import collections.abc
import functools
import types
import typing
from types import UnionType


def format_type(type_, /, *, use_optional: bool = False) -> str:
  format = functools.partial(format_type, use_optional=use_optional)

  if type_ is None:
    return 'None'

  if type(type_) is object:
    return 'object'

  def format_union(args):
    if (types.NoneType in args) and use_optional:
      return f'Optional[{' | '.join([format(arg) for arg in args if arg is not types.NoneType])}]'

    return f'{' | '.join(map(format, args))}'

  match typing.get_origin(type_):
    case collections.abc.Callable:
      args, return_type = typing.get_args(type_)

      if args is Ellipsis:
        return f'Callable[..., {format(return_type)}]'
      else:
        return f'Callable[[{', '.join(map(format, args))}], {format(return_type)}]'
    case typing.Union:
      return format_union(typing.get_args(type_))
    case typing.Literal:
      return f'Literal[{', '.join(map(repr, typing.get_args(type_)))}]'

  match type_:
    case builtins.float:
      return 'float'
    case builtins.int:
      return 'int'
    case builtins.str:
      return 'str'
    case builtins.Ellipsis:
      return '...'
    case types.EllipsisType:
      return 'EllipsisType'
    case types.NoneType:
      return 'None'
    case UnionType(__args__=args):
      return format_union(args)
    case _ if hasattr(type_, '__name__'):
      args = typing.get_args(type_)
      return type_.__name__ + (f'[{', '.join(map(format, args))}]' if args else '')
    case _:
      return '<unknown>'
