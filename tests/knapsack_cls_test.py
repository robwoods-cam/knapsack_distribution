import unittest
import sys
import io
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
    
        self.assertEqual(hash(knapsack_items[0]), 52575527697059388)
        self.assertEqual(hash(knapsack_items[1]), 35253537267539874)
        self.assertEqual(hash(knapsack_items[2]), 49977518110941115)

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

        KnapsackItem._knapsack_items_count = 0  # Hack to account that tests can be run out of order or may fail, changing the number of KnapsackItems created.

        knapsack_items = [KnapsackItem(100, 50), KnapsackItem(50, 30), KnapsackItem(30, 60), KnapsackItem(140, 120), KnapsackItem(40, 25)]
        knapsack_capacity = 100
        KnapsackProblem.create(knapsack_items, knapsack_capacity)

    def test_stable_hash(self):
        """ Test the hash is stable between Python runs. """

        KnapsackItem._knapsack_items_count = 0  # Hack to account that tests can be run out of order or may fail, changing the number of KnapsackItems created.

        knapsack_items = [KnapsackItem(100, 50), KnapsackItem(50, 30), KnapsackItem(30, 60), KnapsackItem(140, 120), KnapsackItem(40, 25)]
        knapsack_capacity = 100
        knapsack_problem = KnapsackProblem.create(knapsack_items, knapsack_capacity)
        
        hash_string = str(sorted(knapsack_items)) + "," + str(knapsack_capacity) + "," + str(0) + "," + str([]) + "," + str(hash(None))
        full_hash = hashlib.sha256(hash_string.encode("utf-8")).digest()
        knapsack_hash = int.from_bytes(full_hash[:7], 'big')

        self.assertEqual(hash(knapsack_problem), knapsack_hash)        
        self.assertEqual(hash(knapsack_problem), 39192840581773738)
        self.assertEqual(knapsack_problem._full_hash, full_hash)
        self.assertEqual(knapsack_problem._full_hash, b'\x8b=\xaeL\x9dy\xaa\x90QCQ\x1dJ\x03\xfc\xf9\xb2=3(\xce\xf1\xf0\xbdJf\xc0\x82v\xb6\x9d\xc9')

    def test_get_node_distribution(self):
        """ Test the node distribution calculation.
        
        This test is based on model 2.0 and for a given knapsack that was manually calculated.
        """

        KnapsackItem._knapsack_items_count = 0  # Hack to account that tests can be run out of order or may fail, changing the number of KnapsackItems created.

        knapsack_items = [KnapsackItem(100, 50), KnapsackItem(50, 30), KnapsackItem(30, 60), KnapsackItem(140, 120), KnapsackItem(40, 25)]
        knapsack_capacity = 100
        knapsack_problem = KnapsackProblem.create(knapsack_items, knapsack_capacity)

        param_alpha = 0.75
        param_beta = 0.6
        param_gamma = 0.2
        param_delta = 0.6

        node_distribution = knapsack_problem.get_node_distribution(param_alpha, param_beta, param_gamma, param_delta)

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
        """ Test the node distribution calculation.
        
        This test is based on model 2.0 and uses the knapsack example in Chapter 1 Appendix 1 (8.1) for the optimisation problem that was manually calculated.
        """

        KnapsackItem._knapsack_items_count = 0  # Hack to account that tests can be run out of order or may fail, changing the number of KnapsackItems created.

        knapsack_items = [KnapsackItem(12, 7), KnapsackItem(8, 5), KnapsackItem(14, 8), KnapsackItem(9, 4)]
        knapsack_capacity = 16
        knapsack_problem = KnapsackProblem.create(knapsack_items, knapsack_capacity)

        param_alpha = 0.70
        param_beta = 0.75
        param_gamma = 0.4
        param_delta = 0.5

        node_distribution = knapsack_problem.get_node_distribution(param_alpha, param_beta, param_gamma, param_delta)

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

        
    def test_print_node_distribution(self):
        """ Test the printed message from print_node_distribution.

        This test is based on model 2.0 and uses the knapsack example in Chapter 1 Appendix 1 (8.1) for the optimisation problem.        
        """

        KnapsackItem._knapsack_items_count = 0  # Hack to account that tests can be run out of order or may fail, changing the number of KnapsackItems created.

        knapsack_items = [KnapsackItem(12, 7), KnapsackItem(8, 5), KnapsackItem(14, 8), KnapsackItem(9, 4)]
        knapsack_capacity = 16
        knapsack_problem = KnapsackProblem.create(knapsack_items, knapsack_capacity)

        param_alpha = 0.70
        param_beta = 0.75
        param_gamma = 0.4
        param_delta = 0.5

        node_distribution = knapsack_problem.get_node_distribution(param_alpha, param_beta, param_gamma, param_delta)
        
        original = sys.stdout
        try:
            buf = io.StringIO()
            sys.stdout = buf
            knapsack_problem.print_node_distribution(node_distribution, (param_alpha, param_beta, param_gamma, param_delta), 0.01)
            expected_print = "Inputs\n\nParameters: α = 0.7, β = 0.75, γ = 0.4, δ = 0.5\n\nKnapsack Problem Variant: Optimisation\n\nItems: (v: 12, w: 7), (v: 8, w: 5), (v: 14, w: 8), (v: 9, w: 4)\n\nBudget: 16\n\n-------------------------------------\n\nOutput\n\nTerminal Nodes (*** for optimal):\n[1, 1, 0, 1] - Σv: 29, Σw: 16 / 16 - 74.873% ***\n[1, 0, 1, 0] - Σv: 26, Σw: 15 / 16 - 15.341%\n[0, 0, 1, 1] - Σv: 23, Σw: 12 / 16 - 8.380%\n[0, 1, 1, 0] - Σv: 22, Σw: 13 / 16 - 1.406%\n\nTotal Distribution: 1.0\n\nNumber of Terminal Nodes: 4\n\n"
            
            self.assertEqual(buf.getvalue(), expected_print)
        finally:
            sys.stdout = original

    
    def test_get_node_distribution_paper_appendix_1_decision(self):
        """ Test the decision witness finding calculation.
        
        This test is based on model 2.0 and uses the knapsack example in Chapter 1 Appendix 1 (8.1) for the decision problem that was manually calculated."""

        knapsack_items = [KnapsackItem(12, 7), KnapsackItem(8, 5), KnapsackItem(14, 8), KnapsackItem(9, 4)]
        knapsack_capacity = 16
        knapsack_problem = KnapsackProblem.create(knapsack_items, knapsack_capacity)
        
        param_alpha = 0.70
        param_beta = 0.75
        param_gamma = 0.4
        param_delta = 0.5
        value_threshold = 27

        satisfiable_percent = knapsack_problem.solve_decision_variant(param_alpha, param_beta, param_gamma, param_delta, value_threshold)
        
        self.assertAlmostEqual(satisfiable_percent, 0.9001191238392088)


if __name__ == '__main__':
    unittest.main()
