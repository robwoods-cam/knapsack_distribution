import unittest
import sys
import io
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

    def test_get_node_distribution(self):
        """ Test the node distribution calculation.
        
        This test is based on model 2.0 and for a given knapsack that was manually calculated.
        """

        KnapsackItem._knapsack_items_count = 0  # Hack to account that tests can be run out of order or may fail, changing the number of KnapsackItems created.

        knapsack_items = [KnapsackItem(100, 50), KnapsackItem(50, 30), KnapsackItem(30, 60), KnapsackItem(140, 120), KnapsackItem(40, 25)]
        knapsack_capacity = 100
        knapsack_instance = KnapsackInstance.create(knapsack_items, knapsack_capacity)

        param_alpha = 0.75
        param_beta = 0.6
        param_gamma = 0.2
        param_delta = 0.6

        node_distribution = knapsack_instance.get_node_distribution(param_alpha, param_beta, param_gamma, param_delta)

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

        self.assertEqual(KnapsackInstance.instance_by_hash[25120288178553251]._standing_knapsack_items, [knapsack_items[0], knapsack_items[1]])
        self.assertEqual(KnapsackInstance.instance_by_hash[6357217347003608]._standing_knapsack_items, [knapsack_items[0], knapsack_items[4]])
        self.assertEqual(KnapsackInstance.instance_by_hash[7741808502296642]._standing_knapsack_items, [knapsack_items[1], knapsack_items[4]])
        self.assertEqual(KnapsackInstance.instance_by_hash[3854787489353282]._standing_knapsack_items, [knapsack_items[1], knapsack_items[2]])
        self.assertEqual(KnapsackInstance.instance_by_hash[19588103317795958]._standing_knapsack_items, [knapsack_items[2], knapsack_items[4]])

    def test_get_node_distribution_paper_appendix_1_optimisation(self):
        """ Test the node distribution calculation.
        
        This test is based on model 2.0 and uses the knapsack example in Chapter 1 Appendix 1 (8.1) for the optimisation instance that was manually calculated.
        """

        KnapsackItem._knapsack_items_count = 0  # Hack to account that tests can be run out of order or may fail, changing the number of KnapsackItems created.

        knapsack_items = [KnapsackItem(12, 7), KnapsackItem(8, 5), KnapsackItem(14, 8), KnapsackItem(9, 4)]
        knapsack_capacity = 16
        knapsack_instance = KnapsackInstance.create(knapsack_items, knapsack_capacity)

        param_alpha = 0.70
        param_beta = 0.75
        param_gamma = 0.4
        param_delta = 0.5

        node_distribution = knapsack_instance.get_node_distribution(param_alpha, param_beta, param_gamma, param_delta)

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

        self.assertEqual(KnapsackInstance.instance_by_hash[19607764745246483]._standing_knapsack_items, [knapsack_items[0], knapsack_items[1], knapsack_items[3]])
        self.assertEqual(KnapsackInstance.instance_by_hash[27586698572505746]._standing_knapsack_items, [knapsack_items[0], knapsack_items[2]])
        self.assertEqual(KnapsackInstance.instance_by_hash[67530635375991832]._standing_knapsack_items, [knapsack_items[2], knapsack_items[3]])
        self.assertEqual(KnapsackInstance.instance_by_hash[11599976948146986]._standing_knapsack_items, [knapsack_items[1], knapsack_items[2]])

        
    def test_print_node_distribution(self):
        """ Test the printed message from print_node_distribution.

        This test is based on model 2.0 and uses the knapsack example in Chapter 1 Appendix 1 (8.1) for the optimisation instance.        
        """

        KnapsackItem._knapsack_items_count = 0  # Hack to account that tests can be run out of order or may fail, changing the number of KnapsackItems created.

        knapsack_items = [KnapsackItem(12, 7), KnapsackItem(8, 5), KnapsackItem(14, 8), KnapsackItem(9, 4)]
        knapsack_capacity = 16
        knapsack_instance = KnapsackInstance.create(knapsack_items, knapsack_capacity)

        param_alpha = 0.70
        param_beta = 0.75
        param_gamma = 0.4
        param_delta = 0.5

        node_distribution = knapsack_instance.get_node_distribution(param_alpha, param_beta, param_gamma, param_delta)
        
        original = sys.stdout
        try:
            buf = io.StringIO()
            sys.stdout = buf
            knapsack_instance.print_node_distribution(node_distribution, (param_alpha, param_beta, param_gamma, param_delta), 0.01)
            expected_print = "Inputs\n\nParameters: α = 0.7, β = 0.75, γ = 0.4, δ = 0.5\n\nKnapsack Problem Variant: Optimisation\n\nItems: (v: 12, w: 7), (v: 8, w: 5), (v: 14, w: 8), (v: 9, w: 4)\n\nBudget: 16\n\n-------------------------------------\n\nOutput\n\nTerminal Nodes (*** for optimal):\n[1, 1, 0, 1] - Σv: 29, Σw: 16 / 16 - 74.873% ***\n[1, 0, 1, 0] - Σv: 26, Σw: 15 / 16 - 15.341%\n[0, 0, 1, 1] - Σv: 23, Σw: 12 / 16 - 8.380%\n[0, 1, 1, 0] - Σv: 22, Σw: 13 / 16 - 1.406%\n\nTotal Distribution: 1.0\n\nNumber of Terminal Nodes: 4\n\n"
            
            self.assertEqual(buf.getvalue(), expected_print)
        finally:
            sys.stdout = original

    
    def test_get_node_distribution_paper_appendix_1_decision(self):
        """ Test the decision witness finding calculation.
        
        This test is based on model 2.0 and uses the knapsack example in Chapter 1 Appendix 1 (8.1) for the decision instance that was manually calculated."""

        knapsack_items = [KnapsackItem(12, 7), KnapsackItem(8, 5), KnapsackItem(14, 8), KnapsackItem(9, 4)]
        knapsack_capacity = 16
        knapsack_instance = KnapsackInstance.create(knapsack_items, knapsack_capacity)
        
        param_alpha = 0.70
        param_beta = 0.75
        param_gamma = 0.4
        param_delta = 0.5
        value_threshold = 27

        satisfiable_percent = knapsack_instance.solve_decision_variant(param_alpha, param_beta, param_gamma, param_delta, value_threshold)
        
        self.assertAlmostEqual(satisfiable_percent, 0.9001191238392088)


if __name__ == '__main__':
    unittest.main()
