import builtins
import collections.abc
import functools
import types
import typing
from types import EllipsisType, NoneType, UnionType
from typing import Callable, Generic, Literal, NewType, Optional, TypeVar


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


T = TypeVar('T')

class A(Generic[T]):
  pass

B = NewType('B', int)


assert format_type(int) == 'int'
assert format_type(list[int]) == 'list[int]'
assert format_type(list[int | str]) == 'list[int | str]'
assert format_type(list[int | str | None]) == 'list[int | str | None]'
assert format_type(list[int | str | None], use_optional=True) == 'list[Optional[int | str]]'
assert format_type(set[int]) == 'set[int]'
assert format_type(frozenset[int]) == 'frozenset[int]'
assert format_type(tuple[int, str]) == 'tuple[int, str]'
assert format_type(tuple[int, ...]) == 'tuple[int, ...]'
assert format_type(EllipsisType) == 'EllipsisType'
assert format_type(A) == 'A'
assert format_type(A[int]) == 'A[int]'
assert format_type(A[T]) == 'A[T]' # type: ignore
assert format_type(A[int | str]) == 'A[int | str]'
assert format_type(B) == 'B'
assert format_type(Optional[int]) == 'int | None'
assert format_type(Literal['a', 3]) == '''Literal['a', 3]'''
assert format_type(type[A]) == 'type[A]'
assert format_type(None) == 'None'
assert format_type(NoneType) == 'None'
assert format_type(Callable[[int, int], str]) == 'Callable[[int, int], str]'
assert format_type(Callable[..., str]) == 'Callable[..., str]'
