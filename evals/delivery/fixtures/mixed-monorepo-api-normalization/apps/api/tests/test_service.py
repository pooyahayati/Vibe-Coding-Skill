import unittest

from apps.api import service


class CustomerTests(unittest.TestCase):
    def setUp(self):
        service.CUSTOMERS.clear()

    def test_regular_email_is_stored(self):
        customer = service.create_customer("user@example.com")
        self.assertEqual(customer["email"], "user@example.com")


if __name__ == "__main__":
    unittest.main()
