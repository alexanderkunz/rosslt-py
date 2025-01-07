import unittest
from rosslt import Tracked


class TestString(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def test_str(self):

        # test with marker
        val = Tracked("test")
        val = 3 * (val + "string")
        self.assertEqual(val.get_original(), "test")


if __name__ == "__main__":
    unittest.main()
