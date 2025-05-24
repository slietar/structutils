import typing
from typing import Annotated, Any, Iterable, Optional

from .check import check
from .error import SchemaError
from .utils import assert_raises


class A:
  pass

class B:
  pass

class C:
  @typing.overload
  def __init__(self, a: A):
    pass

  @typing.overload
  def __init__(self, a: B):
    pass

  def __init__(self, a):
    pass

class D:
  def __init__(self, a: 'A'):
    pass

class E:
  def __init__(self, a: 'Optional[A]'):
    pass

check(A)
check(A | B)
check(C)
check(D)
check(Optional[A | B])
check(Any)
# check(Iterable[A])
# check(E)
check(dict[Annotated[str, 'foo'], Any])

with assert_raises(SchemaError):
  check(dict[int, Any])
