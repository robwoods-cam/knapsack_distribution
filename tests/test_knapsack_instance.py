import hashlib
import unittest

from src.knapsack_distribution import KnapsackInstance, KnapsackItem, __version__


class TestModelVersion(unittest.TestCase):

    def test_version(self):
        """ Check that the version of `knapsack_distribution` matches the model used to calculate these tests.

        Some of these tests use a manually calculated knapsack instance for comparison to the output
        of the package. They rely on a specific knapsack instance, specific parameters, and a specific
        version of the distribution model. Changing any of these may change the results, and these
        tests will no longer work.
        """
        self.assertEqual(__version__.split(".")[0], "2")
        self.assertEqual(__version__.split(".")[1], "0")

class TestKnapsackInstance(unittest.TestCase):

    def test_init(self):
        """ Test the creation of an instance. """

        KnapsackItem._knapsack_items_count = 0  # Hack to account that tests can be run out of order or may fail, changing the number of KnapsackItems created.

        knapsack_items = [KnapsackItem(100, 50), KnapsackItem(50, 30), KnapsackItem(30, 60), KnapsackItem(140, 120), KnapsackItem(40, 25)]
        knapsack_capacity = 100
        KnapsackInstance.create(knapsack_items, knapsack_capacity)

    def test_stable_hash(self):
        """ Test the hash is stable between Python runs. """

        KnapsackItem._knapsack_items_count = 0  # Hack to account that tests can be run out of order or may fail, changing the number of KnapsackItems created.

        knapsack_items = [KnapsackItem(100, 50), KnapsackItem(50, 30), KnapsackItem(30, 60), KnapsackItem(140, 120), KnapsackItem(40, 25)]
        knapsack_capacity = 100
        knapsack_instance = KnapsackInstance.create(knapsack_items, knapsack_capacity)

        hash_string = str(sorted(knapsack_items, key=lambda knapsack_item: hash(knapsack_item))) + "," + str(knapsack_capacity) + "," + str(0) + "," + str([]) + "," + str(hash(None))
        full_hash = hashlib.sha256(hash_string.encode("utf-8")).digest()
        knapsack_hash = int.from_bytes(full_hash[:7], 'big')

        self.assertEqual(hash(knapsack_instance), knapsack_hash)
        self.assertEqual(hash(knapsack_instance), 6338019714886162)
        self.assertEqual(knapsack_instance._full_hash, full_hash)
        self.assertEqual(knapsack_instance._full_hash, b"\x16\x84e5\xafj\x12'=\x8a!l\xa8\xbbO\x88\x02=X\x8c\xde\xc0T\x97\xdd\xff\x9e\x7f\t\xc0`A")


if __name__ == '__main__':
    unittest.main()
