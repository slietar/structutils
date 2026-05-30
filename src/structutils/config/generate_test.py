import json
import sys
from dataclasses import dataclass
from typing import Literal

from .generate import generate


@dataclass
class A:
  x: dict[str, B[int]]

type B[T] = T

type C = dict[Literal['a', 'b', 'c'], int]


for schema in [
    A,
    C,
    list[int] | int,
]:
    json.dump(
        generate(C),
        sys.stdout,
        indent=4,
    )

    sys.stdout.write('\n\n')
