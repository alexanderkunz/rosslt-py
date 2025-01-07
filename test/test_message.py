import unittest
import random
from rosslt import Tracked
from visualization_msgs.msg import Marker
from std_msgs.msg import Int32
from rosslt_py_msgs.msg import TrackedMarker, TrackedInt32


class TestMessage(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.rng = random.Random()

    def test_int32(self):
        original = 5

        # tracked int32
        int32_value = Tracked(Int32())
        int32_value.data = original
        int32_value.data += 1

        # generate message
        int32_msg = int32_value.to_msg(TrackedInt32)

        # restore from message
        int32_new = Tracked.from_msg(int32_msg)

        # verify that expression is still packed
        self.assertEqual(len(int32_new.data.get_expression()._history), 0)
        self.assertTrue(int32_new.data.get_expression().packed())

        # additional expression
        int32_new.data += 4

        # verify that expression is now unpacked
        self.assertTrue(len(int32_new.data.get_expression()._history) > 0)
        self.assertFalse(int32_new.data.get_expression().packed())

        # reverse value
        self.assertEqual(int32_new.data.get_original(), original)

    def test_marker(self):

        # tracked marker
        marker = Tracked(Marker())

        # initial values
        original = self.rng.random()
        marker.pose.position.x = original
        marker.pose.position.y = original
        marker.pose.position.z = original

        # generate history
        for x in range(16):
            marker.pose.position.x += self.rng.random()
            marker.pose.position.y -= self.rng.random()
            marker.pose.position.z *= (1.0 + self.rng.random())
            marker.pose.position.z /= (1.0 + self.rng.random())

        # reverse original marker
        self.assertAlmostEqual(marker.pose.position.x.get_original(), original, 2)
        self.assertAlmostEqual(marker.pose.position.y.get_original(), original, 2)
        self.assertAlmostEqual(marker.pose.position.z.get_original(), original, 2)

        # create message
        msg = marker.to_msg(TrackedMarker)
        self.assertEqual(msg.data.pose.position.x, marker.pose.position.x)
        self.assertEqual(msg.data.pose.position.y, marker.pose.position.y)
        self.assertEqual(msg.data.pose.position.z, marker.pose.position.z)

        # parse message
        marker_new = Tracked.from_msg(msg)
        self.assertEqual(marker_new.pose.position.x, marker.pose.position.x)
        self.assertEqual(marker_new.pose.position.y, marker.pose.position.y)
        self.assertEqual(marker_new.pose.position.z, marker.pose.position.z)

        # reverse new marker
        self.assertAlmostEqual(marker_new.pose.position.x.get_original(), original, 2)
        self.assertAlmostEqual(marker_new.pose.position.y.get_original(), original, 2)
        self.assertAlmostEqual(marker_new.pose.position.z.get_original(), original, 2)


if __name__ == "__main__":
    unittest.main()
