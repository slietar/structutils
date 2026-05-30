from typing import Annotated, Any, NewType

from ..config.error import SchemaError
from ..config.utils import assert_raises
from .resolve import resolve


type A = int
type B[T] = T
type C[T] = list[T]
type D[T] = T | int
type E[T, S] = T | S

F = NewType('F', A)

assert resolve(A).value is int
assert resolve(Annotated[int, 'foo', 'bar']).value is int
assert resolve(Annotated[A, 'foo', 'bar']).value is int
assert resolve(B, allow_unspecialized=True).value is Any
assert resolve(B[int]).value is int
assert resolve(C[int]).value == list[int]
assert resolve(B[int]).value is int
assert resolve(B[int] | B[str]).value == int | str
assert resolve(D[str]).value == int | str
assert resolve(E[int, str]).value == int | str
assert resolve(F).value is int

with assert_raises(SchemaError):
    resolve(B, allow_unspecialized=False)
