from absl.testing import parameterized
from fieldconfig.field import Field
from fieldconfig.field import ValidationError
from fieldconfig.field import RequiredValueError

_NoneType = type(None)


class FieldTest(parameterized.TestCase):

    @parameterized.parameters(
        [
            # matching types
            {"default": 1, "ftype": int, "exp_value": 1, "exp_type": int},
            # type inference
            {
                "default": 1.0,
                "ftype": None,
                "exp_value": 1.0,
                "exp_type": float,
            },
            # cast int -> float
            {
                "default": 1,
                "ftype": float,
                "exp_value": 1.0,
                "exp_type": float,
            },
            # cast list -> tuple
            {
                "default": [1],
                "ftype": tuple,
                "exp_value": (1,),
                "exp_type": tuple,
            },
            # cast tuple -> list
            {
                "default": (1,),
                "ftype": list,
                "exp_value": [1],
                "exp_type": list,
            },
            # allow None value
            {
                "default": None,
                "ftype": int,
                "exp_value": None,
                "exp_type": _NoneType,
            },
        ]
    )
    def test_good_construction(self, default, ftype, exp_value, exp_type):
        field = Field(default, ftype)
        value = field.get()
        self.assertIsInstance(value, exp_type)
        if default is None:
            self.assertEqual(field.get_type(), ftype)
        else:
            self.assertEqual(field.get_type(), exp_type)

    def test_bad_construction(self):
        with self.assertRaisesWithLiteralMatch(
            ValueError,
            "Either provide a valid default value or specify a field type.",
        ):
            Field(None)

    def test_required(self):

        # pass
        field = Field(None, int, required=False)
        value = field.get()
        self.assertIsNone(value)

        # fail
        with self.assertRaisesWithLiteralMatch(
            RequiredValueError,
            "Value is None. Please set a valid value before retrieving.",
        ):
            field = Field(None, int, required=True)
            field.get()

    def test_validator(self):
        # pass
        field = Field(1, int, validator=lambda x: x == 1)
        value = field.get()
        self.assertEqual(value, 1)

        # skip
        field = Field(None, int, validator=lambda x: x == 1)
        value = field.get()
        self.assertIsNone(value)

        # fail with lambda
        with self.assertRaisesWithLiteralMatch(
            ValidationError,
            "The provided value 1 (int) does not meet the criteria: \n"
            "      lambda x: x != 1",
        ):
            field = Field(1, int, validator=lambda x: x != 1)
            field.get()

        # fail with regular function
        def is_valid(x):
            return x != 1

        with self.assertRaisesWithLiteralMatch(
            ValidationError,
            (
                "The provided value 1 (int) does not meet the criteria: \n"
                "      def is_valid(x):\n"
                "            return x != 1"
            ),
        ):
            field = Field(1, int, validator=is_valid)
            field.get()

    def test_field_as_default_value(self):
        # pass
        field = Field(Field(1.1), None)
        value = field.get()
        self.assertEqual(value, 1.1)

        field = Field(Field(1.1), float)
        value = field.get()
        self.assertEqual(value, 1.1)

        # fail
        with self.assertRaisesWithLiteralMatch(
            TypeError,
            "Invalid Field type: <class 'float'>. It should be a subclass of <class 'int'>.",
        ):
            field = Field(Field(1.0), int)

    def test_str(self):
        field = Field(Field(1.1), float)
        self.assertEqual(
            str(field),
            "Field(default=1.1, ftype=<class 'float'>, validator=None, required=False)",
        )

    def test_copy(self):
        field = Field(
            Field(1.1), float, validator=lambda x: x > 0, required=True
        )
        field_copy = field.copy()
        self.assertIsInstance(field_copy, Field)
        for attr in ["_ftype", "_validator", "_value", "_required"]:
            self.assertEqual(getattr(field, attr), getattr(field_copy, attr))
