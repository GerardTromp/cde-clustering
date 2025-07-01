# ------------------------------
# File: tests/test_helpers.py
# ------------------------------
import unittest
from utils.helpers import safe_nested_increment, flatten_nested_dict


class TestSafeNestedIncrement(unittest.TestCase):
    def test_single_increment(self):
        d = {}
        safe_nested_increment(d, "a", "b", "c")
        self.assertEqual(d["a"]["b"]["c"], 1)

    def test_multiple_increments(self):
        d = {}
        safe_nested_increment(d, "x", "y", "z")
        safe_nested_increment(d, "x", "y", "z", v=2)
        self.assertEqual(d["x"]["y"]["z"], 3)

    def test_parallel_keys(self):
        d = {}
        safe_nested_increment(d, "p", "q", "r")
        safe_nested_increment(d, "p", "q", "s")
        self.assertEqual(d["p"]["q"]["r"], 1)
        self.assertEqual(d["p"]["q"]["s"], 1)

    def test_deep_structure(self):
        d = {}
        safe_nested_increment(d, "a", "b", "c", "d", "e")
        self.assertEqual(d["a"]["b"]["c"]["d"]["e"], 1)


class TestFlattenNestedDict(unittest.TestCase):
    def test_flatten_simple(self):
        d = {"a": {"b": 1}}
        expected = {"a.b": 1}
        self.assertEqual(flatten_nested_dict(d), expected)

    def test_flatten_deep(self):
        d = {"x": {"y": {"z": 10}}}
        expected = {"x.y.z": 10}
        self.assertEqual(flatten_nested_dict(d), expected)

    def test_flatten_parallel(self):
        d = {"a": {"b": 1, "c": 2}, "d": 3}
        expected = {"a.b": 1, "a.c": 2, "d": 3}
        self.assertEqual(flatten_nested_dict(d), expected)


if __name__ == "__main__":
    unittest.main()
