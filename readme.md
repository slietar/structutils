# Structutils

Structutils is a Python library for working with structured data.

It supports Python 3.14 and later.


## Installation

Structutils is available on PyPI under the name `pstructutils`.


## Types

### Inferring a type form from a value

```py
import structutils

structutils.infer_type([1, 2, 3]) # => list[int]
```

### Formatting a type form

```py
import structutils

structutils.format_type(list[int]) # => 'list[int]'
```


## Configuration

### Creating and validating a schema

```py
import structutils

@dataclass
class User:
  age: int
  name: str

type Users = list[User]

try:
  structutils.check(Users)
except structutils.SchemaError as e:
  print(f"Invalid schema: {e}")
```

### Generating a JSON schema from a schema

```py
import structutils

with Path('schema.json').open('w') as file:
  json.dump(structutils.generate(Users), file)
```

### Instantiating data using a schema

```py
import structutils

with Path('data.json').open() as file:
  raw_data = json.load(file)

try:
  data = structutils.instantiate(Users, raw_data)
except structutils.InstantiationError as e:
  print(f"Invalid data: {e}")
```


## Miscellaneous

### Loading an object from a string specifier

```py
import structutils

pathlib = structutils.load('pathlib', allow_modules=True)
Iterable = structutils.load('collections.abc:Iterable')
```


<!-- ### Designing and generating a schema

Supported Python types are:

- **Basic types** – `float`, `int`, `str`, `bool`, `None`
- **List-like collections** – `Iterable`, `list`, `tuple`

  These are implemented as an array.

- **Map-like collections** – `Mapping`, `dict`

  These are implemented as an object limited to string keys.

- **Sets** – `frozenset`, `set`

  These are implemented as an array with a uniqueness constraint.

- `Enum` – implemented as a string corresponding to the enum member name
- `Flag` – implemented as a list of strings corresponding to the flag member names
- **Classes** – implemented as an object used to call `__init__` on the class

  The class' positional-only parameters must have a default value, and all other parameters must have type annotations. It is the only type that will be merged if multiple data sources are provided.

  A subclass can be specified using a property with the `$class` key in the data source. The value of this property must be of the form `<module name>:<class qualified name>`, or `<class name>` if the subclass was registered with a unique name at generation or instantiation time.

```py
import json
from abc import ABC
from dataclasses import dataclass
from enum import IntEnum
from pathlib import Path

from structutils.config import SchemaError, check, generate

@dataclass
class NetworkConfig:
  address: str
  port: int

class Mode(IntEnum):
  Development = 0
  Production = 1

class UserBase(ABC):
  pass

@dataclass
class RegularUser(UserBase):
  name: str
  age: int

@dataclass
class AdminUser(UserBase):
  name: str
  permissions: set[str]

@dataclass
class Config:
  mode: Mode
  network: NetworkConfig
  users: list[UserBase]
  version: Literal['1.0', '2.0']

# To check the schema
try:
  check(Config)
except SchemaError as e:
  print(f"Invalid schema: {e}")

# To generate a JSON schema
with Path('config-schema.json').open('w') as ifle:
  json.dump(generate(Config), file, indent=2)
```

### Writing data

```json
{
  "$schema": "config-schema.json",
  "mode": "Development",
  "network": {
    "address": "127.0.0.1",
    "port": 8080
  },
  "users": [
    {
      "$class": "RegularUser",
      "name": "Alice"
    },
    {
      "$class": "AdminUser",
      "name": "Bob",
      "permissions": ["read", "write"]
    }
  ],
  "version": "1.0"
}
```

### Reading data

```py
from structutils.config import InstantiationError, instantiate

with Path('config.json').open() as file:
  raw_config = json.load(file)

try:
  config = instantiate(Config, raw_config)
except InstantiationError as e:
  print(f"Invalid data: {e}")
except SchemaError as e:
  print(f"Invalid schema: {e}")
```



```py
@dataclass
class Config:
  optimizer: InferSubclasses[Optimizer]
  optimizer: Unchecked[Optimizer]
  optimizer: Exact[Optimizer] # Same as if Optimizer is @final
```

-->
