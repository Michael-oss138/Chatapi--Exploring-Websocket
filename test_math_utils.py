import unittest 
from math_utils import add

class TestMathUtils(unittest.TestCase):

    def test_add_positive_numbers(self):
        result = add(2, 3)
        self.assertEqual(result, 5)

    def test_negative_numbers(self):
        result = add(-1, -1)
        self.assertEqual(result, -2)

    def test_mixed_numbers(self):
        result = add(-1, 1)
        self.assertEqual(result, 0)


if __name__ == "__main__":
    unittest.main()