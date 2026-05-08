from typing import Annotated, NewType

from .resolve import resolve


type A = int
B = NewType('B', A)

assert resolve(A).value is int
assert resolve(Annotated[int, 'foo', 'bar']).value is int
assert resolve(Annotated[A, 'foo', 'bar']).value is int
assert resolve(B).value is int
