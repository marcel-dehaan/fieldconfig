## ConfigField
Configuration managment for Python.
Inspired by [ml_collections](https://github.com/google/ml_collections)

### Features
- Dot-Based access to fields
- Type-safe
- Field value validation
- Intermediate attribute creation
- Freezing


```
from fieldconfig import Config
from fieldconfig import Field
from fieldconfig.field import ValidationError

cfg = Config()
cfg.str = "John"
cfg.nest = Config()
cfg.nest.pos_int = Field(1, validator=lambda x: x > 0)
cfg.nest.tup = Field(None, ftype=tuple)
cfg["nest.tup"] = [1, 2]

print(cfg.to_dict())  # {'str': 'John', 'nest': {'pos_int': 1, 'tup': (1, 2)}}

try:
    cfg.str = 1
except TypeError as e:
    print(e)  # Cannot cast 1 from type float to type str

try:
    cfg.nest.pos_int = -1
except ValidationError as e:
    print(e)  # The provided value -1 (int) does not meet the criteria: lambda x: x > 0

cfg.freeze()
try:
    cfg.str = "Doe"
except ValueError as e:
    print(e)  # Config is frozen


cfg = Config(create_intermediate_attributes=True)
cfg.branch.twig.nleafs = 3
print(cfg.to_dict())  # {'branch': {'twig': {'nleafs': 3}}}
cfg.disable_intermediate_attribute_creation()
try:
    cfg.ranch.twig.color = "green"
except AttributeError as e:
    print(e)
    # Cannot add key ranch because the config has intermediate attribute
    # creation disabled. Did you mean "branch" instead of "ranch"?
```



