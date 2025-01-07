import copy
import pickle
import random
import unittest
from rosslt import Tracked
from visualization_msgs.msg import Marker


class TestWrapping(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.rng = random.Random()

    def test_hash(self):

        # integer
        val = self.rng.randint(-100, 100)
        self.assertEqual(hash(val), hash(Tracked(val)))

        # float
        val = self.rng.random()
        self.assertEqual(hash(val), hash(Tracked(val)))

        # tuple
        val = tuple(str(self.rng.randint(0, 10000)))
        self.assertEqual(hash(val), hash(Tracked(val)))

        # attribute
        class A:
            def __init__(self):
                self.value = val

        self.assertEqual(hash(val), hash(Tracked(A()).value))

    def test_format(self):

        # int to hex format
        val = Tracked(0x123)
        self.assertEqual("{:04X}".format(val), "0123")

    def test_copy(self):

        # tracked marker
        marker = Tracked(Marker())
        marker.pose.position.x = 1.0

        # copy position
        copy_val = copy.copy(marker.pose.position)
        copy_val.x += 1

        # deep copy marker
        copy_val = copy.deepcopy(marker)
        copy_val.pose.position.x += 1
        self.assertEqual(copy_val.pose.position.x, 2)

        # assert initial value after copies
        self.assertEqual(marker.pose.position.x, 1)

    def test_pickle(self):

        # tracked int
        tracked1 = pickle.dumps(5)
        tracked2 = pickle.dumps(5)
        self.assertEqual(tracked1, tracked2)

        # tracked marker
        tracked1 = pickle.dumps(Marker())
        tracked2 = pickle.dumps(Marker())
        self.assertEqual(tracked1, tracked2)

    def test_instance(self):

        # subclass
        # expected to return false, because the metaclass of the wrapped object can not be modified
        self.assertFalse(isinstance(Tracked(5), int))
        self.assertFalse(isinstance(Tracked(Marker()), Marker))

    def test_marker(self):

        # tracked marker
        marker = Tracked(Marker())

        # set initial values
        original = 5.0
        marker.pose.position.x = original
        marker.pose.position.y = original

        # in place operators
        marker.pose.position.x += 1.5
        marker.pose.position.x -= 0.5
        marker.pose.position.y *= 4.0
        marker.pose.position.y /= 2.0

        # using temporary value
        marker.pose.position.x = marker.pose.position.x + 2.5
        marker.pose.position.x = marker.pose.position.x - 1.5
        marker.pose.position.y = marker.pose.position.y * 4.0
        marker.pose.position.y = marker.pose.position.y / 2.0

        # integer test for float type assertion
        marker.pose.position.x += 2
        marker.pose.position.x -= 1
        marker.pose.position.y *= 4
        marker.pose.position.y /= 2

        # deep copy
        test_val = copy.deepcopy(marker.pose.position)
        self.assertEqual(test_val._location.id, -1)
        test_val.x *= 0

        # reverse and compare with original value
        self.assertEqual(marker.pose.position.x.get_original(), original)
        self.assertEqual(marker.pose.position.y.get_original(), original)


if __name__ == "__main__":
    unittest.main()
