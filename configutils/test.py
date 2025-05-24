from typing import Any, Iterable, Optional
import typing

from .check import check


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
