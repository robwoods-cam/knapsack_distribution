import unittest
# import sys
# import io
import hashlib

from src.knapsack_distribution import KnapsackItem, KnapsackInstance, __version__

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
        
        hash_string = str(sorted(knapsack_items)) + "," + str(knapsack_capacity) + "," + str(0) + "," + str([]) + "," + str(hash(None))
        full_hash = hashlib.sha256(hash_string.encode("utf-8")).digest()
        knapsack_hash = int.from_bytes(full_hash[:7], 'big')

        self.assertEqual(hash(knapsack_instance), knapsack_hash)        
        self.assertEqual(hash(knapsack_instance), 39192840581773738)
        self.assertEqual(knapsack_instance._full_hash, full_hash)
        self.assertEqual(knapsack_instance._full_hash, b'\x8b=\xaeL\x9dy\xaa\x90QCQ\x1dJ\x03\xfc\xf9\xb2=3(\xce\xf1\xf0\xbdJf\xc0\x82v\xb6\x9d\xc9')


if __name__ == '__main__':
    unittest.main()
