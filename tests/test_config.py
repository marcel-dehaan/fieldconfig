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
        cfg.a.b = 1
        self.assertEqual(cfg.a.b, 1)

        # enable intermediate attribute creation after instantiation
        cfg = Config(create_intermediate_attributes=False)
        cfg.enable_intermediate_attribute_creation()
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

    def test_update(self):
        cfg = Config()
        cfg.a = Config()
        cfg.a.b = Config()
        cfg.a.b.c = 1
        cfg.a.b.d = 2
        cfg.update({"a.b.c": 3, "a.b.d": 4})

        self.assertEqual(cfg.a.b.c, 3)
        self.assertEqual(cfg.a.b.d, 4)

        cfg = Config(create_intermediate_attributes=True)
        cfg.update({"a.b.c": 3})
        self.assertEqual(cfg.a.b.c, 3)
