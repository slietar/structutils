import json
import sys
from dataclasses import dataclass

from .generate import generate


@dataclass
class A:
  x: dict[str, str]


json.dump(
    generate(A),
    sys.stdout,
    indent=2,
)
