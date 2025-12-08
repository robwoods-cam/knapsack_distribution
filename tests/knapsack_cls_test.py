import unittest

from knapsack_cls import KnapsackItem, KnapsackProblem, MODEL_VERSION


class TestModelVersion(unittest.TestCase):

    def test_version(self):
        self.assertEqual(MODEL_VERSION, 2)


class TestKnapsackItem(unittest.TestCase):

    def test_init(self):

        value = 10
        weight = 30

        knapsack_item = KnapsackItem(value, weight)

        density: float = value / weight

        self.assertEqual(knapsack_item.value, value)
        self.assertEqual(knapsack_item.weight, weight)
        self.assertAlmostEqual(knapsack_item.density, density)


    def test_comparison(self):
        """ Test the comparison between Knapsack Items

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


class TestKnapsackProblem(unittest.TestCase):

    def test_get_node_distribution(self):
        """ This test is based on Model 2 """
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
        
        self.assertAlmostEqual(list(sorted_node_distribution.values())[0], 0.776998932560427)
        self.assertAlmostEqual(list(sorted_node_distribution.values())[1], 0.162691836871925)
        self.assertAlmostEqual(list(sorted_node_distribution.values())[2], 0.0440568067760513)
        self.assertAlmostEqual(list(sorted_node_distribution.values())[3], 0.0129266429474177)
        self.assertAlmostEqual(list(sorted_node_distribution.values())[4],  0.00332578084417862)

        self.assertEqual(KnapsackProblem.problems_by_hash[list(sorted_node_distribution.keys())[0]]._standing_knapsack_items, [knapsack_items[0], knapsack_items[1]])
        self.assertEqual(KnapsackProblem.problems_by_hash[list(sorted_node_distribution.keys())[1]]._standing_knapsack_items, [knapsack_items[0], knapsack_items[4]])
        self.assertEqual(KnapsackProblem.problems_by_hash[list(sorted_node_distribution.keys())[2]]._standing_knapsack_items, [knapsack_items[1], knapsack_items[4]])
        self.assertEqual(KnapsackProblem.problems_by_hash[list(sorted_node_distribution.keys())[3]]._standing_knapsack_items, [knapsack_items[1], knapsack_items[2]])
        self.assertEqual(KnapsackProblem.problems_by_hash[list(sorted_node_distribution.keys())[4]]._standing_knapsack_items, [knapsack_items[2], knapsack_items[4]])


    def test_get_node_distribution_paper_appendix_1_optimisation(self):
        """ This test is based on Model 2
        
        This test uses the knapsack example in Chapter 1 Appendix 1 (8.1) for the optimisation problem """
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
        
        self.assertAlmostEqual(list(sorted_node_distribution.values())[0], 0.7487276377548032)
        self.assertAlmostEqual(list(sorted_node_distribution.values())[1], 0.1534085161146231)
        self.assertAlmostEqual(list(sorted_node_distribution.values())[2], 0.08380264655104011)
        self.assertAlmostEqual(list(sorted_node_distribution.values())[3], 0.014061199579533638)

        self.assertEqual(KnapsackProblem.problems_by_hash[list(sorted_node_distribution.keys())[0]]._standing_knapsack_items, [knapsack_items[0], knapsack_items[1], knapsack_items[3]])
        self.assertEqual(KnapsackProblem.problems_by_hash[list(sorted_node_distribution.keys())[1]]._standing_knapsack_items, [knapsack_items[0], knapsack_items[2]])
        self.assertEqual(KnapsackProblem.problems_by_hash[list(sorted_node_distribution.keys())[2]]._standing_knapsack_items, [knapsack_items[2], knapsack_items[3]])
        self.assertEqual(KnapsackProblem.problems_by_hash[list(sorted_node_distribution.keys())[3]]._standing_knapsack_items, [knapsack_items[1], knapsack_items[2]])

        
    def test_get_node_distribution_paper_appendix_1_decision(self):
        """ This test is based on Model 2
        
        This test uses the knapsack example in Chapter 1 Appendix 1 (8.1) for the decision problem """
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
