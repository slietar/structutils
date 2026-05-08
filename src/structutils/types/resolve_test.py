from typing import Annotated

from .resolve import resolve


type A = int

assert resolve(A).value is int
assert resolve(Annotated[int, 'foo', 'bar']).value is int
assert resolve(Annotated[A, 'foo', 'bar']).value is int
