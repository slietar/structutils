from types import EllipsisType, NoneType
from typing import Callable, Generic, Literal, NewType, Optional, TypeVar

from .format import format_type


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
