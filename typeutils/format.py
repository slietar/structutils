import builtins
import functools
import types
from types import EllipsisType, UnionType
from typing import (Generic, NewType, Optional, TypeVar, Union, get_args,
                    get_origin)


def format_type(type_, /, *, use_optional: bool = False):
  format = functools.partial(format_type, use_optional=use_optional)

  def format_union(args):
    if (types.NoneType in args) and use_optional:
      return f'Optional[{' | '.join([format(arg) for arg in args if arg is not types.NoneType])}]'

    return f'{' | '.join(map(format, args))}'

  if get_origin(type_) is Union:
    args = get_args(type_)
    return format_union(get_args(type_))

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
    case _:
      args = get_args(type_)
      return type_.__name__ + (f'[{', '.join(map(format, args))}]' if args else '')


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
