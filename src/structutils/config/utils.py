import contextlib


@contextlib.contextmanager
def assert_raises(exception_type: type[Exception], /):
  try:
    yield
  except Exception as e:
    if not isinstance(e, exception_type):
      raise
  else:
    raise AssertionError(f'Expected {exception_type.__name__} to be raised, but no exception was raised')


def optional_dict(**kwargs):
  return { key: value for key, value in kwargs.items() if value is not None }
