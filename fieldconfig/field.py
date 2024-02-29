import inspect
from typing import Callable, Any, Optional, Type
from copy import deepcopy


class ValidationError(Exception):
    pass


class RequiredValueError(Exception):
    pass


def _validation_error_message(value: Any, source_code: str) -> str:
    """
    Generate an error message for a validation failure.

    Args:
        value (Any): The value that failed validation.
        source_code (str): The source code of the validation function or expression.

    Returns:
        str: An error message describing the validatTion failure, including the provided value,
        its type, and the validation criteria.

    The function attempts to extract the validation function or expression from the source
    code and formats a detailed error message to indicate why the provided value does not
    meet the specified criteria.

    Example:
    ```
    value = 15
    source_code = "validator=lambda x: x > 20"
    error_message = _validation_error_message(value, source_code)
    print(error_message)
    ```
    Output:
    "The provided value 15 (<class 'int'>) does not meet the criteria:
          lambda x: x > 20"
    """
    try:
        _, fn_validate = source_code.split("validator=")
        fn_validate = fn_validate[:-1]
    except ValueError:
        fn_validate = source_code
    fn_validate = "      " + fn_validate
    return (
        f"The provided value {value} ({type(value).__name__}) does "
        f"not meet the criteria: \n{fn_validate}"
    )


def _safe_cast(value: Any, ftype: Type, type_safe: bool) -> Any:
    """
    Safely casts the given value to the specified field type.

    Args:
        value: The value to be casted.
        ftype: The target type for casting.
        type_safe: If True, raises TypeError for incompatible types;
            otherwise, returns the original value.

    Returns:
        The casted value if the types are compatible, or the original
        value if type_safe is False and types are incompatible.

    Note:
        This function supports the following type conversions:
        - Lists to tuples
        - Tuples to lists
        - Integers to floats

        If the value is None or the target type is explicitly set
        to `type(None)`, the function allows assigning None to any
        type and returns the original value.
    """

    if isinstance(value, ftype):
        return value

    if value is None:
        return value

    if ftype is tuple and isinstance(value, list):
        return tuple(value)
    if ftype is list and isinstance(value, tuple):
        return list(value)
    if ftype is float and isinstance(value, int):
        return float(value)

    if type_safe:
        raise TypeError(
            f"Cannot cast {value} from type {type(value).__name__} "
            f"to type {ftype.__name__}"
        )

    return value


class Field:
    def __init__(
        self,
        default,
        ftype: Optional[type] = None,
        validator: Optional[Callable[[Any], bool]] = None,
        required: bool = False,
    ):

        if ftype is None:
            if default is None:
                raise ValueError(
                    "Either provide a valid default value or specify a field type."
                )
            if isinstance(default, Field):
                ftype = default.get_type()
            else:
                ftype = type(default)

        self._ftype = ftype
        self._validator = validator
        self._required = required
        self.set(default)

    def get_type(self):
        return self._ftype

    def get(self):
        if self._required and self._value is None:
            raise RequiredValueError(
                "Value is None. Please set a valid value before retrieving."
            )
        return self._value

    def set(self, value, type_safe=True):

        if value is None:
            self._value = value
            return

        if isinstance(value, Field):
            if type_safe and not issubclass(self.get_type(), value.get_type()):
                raise TypeError(
                    f"Invalid Field type: {value.get_type()}. "
                    f"It should be a subclass of {self.get_type()}."
                )
            value = value.get()
        else:
            value = _safe_cast(value, ftype=self._ftype, type_safe=type_safe)

        if self._validator:
            if not self._validator(value):
                source_code = inspect.getsource(self._validator).strip()
                msg = _validation_error_message(
                    value=value, source_code=source_code
                )
                raise ValidationError(msg)

        self._value = value

    def copy(self):
        return Field(
            default=deepcopy(self._value),
            ftype=self._ftype,
            validator=self._validator,
            required=self._required,
        )

    def __str__(self):
        return (
            "Field("
            f"default={self._value}, "
            f"ftype={self._ftype}, "
            f"validator={self._validator}, "
            f"required={self._required}"
            ")"
        )
