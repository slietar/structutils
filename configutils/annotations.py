from typing import Annotated


class ExactAnnType:
  pass

ExactAnn = ExactAnnType()

type Exact[T] = Annotated[T, ExactAnn]
