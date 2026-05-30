class InstantiationError(Exception):
  pass

class SchemaError(Exception):
  pass

class InstantiationErrorGroup(ExceptionGroup, InstantiationError):
  pass
