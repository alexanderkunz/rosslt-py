import unittest
import random
from rosslt import Tracked


class TestContainer(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.rng = random.Random()
        self.iterations = 1000

    def test_lists(self):

        # run n times
        for n in range(self.iterations):

            # test list creation
            val = Tracked([])
            for i in range(self.rng.randint(1, 20)):

                # append random number
                item = self.rng.randint(1, 999)
                val.append(item)

                # verify addition
                val[i] += 1
                self.assertEqual(val[i], item + 1)

            # test iterator
            i = 0
            for x in val:
                self.assertEqual(x, val[i])
                i += 1

    def test_dict(self):

        # run n times
        for n in range(self.iterations):

            # test dict creation
            val = Tracked({})
            key = 0
            for i in range(self.rng.randint(1, 20)):

                # append random entry
                item = self.rng.randint(1, 999)
                val[key] = item

                # verify addition
                val[key] += 1
                self.assertEqual(val[key], item + 1)

                # iterate key
                key += 1

            # test iterator
            val_length = 0
            for _ in val:
                val_length += 1
            self.assertEqual(val_length, len(val))

    def test_class(self):

        # test class definition
        class RGB:
            def __init__(self, r=0, g=0, b=0):
                self.r = r
                self.g = g
                self.b = b

        # run n times
        for n in range(self.iterations):

            # test class creation
            ran_r = self.rng.randint(1, 999)
            ran_g = self.rng.randint(1, 999)
            ran_b = self.rng.randint(1, 999)
            val = Tracked(RGB(ran_r, ran_g, ran_b))

            # apply random operations to value
            while self.rng.random() < 0.9:
                number = self.rng.randint(1, 999)
                choice = self.rng.randint(1, 1000)
                if choice == 1:
                    val.r = val.r + number
                elif choice == 2:
                    val.g = val.g + number
                elif choice == 3:
                    val.b = val.b + number
                elif choice == 4:
                    val.r += number
                elif choice == 5:
                    val.g += number
                elif choice == 6:
                    val.b += number
                elif choice == 7:
                    val.r = val.r - number
                elif choice == 8:
                    val.g = val.g - number
                elif choice == 9:
                    val.b = val.b - number
                elif choice == 10:
                    val.r -= number
                elif choice == 11:
                    val.g -= number
                elif choice == 12:
                    val.b -= number

            # validate results
            self.assertEqual(val.r.get_original(), ran_r)
            self.assertEqual(val.g.get_original(), ran_g)
            self.assertEqual(val.b.get_original(), ran_b)


if __name__ == "__main__":
    unittest.main()
