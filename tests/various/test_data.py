import unittest

from app.data import UraNumber


class TestUraNumber(unittest.TestCase):
    def test_ura_number(self) -> None:
        self.assertEqual("00001234", str(UraNumber("1234")))
        self.assertEqual("12345678", str(UraNumber("12345678")))

        with self.assertRaises(ValueError):
            UraNumber("1234567890")
        with self.assertRaises(ValueError):
            UraNumber("foobar")
        with self.assertRaises(ValueError):
            UraNumber("1A525")
        with self.assertRaises(ValueError):
            UraNumber("")
