import unittest

from app.filters import FilterStore


class FilterStoreTests(unittest.TestCase):
    def test_single_save_is_preserved(self):
        store = FilterStore()
        store.save("open-orders")
        self.assertEqual(store.all(), ["open-orders"])


if __name__ == "__main__":
    unittest.main()
