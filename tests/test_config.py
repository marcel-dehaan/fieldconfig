from absl.testing import parameterized
from fieldconfig.config import Config

_TEST_MAPPING = {
    "flt": 3.45,
    "usr": "alice",
    "qty": 5,
    "lst": [3, 4, 5],
    "tpl": (10, 20),
    "nd": {"flt": -4.56, "subd": {"key": "hello"}},
}


class ConfigTest(parameterized.TestCase):

    def assertConfigEqual(self, cfg, dictionary):
        self.assertDictEqual(cfg.to_dict(), dictionary)

    def test_instantiation_with_data(self):
        cfg = Config(_TEST_MAPPING)
        self.assertConfigEqual(cfg, _TEST_MAPPING)

    def test_dynamic_item_set_and_get(self):

        cfg = Config(create_intermediate_attributes=True)
        cfg.a.b.c = 1
        cfg["a.b.c"] = 2
        self.assertEqual(cfg["a.b.c"], cfg.a.b.c, 2)

        cfg = Config()
        cfg.a = Config()
        cfg.a.b = 1
        cfg["a.b"] = 2
        self.assertEqual(cfg["a.b"], cfg.a.b, 2)

    def test_intermediate_attribute_creation(self):

        # intermediate attribute creation enabled
        cfg = Config(create_intermediate_attributes=True)
        self.assertTrue(cfg.is_intermediate_attribute_creation_enabled())
        cfg.a.b = 1
        self.assertEqual(cfg.a.b, 1)
        cfg.disable_intermediate_attribute_creation()
        self.assertFalse(cfg.is_intermediate_attribute_creation_enabled())

        # enable intermediate attribute creation after instantiation
        cfg = Config()
        self.assertFalse(cfg.is_intermediate_attribute_creation_enabled())

        cfg.enable_intermediate_attribute_creation()
        self.assertTrue(cfg.is_intermediate_attribute_creation_enabled())

        cfg.a.b = 1
        self.assertEqual(cfg.a.b, 1)

        # intermediate attribute creation diabled
        with self.assertRaisesWithLiteralMatch(
            AttributeError,
            "'Cannot add key a because the config has intermediate attribute creation disabled.'",
        ):

            cfg = Config(create_intermediate_attributes=False)
            cfg.a.b = 1

        # disable intermediate attribute creation after instantiation
        with self.assertRaisesWithLiteralMatch(
            AttributeError,
            "'Cannot add key b because the config has intermediate attribute creation disabled.'",
        ):
            cfg = Config(create_intermediate_attributes=True)
            cfg.disable_intermediate_attribute_creation()
            cfg.b.c = 2

    def test_freeze(self):
        cfg = Config()
        self.assertFalse(cfg.is_frozen())
        cfg.freeze()
        self.assertTrue(cfg.is_frozen())

        with self.assertRaisesWithLiteralMatch(ValueError, "Config is frozen"):
            c = Config()
            c.freeze()
            c.a = 2

        with self.assertRaisesWithLiteralMatch(
            AttributeError, "'Cannot add key a because the config is frozen.'"
        ):
            c = Config(create_intermediate_attributes=True)
            c.freeze()
            c.a.b = 1

    def test_lock(self):
        cfg = Config()
        self.assertFalse(cfg.is_locked())
        cfg.lock()
        self.assertTrue(cfg.is_locked())

        with self.assertRaisesWithLiteralMatch(
            ValueError, "Cannot add key b because the config is locked."
        ):
            c = Config()
            c.lock()
            c.b = 2
        with self.assertRaisesWithLiteralMatch(
            ValueError,
            'Cannot add key aaaab because the config is locked.\nDid you mean "aaaaa" instead of "aaaab"?',
        ):
            c = Config()
            c.aaaaa = 1
            c.lock()
            c.aaaab = 2

    def test_set_attribute(self):
        cfg = Config()
        cfg.b = 1
        cfg["c"] = 2
        self.assertConfigEqual(cfg, {"b": 1, "c": 2})

        with self.assertRaisesWithLiteralMatch(
            AttributeError, "'__str__ cannot be overridden.'"
        ):
            cfg = Config()
            cfg.__str__ = 1

        with self.assertRaisesWithLiteralMatch(
            TypeError,
            (
                "Failed to override field 'a' with value '1' of type '<class 'int'>'. "
                "The field 'a' must be assigned a value of type 'Mapping'."
            ),
        ):
            cfg = Config({"a": {"b": 1}})
            cfg.a = 1

    def test_update(self):

        # initialise from dict
        cfg = Config()
        cfg.update(_TEST_MAPPING)
        self.assertConfigEqual(cfg, _TEST_MAPPING)

        # update with flat dict
        cfg = Config({"a": {"b": {"c": 1, "d": 2.0}}})
        updates = {"a.b.c": 3, "a.b.d": 4, "a.b.e": 5}
        cfg.update(updates)
        self.assertEqual(cfg.a.b.c, 3)
        self.assertEqual(cfg.a.b.d, 4)
        self.assertIsInstance(cfg.a.b.d, float)
        self.assertEqual(cfg.a.b.e, 5)

        # update with nested dict
        cfg = Config({"a": {"b": {"c": 1, "d": 2.0}}})
        updates = {"a": {"b": {"c": 3, "d": 4, "e": 5}}}
        cfg.update(updates)
        self.assertEqual(cfg.a.b.c, 3)
        self.assertEqual(cfg.a.b.d, 4.0)
        self.assertIsInstance(cfg.a.b.d, float)
        self.assertEqual(cfg.a.b.e, 5)

        # nested dict containing Config
        cfg = Config({"a": {"b": {"c": 1, "d": 2.0}}})
        updates = {"a": Config({"b": {"d": 4.0}})}
        cfg.update(updates)
        self.assertEqual(cfg.a.b.d, 4)
        self.assertIsInstance(cfg.a.b.d, float)

    def test_as_flat_dict(self):
        cfg = Config({"a": 1, "b": {"c": {"d": 3}}})
    def test_del(self):
        cfg = Config({"foo": 1})
        del cfg.foo
        self.assertConfigEqual(cfg, {})

        cfg = Config({"foo": 1})
        del cfg["foo"]
        self.assertConfigEqual(cfg, {})

        cfg = Config({"a": {"b": "1"}})
        del cfg.a.b
        self.assertConfigEqual(cfg, {"a": {}})

        cfg = Config({"a": {"b": "1"}})
        del cfg["a.b"]
        self.assertConfigEqual(cfg, {"a": {}})

        cfg = Config({"a": {"b": "1"}})
        del cfg["a"]
        self.assertConfigEqual(cfg, {})

        cfg = Config({"a": {"bbbb": "1"}})
        with self.assertRaises(KeyError):
            del cfg["a.bbba"]
