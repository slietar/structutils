from dataclasses import dataclass
from enum import Enum
from typing import Annotated, Any, Literal, Optional, override

from .error import InstantiationError, SchemaError
from .instantiate import InheritedDict, InheritedDictAnn, instantiate
from .utils import assert_raises


@dataclass
class A:
  x: int
  y: str

@dataclass
class B(A):
  pass

class C:
  def __init__(self, p: int, /):
    pass

class D:
  def __init__(self, p: int = 5):
    self.p = p

  @override
  def __eq__(self, other):
    return isinstance(other, D) and (self.p == other.p)

class E:
  def __init__(self, a: int, **b: str):
    self.a = a
    self.b = b

  @override
  def __eq__(self, other):
    return isinstance(other, E) and (self.a == other.a) and (self.b == other.b)

@dataclass
class F:
  a: A

class G(A):
  def __init__(self, a: int, /):
    pass

type H = int
type I[T] = list[T]

class J(Enum):
  A = 'a'
  B = 'b'

assert instantiate(int, 3) == 3
assert instantiate(list[int], [3, 4]) == [3, 4]
assert instantiate(float, 3) == 3.0
assert isinstance(instantiate(float, 3), float)
assert instantiate(int | None, None) is None
assert instantiate(int | None, 3) == 3
assert instantiate(Optional[int], None) is None
assert instantiate(A, dict(x=3, y='4')) == A(3, '4')
assert instantiate(A, dict(_target_='B', x=3, y='4')) == B(3, '4')
assert instantiate(D, dict()) == D()
assert instantiate(D, dict(p=6)) == D(p=6)
assert instantiate(A, dict(x=5), dict(x=3, y='4')) == A(5, '4')
assert instantiate(Optional[A], dict(x=5), None, dict(x=3, y='4')) == A(5, '4')
assert instantiate(Optional[A], None, dict(x=3, y='4')) is None
assert instantiate(Literal['a', 3], 'a') == 'a'
assert instantiate(A, dict(_target_='B', x=3, y='4'), dict(x=5)) == B(x=3, y='4')
assert instantiate(E, dict(a=3)) == E(a=3)
assert instantiate(E, dict(a=3, x='1')) == E(a=3, x='1')
assert instantiate(E, dict(a=3), dict(x='1')) == E(a=3, x='1')
assert instantiate(Optional[F], None, dict(a=dict(x=3))) is None
assert instantiate(Any, 3, 'a') == 3
assert instantiate(dict[str, int], {'a': 3, 'b': 4}, {'c': 5}) == {'a': 3, 'b': 4}
assert instantiate(Annotated[int, 'foo'], 3) == 3
assert instantiate(Annotated[dict[str, int], InheritedDictAnn], {'a': 3, 'b': 4}, {'c': 5}) == {'a': 3, 'b': 4, 'c': 5}
assert instantiate(InheritedDict[str, int], {'a': 3, 'b': 4}, {'c': 5}) == {'a': 3, 'b': 4, 'c': 5}
assert instantiate(H, 3) == 3
assert instantiate(I[int], [3, 4]) == [3, 4]
assert instantiate(J, 'a') == J.A
# print(instantiate(Factory[A], dict(x=3, y='4')))
# assert instantiate(Factory[A], dict(x=3, y='4'))() == A(3, '4')
# assert instantiate(Annotated[type[A], FactoryDelayedArgs(0, 'x', 'y')], dict(x=3))(y='4') == A(3, '4')
assert instantiate(None, None) is None
assert instantiate(bool, True) is True


with assert_raises(InstantiationError):
  instantiate(list[int], [3, 4.0])

with assert_raises(SchemaError):
  assert instantiate(list[int | str], [3, '4']) == [3, '4']

with assert_raises(InstantiationError):
  instantiate(A, dict(x=3))

with assert_raises(InstantiationError):
  instantiate(A, dict(x=3, y=4))

with assert_raises(InstantiationError):
  instantiate(A, dict(x=3, y='4', z=5))

with assert_raises(SchemaError):
  instantiate(C, dict())

with assert_raises(InstantiationError):
  instantiate(Literal['a', 3], 'b')

with assert_raises(InstantiationError):
  instantiate(Optional[int], None, 'a')

with assert_raises(InstantiationError):
  instantiate(A, dict(_target_='B', x=3, y='4'), dict(x='5'))

with assert_raises(InstantiationError):
  instantiate(E, dict(a=3, x=1))

with assert_raises(InstantiationError):
  instantiate(E, dict(a=3), dict(x=1))

with assert_raises(InstantiationError):
  instantiate(E, dict(a=3), dict(x='1'), dict(x=1))

with assert_raises(InstantiationError):
  instantiate(A, dict(_target_='B', x=3))

with assert_raises(InstantiationError):
  instantiate(A, dict(_target_='G'))

with assert_raises(SchemaError):
  instantiate(dict[A, int], {})

with assert_raises(InstantiationError):
  instantiate(dict[str, int], {3: 4})

with assert_raises(InstantiationError):
  instantiate(J, 'c')

with assert_raises(InstantiationError):
    assert instantiate(bool, 1) is True
