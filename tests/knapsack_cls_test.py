import unittest
import hashlib

from knapsack_cls import KnapsackItem, KnapsackProblem
import knapsack_cls


class TestModelVersion(unittest.TestCase):

    def test_version(self):
        """ Check that the version of `knapsack_cls` matches the model used to calculate these tests.
        
        Some of these tests use a manually calculated knapsack instance for comparison to the output
        of the package. They rely on a specific knapsack instance, specific parameters, and a specific
        version of the distribution model. Changing any of these may change the results, and these 
        tests will no longer work.
        """
        self.assertEqual(knapsack_cls.__version__.split(".")[0], "2")
        self.assertEqual(knapsack_cls.__version__.split(".")[1], "0")


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

        value = 10
        weight = 30

        knapsack_item_id = KnapsackItem._knapsack_items_count
        knapsack_item = KnapsackItem(value, weight)

        hash_string = str(value) + "," + str(weight) + "," + str(knapsack_item_id)
        full_hash = hashlib.sha256(hash_string.encode("utf-8")).digest()
        knapsack_hash = int.from_bytes(full_hash[:7], 'big')

        self.assertEqual(hash(knapsack_item), knapsack_hash)        
    
    def test_create_from_list(self):
        """ Test the creation of multiple instances using the classmethod `create_from_list`. """

        values = [20, 10, 30]
        weights = [20, 30, 10]
        
        knapsack_items_count = KnapsackItem._knapsack_items_count
        knapsack_items = KnapsackItem.create_from_list(values, weights)

        self.assertEqual(len(knapsack_items), 3)

        for i, knapsack_item in enumerate(knapsack_items):
            self.assertIsInstance(knapsack_item, KnapsackItem)

            hash_string = str(values[i]) + "," + str(weights[i]) + "," + str(knapsack_items_count + i)
            full_hash = hashlib.sha256(hash_string.encode("utf-8")).digest()
            knapsack_hash = int.from_bytes(full_hash[:7], 'big')        
                
            self.assertEqual(hash(knapsack_item), knapsack_hash)

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
        
        To allow for simplification of knapsack problems with repeated identical items (same value and weight),
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


class TestKnapsackProblem(unittest.TestCase):

    def test_init(self):
        """ Test the creation of an instance. """
        pass  # TODO

    def test_stable_hash(self):
        """ Test the hash is stable between Python runs. """
        pass  # TODO

    def test_get_node_distribution(self):
        """ This test is based on model 2.0 TODO"""

        KnapsackItem._knapsack_items_count = 0  # Hack to account that tests can be run out of order or may fail, changing the number of KnapsackItems created.

        knapsack_items = [KnapsackItem(100, 50), KnapsackItem(50, 30), KnapsackItem(30, 60), KnapsackItem(140, 120), KnapsackItem(40, 25)]
        knapsack_capacity = 100
        knapsack_problem = KnapsackProblem.create(knapsack_items, knapsack_capacity)

        param_alpha = 0.75
        param_beta = 0.6
        param_gamma = 0.2
        param_delta = 0.6

        node_distribution = knapsack_problem.get_node_distribution(param_beta, param_alpha, param_gamma, param_delta)

        self.assertAlmostEqual(sum(node_distribution.values()), 1.0)

        sorted_node_distribution = {key: value for key, value in sorted(node_distribution.items(), key=lambda item: item[1], reverse=True)}
        
        self.assertEqual(list(sorted_node_distribution.keys())[0], 25120288178553251)
        self.assertEqual(list(sorted_node_distribution.keys())[1], 6357217347003608)
        self.assertEqual(list(sorted_node_distribution.keys())[2], 7741808502296642)
        self.assertEqual(list(sorted_node_distribution.keys())[3], 3854787489353282)
        self.assertEqual(list(sorted_node_distribution.keys())[4], 19588103317795958)
        
        self.assertAlmostEqual(node_distribution[25120288178553251], 0.776998932560427)
        self.assertAlmostEqual(node_distribution[6357217347003608], 0.162691836871925)
        self.assertAlmostEqual(node_distribution[7741808502296642], 0.0440568067760513)
        self.assertAlmostEqual(node_distribution[3854787489353282], 0.0129266429474177)
        self.assertAlmostEqual(node_distribution[19588103317795958],  0.00332578084417862)

        self.assertEqual(KnapsackProblem.problems_by_hash[25120288178553251]._standing_knapsack_items, [knapsack_items[0], knapsack_items[1]])
        self.assertEqual(KnapsackProblem.problems_by_hash[6357217347003608]._standing_knapsack_items, [knapsack_items[0], knapsack_items[4]])
        self.assertEqual(KnapsackProblem.problems_by_hash[7741808502296642]._standing_knapsack_items, [knapsack_items[1], knapsack_items[4]])
        self.assertEqual(KnapsackProblem.problems_by_hash[3854787489353282]._standing_knapsack_items, [knapsack_items[1], knapsack_items[2]])
        self.assertEqual(KnapsackProblem.problems_by_hash[19588103317795958]._standing_knapsack_items, [knapsack_items[2], knapsack_items[4]])

    def test_get_node_distribution_paper_appendix_1_optimisation(self):
        """ This test is based on model 2.0
        
        This test uses the knapsack example in Chapter 1 Appendix 1 (8.1) for the optimisation problem 
        
        TODO"""

        KnapsackItem._knapsack_items_count = 0  # Hack to account that tests can be run out of order or may fail, changing the number of KnapsackItems created.

        knapsack_items = [KnapsackItem(12, 7), KnapsackItem(8, 5), KnapsackItem(14, 8), KnapsackItem(9, 4)]
        knapsack_capacity = 16
        knapsack_problem = KnapsackProblem.create(knapsack_items, knapsack_capacity)

        param_alpha = 0.70
        param_beta = 0.75
        param_gamma = 0.4
        param_delta = 0.5

        node_distribution = knapsack_problem.get_node_distribution(param_beta, param_alpha, param_gamma, param_delta)

        self.assertAlmostEqual(sum(node_distribution.values()), 1.0)

        sorted_node_distribution = {key: value for key, value in sorted(node_distribution.items(), key=lambda item: item[1], reverse=True)}

        self.assertEqual(list(sorted_node_distribution.keys())[0], 19607764745246483)
        self.assertEqual(list(sorted_node_distribution.keys())[1], 27586698572505746)
        self.assertEqual(list(sorted_node_distribution.keys())[2], 67530635375991832)
        self.assertEqual(list(sorted_node_distribution.keys())[3], 11599976948146986)
        
        self.assertAlmostEqual(node_distribution[19607764745246483], 0.7487276377548032)
        self.assertAlmostEqual(node_distribution[27586698572505746], 0.1534085161146231)
        self.assertAlmostEqual(node_distribution[67530635375991832], 0.08380264655104011)
        self.assertAlmostEqual(node_distribution[11599976948146986], 0.014061199579533638)

        self.assertEqual(KnapsackProblem.problems_by_hash[19607764745246483]._standing_knapsack_items, [knapsack_items[0], knapsack_items[1], knapsack_items[3]])
        self.assertEqual(KnapsackProblem.problems_by_hash[27586698572505746]._standing_knapsack_items, [knapsack_items[0], knapsack_items[2]])
        self.assertEqual(KnapsackProblem.problems_by_hash[67530635375991832]._standing_knapsack_items, [knapsack_items[2], knapsack_items[3]])
        self.assertEqual(KnapsackProblem.problems_by_hash[11599976948146986]._standing_knapsack_items, [knapsack_items[1], knapsack_items[2]])

        
    def test_get_node_distribution_paper_appendix_1_decision(self):
        """ This test is based on Model 2
        
        This test uses the knapsack example in Chapter 1 Appendix 1 (8.1) for the decision problem 
        
        TODO"""

        knapsack_items = [KnapsackItem(12, 7), KnapsackItem(8, 5), KnapsackItem(14, 8), KnapsackItem(9, 4)]
        knapsack_capacity = 16
        knapsack_problem = KnapsackProblem.create(knapsack_items, knapsack_capacity)
        
        param_alpha = 0.70
        param_beta = 0.75
        param_gamma = 0.4
        param_delta = 0.5
        value_threshold = 27

        satisfiable_percent = knapsack_problem.solve_decision_variant(param_beta, param_alpha, param_gamma, param_delta, value_threshold)
        
        self.assertAlmostEqual(satisfiable_percent, 0.9001191238392088)


if __name__ == '__main__':
    unittest.main()
