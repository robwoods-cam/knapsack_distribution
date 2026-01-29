import unittest
import hashlib

from src.knapsack_distribution import KnapsackItem, __version__

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


class TestKnapsackItem(unittest.TestCase):

    def test_init(self):
        """ Test the creation of an instance. """

        value = 10
        weight = 30

        knapsack_item = KnapsackItem(value, weight)

        density: float = value / weight

        self.assertIsInstance(knapsack_item, KnapsackItem)
        self.assertEqual(knapsack_item.value, value)
        self.assertEqual(knapsack_item.weight, weight)
        self.assertAlmostEqual(knapsack_item.density, density)

        
    def test_invalid_init(self):
        """ Test the creation of an invalid instance. """

        with self.assertRaises(TypeError):
            value = None
            weight = 30
            KnapsackItem(value, weight)

        with self.assertRaises(TypeError):
            value = 10
            weight = 30.0
            KnapsackItem(value, weight)

        with self.assertRaises(ValueError):
            value = -5
            weight = 30
            KnapsackItem(value, weight)

        with self.assertRaises(ValueError):
            value = 10
            weight = 0
            KnapsackItem(value, weight)
    
    def test_stable_hash(self):
        """ Test the hash is stable between Python runs. """
        
        KnapsackItem._knapsack_items_count = 0  # Hack to account that tests can be run out of order or may fail, changing the number of KnapsackItems created.

        value = 10
        weight = 30

        knapsack_item_id = KnapsackItem._knapsack_items_count
        knapsack_item = KnapsackItem(value, weight)

        hash_string = str(value) + "," + str(weight) + "," + str(knapsack_item_id)
        full_hash = hashlib.sha256(hash_string.encode("utf-8")).digest()
        knapsack_item_hash = int.from_bytes(full_hash[:7], 'big')

        self.assertEqual(hash(knapsack_item), knapsack_item_hash)
        self.assertEqual(hash(knapsack_item), 17689981930889819)
        self.assertEqual(knapsack_item._full_hash, full_hash)
        self.assertEqual(knapsack_item._full_hash, b'>\xd8\xf1\xe1\x12\xe2[+\xe1|_\xdb\xe4\x825\x007\xab\xc5`\xaa\x10\x81\xc3\xbd\x8c\xff\x8e1\x8c;\x15')
    
    def test_create_from_list(self):
        """ Test the creation of multiple instances using the classmethod `create_from_list`. """
        
        KnapsackItem._knapsack_items_count = 0  # Hack to account that tests can be run out of order or may fail, changing the number of KnapsackItems created.

        values = [20, 10, 30]
        weights = [20, 30, 10]
        
        knapsack_items_count = KnapsackItem._knapsack_items_count
        knapsack_items = KnapsackItem.create_from_list(values, weights)

        self.assertEqual(len(knapsack_items), 3)

        for i, knapsack_item in enumerate(knapsack_items):
            self.assertIsInstance(knapsack_item, KnapsackItem)

            hash_string = str(values[i]) + "," + str(weights[i]) + "," + str(knapsack_items_count + i)
            full_hash = hashlib.sha256(hash_string.encode("utf-8")).digest()
            knapsack_item_hash = int.from_bytes(full_hash[:7], 'big')
                
            self.assertEqual(hash(knapsack_item), knapsack_item_hash)
    
        self.assertEqual(hash(knapsack_items[0]), 67428692212939834)
        self.assertEqual(hash(knapsack_items[1]), 46942366995636327)
        self.assertEqual(hash(knapsack_items[2]), 48967257744732795)

    def test_comparison(self):
        """ Test the comparison between Knapsack Items.

        Ordering is done by density, however, to break ties, the larger item (in both value and weight)
        is considered "greater", to enable strict ordering of non-identical items. 

        large is the greatest
        medium all have the same density, but 2 is less than 1 and 3 in both value and weight
        medium 1 and 3 are greater than 2, but equal to each other
        small the least
        """

        knapsack_item_large = KnapsackItem(30, 10)

        knapsack_item_medium_1 = KnapsackItem(20, 20)
        knapsack_item_medium_2 = KnapsackItem(15, 15)
        knapsack_item_medium_3 = KnapsackItem(20, 20)

        knapsack_item_small = KnapsackItem(10, 20)

        self.assertGreater(knapsack_item_large, knapsack_item_medium_1)
        self.assertGreater(knapsack_item_large, knapsack_item_medium_2)
        self.assertGreater(knapsack_item_large, knapsack_item_medium_3)
        self.assertGreater(knapsack_item_large, knapsack_item_small)
        
        self.assertGreater(knapsack_item_medium_1, knapsack_item_medium_2)
        self.assertGreater(knapsack_item_medium_1, knapsack_item_small)
        self.assertGreater(knapsack_item_medium_3, knapsack_item_medium_2)
        self.assertGreater(knapsack_item_medium_3, knapsack_item_small)
        self.assertGreater(knapsack_item_medium_2, knapsack_item_small)

        self.assertNotEqual(knapsack_item_medium_1, knapsack_item_medium_2)
        self.assertEqual(knapsack_item_medium_1, knapsack_item_medium_3)
        self.assertNotEqual(knapsack_item_medium_2, knapsack_item_medium_3)

        self.assertNotEqual(knapsack_item_large, knapsack_item_medium_1)
        self.assertNotEqual(knapsack_item_large, knapsack_item_medium_2)
        self.assertNotEqual(knapsack_item_large, knapsack_item_medium_3)
        self.assertNotEqual(knapsack_item_large, knapsack_item_small)
        self.assertNotEqual(knapsack_item_small, knapsack_item_medium_1)
        self.assertNotEqual(knapsack_item_small, knapsack_item_medium_2)
        self.assertNotEqual(knapsack_item_small, knapsack_item_medium_3)

        self.assertLess(knapsack_item_small, knapsack_item_large)
        self.assertLess(knapsack_item_small, knapsack_item_medium_1)
        self.assertLess(knapsack_item_small, knapsack_item_medium_2)
        self.assertLess(knapsack_item_small, knapsack_item_medium_3)
    
    def test_dominance(self):
        """ Test dominance of `KnapsackItem`s.

        Items with higher value for the same (or less) weight dominate.
        Items with lower weight for the same (or less) value dominate.
        
        A dominates B dominates C.
        D is not dominated, nor dominates any item."""
    
        knapsack_item_A = KnapsackItem(30, 10)
        knapsack_item_B = KnapsackItem(20, 20)
        knapsack_item_C = KnapsackItem(10, 20)
        knapsack_item_D = KnapsackItem(5, 5)

        knapsack_items = [knapsack_item_A, knapsack_item_B, knapsack_item_C, knapsack_item_D]

        for i, knapsack_item in enumerate(knapsack_items):
            knapsack_item.set_dominance(knapsack_items[:i] + knapsack_items[i + 1:])

        self.assertFalse(knapsack_item_A.check_dominance([knapsack_item_B, knapsack_item_C, knapsack_item_D]))

        self.assertTrue(knapsack_item_B.check_dominance([knapsack_item_A]))
        self.assertFalse(knapsack_item_B.check_dominance([knapsack_item_C, knapsack_item_D]))

        self.assertTrue(knapsack_item_C.check_dominance([knapsack_item_A]))
        self.assertTrue(knapsack_item_C.check_dominance([knapsack_item_B]))
        self.assertFalse(knapsack_item_C.check_dominance([knapsack_item_D]))
        
        self.assertFalse(knapsack_item_D.check_dominance([knapsack_item_A, knapsack_item_B, knapsack_item_C]))
    
    def test_repeated_item_dominance(self):
        """ Test dominance of repeated `KnapsackItem`s.
        
        To allow for simplification of knapsack instances with repeated identical items (same value and weight),
        an arbitrary dominance between repeated items is applied which is that early items dominate later items.
        """

        knapsack_item_A = KnapsackItem(30, 10)
        knapsack_item_B = KnapsackItem(30, 10)
        knapsack_item_C = KnapsackItem(30, 10)
        
        knapsack_items = [knapsack_item_A, knapsack_item_B, knapsack_item_C]

        for i, knapsack_item in enumerate(knapsack_items):
            knapsack_item.set_dominance(knapsack_items[:i] + knapsack_items[i + 1:])

        self.assertFalse(knapsack_item_A.check_dominance([knapsack_item_B, knapsack_item_C]))

        self.assertTrue(knapsack_item_B.check_dominance([knapsack_item_A]))
        self.assertFalse(knapsack_item_B.check_dominance([knapsack_item_C]))

        self.assertTrue(knapsack_item_C.check_dominance([knapsack_item_A]))
        self.assertTrue(knapsack_item_C.check_dominance([knapsack_item_B]))
    
    def test_unset_dominance(self):
        """ Test calling `check_dominance` before `set_dominance`. """

        with self.assertRaises(RuntimeError):
            knapsack_item_A = KnapsackItem(30, 10)
            knapsack_item_B = KnapsackItem(20, 20)

            knapsack_item_A.check_dominance([knapsack_item_B])

    def test_invalid_self_dominance(self):
        """ Test setting invalid dominance (self dominance). """

        with self.assertRaises(ValueError):
            value = 10
            weight = 30

            knapsack_item = KnapsackItem(value, weight)

            knapsack_item.set_dominance([knapsack_item])

if __name__ == '__main__':
    unittest.main()
