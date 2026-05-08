from collections.abc import Iterable
from typing import Annotated, Any, Optional, overload

from .check import check
from .error import SchemaError
from .utils import assert_raises


class A:
  pass

class B:
  pass

class C:
  @overload
  def __init__(self, a: A):
    pass

  @overload
  def __init__(self, a: B):
    pass

  def __init__(self, a):
    pass

class D:
  def __init__(self, a: A):
    pass

class E:
  def __init__(self, a: Optional[A]):
    pass

check(A)
check(A | B)
check(C)
check(D)
check(Optional[A | B])
check(Any)
check(E)
check(dict[Annotated[str, 'foo'], Any])

with assert_raises(SchemaError):
  check(Iterable[A])

with assert_raises(SchemaError):
  check(dict[int, Any])
