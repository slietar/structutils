import functools
import importlib
from typing import Any


@functools.cache
def _get_regex(*, allow_modules: bool = False):
  import re

  name = r'[a-z_]\w*(?:\.[a-z_]\w*)*'
  return re.compile(rf'^{name}(?::{name}){'?' if allow_modules else ''}$', flags=re.IGNORECASE)

def load(specifier: str, /, *, allow_modules: bool) -> Any:
  """
  Raises
    ImportError
  """

  if __debug__ and not _get_regex(allow_modules=allow_modules).match(specifier):
    raise ImportError(f'Invalid specifier "{specifier}"')

  parts = specifier.split(':', maxsplit=1)
  module = importlib.import_module(parts[0])

  current_value = module

  if len(parts) == 2:
    for name_part in parts[1].split('.'):
      if hasattr(current_value, name_part):
        current_value = getattr(current_value, name_part)
      else:
        raise ImportError(f'Cannot find {name_part} in {parts[0]}')

  return current_value
