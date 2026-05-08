class InstantiationError(Exception):
  pass

class SchemaError(Exception):
  pass

class SchemaErrorGroup(ExceptionGroup, SchemaError):
  pass
