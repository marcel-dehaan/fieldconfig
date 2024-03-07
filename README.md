## FieldConfig
FieldConfig is a configuration management library for Python.

### **Features:**
- Dot-based access
  - `config.a.b`
  - `config["a.b"]`
- Type-safe (flag)
  - Secure casting
  - Top-level type enforcement
- User-defined validation function
  - Supports arbitrary complexity
- Freezing (toggle)
  - Renders the configuration read-only
- Locking (toggle)
  - Prevents extending the configuration
- Intermediate attribute creation (toggle)
  - Reduces boilerplate code


## Table of Contents

- [Installation](#installation)
- [Configuration Stucture](#configuration-structure)
- [Usage](#usage)
  - [Update Method](#update-method)
  - [Locking](#locking)
  - [Freezing](#freezing)
  - [Intermediate Attribute Creation](#intermediate-attribute-creation)
- [Upcoming Features](#upcoming-features)

<a id="installation"></a>
## Installation
```python
pip install fieldconfig
```

<a id="configuration-structure"></a>
## Configuration Structure
Configurations generated using FieldConfig are structured as branches composed of Config objects and leaves populated with Fields. The Config object governs mutability, allowing for actions such as Freezing, Locking, and Intermediate attribute creation, as well as type-safety of all its Fields. Fields, on the other hand, can enforce value validation through user-defined functions and retain information about the field type.

FieldConfig is heavily inspired by [ml_collections](https://github.com/google/ml_collections). However, it provides an optional Field validation mechanism allowing any validation function, preventing misuse beyond the default top-level type checking. This is particularly beneficial for configurations exposed to and updatable by external users. Additionally, its intermediate attribute creation mechanism avoids boilerplate code when defining nested configurations.

<a id="usage"></a>
## Usage
### Overview
Let's generate a configuration object, populate it through different methods, and then examine its structure.
```python
from fieldconfig import Config, Field

config = Config({"int": 1})
config.str = "John"
config.nest = Config()
config.nest.tup = Field(None, ftype=tuple)
config.nest.tup = [1, "one"]
config.nest.pos_int = Field(1, validator=lambda x: x > 0)
config["nest.float"] = 3.5

print(config.nest.float)
# --> 3.5

# peek under the hood, note the field-type is inferred
print(config.nest._fields["float"])
# --> Field(default=3.5, ftype=<class 'float'>, validator=None, required=False)

print(config.to_dict())
# --> {'int': 1, 'str': 'John', 'nest': {'tup': (1, 2), 'pos_int': 1, 'float': 3.5}}

print(config.to_flat_dict())
# --> {'int': 1, 'str': 'John', 'nest.tup': (1, 'one'), 'nest.pos_int': 1, 'nest.float': 3.5}
```

The code snippet above demonstrates:
- Configuration objects can be filled by providing a (nested) mapping during instantiation or by extending them after creation through dot or item assignment. 
- Internally, values are encapsulated within a field, with automatic inference of the value type unless explicitly passed. This inference is maintained unless the Config is instantiated with the `type_safe` flag set to `False`.
- Values that can be safely cast to the field type will automatically do so, as demonstrated by the assignment of a list to 'nest.tup'.

Lets test the enforcements imposed by this configuration object.
```python
from fieldconfig.field import ValidationError

try:
    config.str = 1.5
except TypeError as e:
    print(e)  
    # --> Cannot cast 1 from type float to type str

try:
    config.nest.pos_int = -1
except ValidationError as e:
    print(e)  
    # -->  The provided value -1 (int) does not meet the criteria: 
    # -->         lambda x: x > 0
```
<a id="update-method"></a>
### Update Method
In addition to the demonstrated field overrides, a config object can be updated using its `update` method. It accepts both nested or flat Mappings. Config objects can be passed as well since they adhere to the Mapping protocol.

```python
import inspect

# Cleanup for clarity, works with both getitem and getattr.
del config.int
del config["nest.tup"]

config.update({"str": "Doe", "nest.pos_int": 2, "new": "foo"})
config.update(Config({"nest": {"float": 4.5}}))

print(config.to_flat_dict())
# --> {'str': 'Doe', 'nest.pos_int': 2, 'nest.float': 4.5, 'new': 'foo'}

# note validation is upheld during updates of field values
print(inspect.getsource(config.nest._fields["pos_int"]._validator))
# --> config.nest.pos_int = Field(1, validator=lambda x: x > 0)
```
<a id="locking"></a>
### Locking
A locked configuration has an immutable structure but permits updates to individual fields.
```python
config = Config()
config.foo = "bar"

config.lock()
assert config.is_locked()

config.foo = "xyz"  # this works

try:
    config.foot = "bar"
except ValueError as e:
    print(e)
    # --> ValueError: Cannot add key foot because the config is locked.
    # --> Did you mean "foo" instead of "foot"?

try:
    del config.foo
except AttributeError as e:
    print(e)
    # --> AttributeError: 'This Config is locked, you have to unlock it before trying to delete a field.'

config.unlock()
assert not config.is_locked()
```
<a id="freezing"></a>
### Freezing
Freezing a configuration renders it read-only. 
```python
config = Config()
config.freeze()
assert config.is_frozen()


try:
    cfg.str = "Doe"
except ValueError as e:
    print(e)  
    # --> Config is frozen
```
<a id="intermediate-attribute-creation"></a>
### Intermediate Attribute Creation
Enable intermediate attribute creation to skip the incremental construction of nested structures. Use this feature at your own peril.
```python
config = Config(create_intermediate_attributes=True)
config.branch.twig.leaf = True
config.radicle.branch.offshoot = False

print(config.to_dict())
# --> {'branch': {'twig': {'leaf': True}}, 'radicle': {'branch': {'offshoot': False}}}

config.disable_intermediate_attribute_creation()
```
<a id="upcoming features"></a>
### Upcoming Features
- serialization 