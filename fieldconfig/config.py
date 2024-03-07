from typing import Any, Mapping, Optional
import yaml
import difflib
from fieldconfig.field import Field


class Config(Mapping):
    def __init__(
        self,
        data: Optional[Mapping[str, Any]] = None,
        type_safe=True,
        create_intermediate_attributes: bool = False,
    ):
        super(Config, self).__setattr__("_fields", {})
        super(Config, self).__setattr__("_type_safe", type_safe)
        super(Config, self).__setattr__("_frozen", False)
        super(Config, self).__setattr__("_locked", False)
        super(Config, self).__setattr__(
            "_create_intermediate_attributes",
            create_intermediate_attributes,
        )

        if data:
            _fill_config_from_mapping(self, mapping=data)

    def copy(self):
        config_copy = self.__class__()
        for key, value in self._fields.items():
            if isinstance(value, Field | Config):
                value = value.copy()
            config_copy[key] = value

        super(Config, config_copy).__setattr__("_frozen", self._frozen)
        super(Config, config_copy).__setattr__("_type_safe", self._type_safe)
        super(Config, config_copy).__setattr__("_locked", self._locked)

        super(Config, config_copy).__setattr__(
            "_create_intermediate_attributes",
            self._create_intermediate_attributes,
        )
        return config_copy

    def __delitem__(self, key):
        if self.is_locked():
            raise KeyError(
                "This Config is currently locked. Please unlock it "
                "before attempting to delete a field."
            )

        if "." in key:
            key, rest = key.split(".", 1)
            del self[key][rest]
            return

        try:
            del self._fields[key]
        except KeyError as e:
            raise KeyError(_suggest_alternative(key, self._fields), e)

    def to_dict(self):
        return _config_to_dict(self)

    def to_flat_dict(self):
        return _config_to_flat_dict(self)

    def items(self):
        return self._fields.items()

    def keys(self):
        return sorted(list(self._fields.keys()))

    def freeze(self):
        """Freezes the configuration, making it read-only."""
        super(Config, self).__setattr__("_frozen", True)

    def enable_intermediate_attribute_creation(self):
        """Enables automatic generation of intermediaries."""
        super(Config, self).__setattr__("_create_intermediate_attributes", True)

    def disable_intermediate_attribute_creation(self):
        """Disables automatic generation of intermediaries."""
        super(Config, self).__setattr__("_create_intermediate_attributes", False)

    def is_intermediate_attribute_creation_enabled(self):
        return self._create_intermediate_attributes

    def lock(self):
        super(Config, self).__setattr__("_locked", True)

    def unlock(self):
        super(Config, self).__setattr__("_locked", False)

    def is_locked(self):
        return self._locked

    def is_frozen(self):
        return self._frozen

    def update(self, updates: Mapping[str, Any]):
        for k, v in updates.items():
            if k not in self._fields:
                self[k] = v

            elif isinstance(self._fields[k], Config) and isinstance(v, Mapping):
                self._fields[k].update(v)

            else:
                self[k] = v

    def is_type_safe(self):
        return self._type_safe

    def __iter__(self):
        return self._fields.__iter__()

    def __len__(self):
        return len(self._fields)

    def __contains__(self, key):
        return key in self._fields

    def __setitem__(self, key, value):
        config = self
        frozen = self._frozen
        locked = self._locked
        if "." in key:
            keys = key.split(".")
            for key in keys[:-1]:
                config = getattr(config, key)
                frozen = frozen or config.is_frozen()
                locked = locked or config.is_locked()

            key = keys[-1]

        if frozen:
            raise ValueError("Config is frozen")
        if key in config._fields:
            field = config._fields[key]
            if isinstance(field, Config):
                if isinstance(value, Mapping):
                    config._fields[key] = Config(value)
                else:
                    raise TypeError(
                        f"Failed to override field '{key}' with value '{value}' "
                        f"of type '{type(value)}'. The field '{key}' must be "
                        "assigned a value of type 'Mapping'."
                    )
            field.set(value, config._type_safe)
        else:
            if locked:
                msg = f"Cannot add key {key} because the config is locked."
                msg = _suggest_alternative(key, config._fields, msg)
                raise ValueError(msg)

            if isinstance(value, Config | Field):
                config._fields[key] = value
            else:

                config._fields[key] = Field(value)

    def _ensure_mutability(self, attribute):
        if attribute in dir(super(Config, self)):
            raise KeyError(f"{attribute} cannot be overridden.")

    def __setattr__(self, attribute, value):
        try:
            self._ensure_mutability(attribute)
            self[attribute] = value
        except KeyError as e:
            raise AttributeError(e)

    def __delattr__(self, attribute):
        try:
            self._ensure_mutability(attribute)
            del self[attribute]
        except KeyError as e:
            raise AttributeError(e)

    def __getitem__(self, key: str):
        if "." in key:
            key, rest = key.split(".", 1)
            return self[key][rest]

        if key in self._fields:
            field = self._fields[key]
            if isinstance(field, Field):
                return field.get()
            else:
                return field

        if self._frozen or not self._create_intermediate_attributes:
            reason = (
                "is frozen"
                if self._frozen
                else "has intermediate attribute creation disabled"
            )
            msg = f"Cannot add key {key} because the config {reason}."
            msg = _suggest_alternative(key, self._fields, msg)
            raise KeyError(msg)
        self._fields[key] = Config(create_intermediate_attributes=True)
        return self._fields[key]

    def __getattr__(self, attribute):
        try:
            return self[attribute]
        except KeyError as e:
            raise AttributeError(e)

    def __str__(self):
        try:
            return yaml.dump(_config_to_dict(self))
        except Exception:
            return str(_config_to_dict(self))

    def __repr__(self):
        return self.__str__()


def _config_to_dict(config: Config) -> dict:
    """
    Convert a Config object to a dictionary representation recursively.

    This function recursively converts a Config object and its nested
    Config objects into a dictionary. It includes only public
    attributes and their corresponding values.

    Args:
        config (Config): The Config object to be converted.

    Returns:
        dict: A dictionary representing the Config object.
    """
    config_dict = {}
    for key in config:
        if key.startswith("_"):
            continue
        if isinstance(config._fields[key], Config):
            value = _config_to_dict(config._fields[key])
        elif isinstance(config._fields[key], Field):
            value = config._fields[key].get()
        config_dict[key] = value
    return config_dict


def _config_to_flat_dict(config: Config, prefix="") -> dict:
    """
    Convert a Config object to a flat dot-notation dictionary recursively.

    This function recursively converts a Config object and its nested
    Config objects into a flat dot-notation dictionary. It includes only
    public attributes and their corresponding values.

    Args:
        config (Config): The Config object to be converted.
        prefix (str): The prefix for dot-notation keys.

    Returns:
        dict: A flat dictionary with dot-notation keys.
    """
    flat_dict = {}
    for key in config:
        if key.startswith("_"):
            continue
        full_key = f"{prefix}.{key}" if prefix else key
        if isinstance(config._fields[key], Config):
            nested_dict = _config_to_flat_dict(config._fields[key], prefix=full_key)
            flat_dict.update(nested_dict)
        elif isinstance(config._fields[key], Field):
            value = config._fields[key].get()
            flat_dict[full_key] = value
    return flat_dict


def _fill_config_from_mapping(base_config: Config, mapping: Mapping[str, Any]) -> None:
    """
    Recursively fill the given configuration object using values
    from a mapping.

    This function traverses a mapping and sets corresponding attributes
    in the configuration object. If a value in the mapping is itself a
    dictionary,a child configuration is created and filled recursively.

    Args:
        base_config (Config): The configuration object to be filled.
        values_mapping (Mapping[str, Any]): The mapping containing values
            to be set.
    """
    for key, rest in mapping.items():
        if isinstance(rest, dict):
            child_config = Config(type_safe=base_config.is_type_safe)
            _fill_config_from_mapping(child_config, rest)
            rest = child_config
        base_config.__setattr__(key, rest)


def _suggest_alternative(word, possibilities, message="") -> str:
    """
    Add a 'Did you mean' message to the given message if a close match
    is found.

    Args:
        word: The word to check for alternatives.
        possibilities: List of possible alternative words.
        message: The original message to which the suggestion will be added.

    Returns:
        Updated message with 'Did you mean' suggestion if a close match
        is found. Otherwise, the original message.
    """
    matches = difflib.get_close_matches(word, possibilities, 1, 0.7)
    if matches:
        if message:
            message += "\n"
        message += f'Did you mean "{matches[0]}" instead of "{word}"?'
    return message
