import unittest
from rosslt import Tracked
from visualization_msgs.msg import Marker


class TestComparators(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def test_int(self):

        # test with integer
        val = Tracked(5)
        self.assertTrue(val > 1)
        self.assertTrue(val < 11)
        self.assertTrue(val >= 5)
        self.assertTrue(val <= 5)

    def test_marker(self):

        # test with marker
        val = Tracked(Marker())
        val.pose.position.x = 5.0
        self.assertTrue(val.pose.position.x > 1)
        self.assertTrue(val.pose.position.x < 11)
        self.assertTrue(val.pose.position.x >= 5)
        self.assertTrue(val.pose.position.x <= 5)


if __name__ == "__main__":
    unittest.main()
