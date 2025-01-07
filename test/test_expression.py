import unittest
import random
from rosslt import Tracked


class TestExpression(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.rng = random.Random()
        self.iterations = 1000

    def test_integer(self):

        # run n times
        for n in range(self.iterations):

            # choose start value and create tracked
            val_start = self.rng.randint(0, 100)
            val_cur = Tracked(val_start)

            # apply random operations to value
            # no floor division because of information loss
            while self.rng.random() < 0.9:
                choice = self.rng.randint(1, 9)
                val_random = self.rng.randint(-100, 100)
                if choice == 1:
                    val_cur = val_cur + val_random
                elif choice == 2:
                    val_cur = val_cur - val_random
                elif choice == 3:
                    val_cur = val_cur * (val_random or 1)
                elif choice == 4:
                    val_cur = val_random + val_cur
                elif choice == 5:
                    val_cur = val_random - val_cur
                elif choice == 6:
                    val_cur = (val_random or 1) * val_cur
                elif choice == 7:
                    val_cur += val_random
                elif choice == 8:
                    val_cur -= val_random
                elif choice == 9:
                    val_cur *= val_random or 1

            # assert expression
            val_expression = val_cur.get_expression()(val_start)
            self.assertEqual(val_expression, val_cur)

            # assert reverse
            backwards = val_cur.get_expression().reverse()
            val_reverse = backwards(val_cur)
            self.assertEqual(val_reverse, val_start)

            # assert type
            self.assertEqual(int, type(val_cur._data), str(val_cur._data))
            self.assertEqual(int, type(val_expression), str(val_expression))
            self.assertEqual(int, type(val_reverse), str(val_reverse))

    def test_float(self):

        # run n times
        for n in range(self.iterations):

            # choose start value and create tracked
            val_start = self.rng.random()
            val_cur = Tracked(val_start)

            # apply random operations to value
            while self.rng.random() < 0.9:
                choice = self.rng.randint(1, 9)
                val_random = self.rng.random() * 10
                if choice == 1:
                    val_cur = val_cur + val_random
                elif choice == 2:
                    val_cur = val_cur - val_random
                elif choice == 3:
                    val_cur = val_cur * (val_random + 1)
                elif choice == 4:
                    val_cur = val_cur / (val_random + 1)
                elif choice == 5:
                    val_cur += val_random
                elif choice == 6:
                    val_cur -= val_random
                elif choice == 7:
                    val_cur *= (val_random + 1)
                elif choice == 8:
                    val_cur /= (val_random + 1)
                elif choice == 9:
                    val_cur = val_cur ** 0.75

            # assert expression
            val_expression = val_cur.get_expression()(val_start)
            self.assertAlmostEqual(val_expression, val_cur, 1)

            # assert reverse
            backwards = val_cur.get_expression().reverse()
            val_reverse = backwards(val_cur)
            self.assertAlmostEqual(val_reverse, val_start, 1)

    def test_trig(self):

        # run n times
        for n in range(self.iterations):

            # choose start value and create tracked
            val_start = self.rng.random()
            val_cur = Tracked(val_start)

            # apply random operations to value
            while self.rng.random() < 0.9:
                choice = self.rng.randint(1, 4)
                if choice == 1:
                    val_cur = val_cur.sin()
                elif choice == 2:
                    val_cur = val_cur.cos()
                elif abs(val_cur) < 1:

                    # value is in range (-1, 1)
                    if choice == 3:
                        val_cur = val_cur.asin()
                    elif choice == 4:
                        val_cur = val_cur.acos()

            # assert expression
            val_expression = val_cur.get_expression()(val_start)
            self.assertAlmostEqual(val_expression, val_cur, 1)

    def test_dependencies(self):

        def blackbox(a, b):
            a = 9 - a + b
            b = a + b + 4
            return a + b

        # one tracked instance
        self.assertEqual(blackbox(Tracked(7), 3).get_original(), 7)

        # two tracked instances
        self.assertEqual(blackbox(Tracked(5), Tracked(7)).get_original(), 5)

    def test_blackbox(self):

        def blackbox(x):
            from random import Random
            rng = Random(1337)
            while rng.random() < 0.9:
                choice = rng.randint(0, 8)
                val = rng.random() * 10
                if choice == 0:
                    x = x + val
                elif choice == 1:
                    x = x - val
                elif choice == 2:
                    x = x * (val + 1)
                elif choice == 3:
                    x = x / (val + 1)
                elif choice == 4:
                    x += val
                elif choice == 5:
                    x -= val
                elif choice == 6:
                    x *= (val + 1)
                elif choice == 7:
                    x /= (val + 1)
                elif choice == 8:
                    x = x ** 0.75
            return x

        from rosslt import Tracked
        param = blackbox(Tracked(0.0)).get_expression().reverse()(42.0)
        print(f"blackbox({param}) = {blackbox(param)}")

        self.assertAlmostEqual(blackbox(param), 42.0, 2)


if __name__ == "__main__":
    unittest.main()
