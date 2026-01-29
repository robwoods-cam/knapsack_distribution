from knapsack_distribution import KnapsackItem, KnapsackInstance, ProblemType

def main() -> None:
    # Define knapsack items
    knapsack_items = [
        KnapsackItem(535, 236), KnapsackItem(214, 113), KnapsackItem(152, 96),
        KnapsackItem(342, 220), KnapsackItem(259, 172), KnapsackItem(268, 212),
        KnapsackItem(246, 220), KnapsackItem(137, 158), KnapsackItem(148, 184),
        KnapsackItem(24, 46), KnapsackItem(23, 64), KnapsackItem(47, 189)
    ]

    # Define capacity
    knapsack_capacity = 957

    # Create knapsack problem
    knapsack_instance = KnapsackInstance.create(knapsack_items, knapsack_capacity)

    # Define parameters
    parameters = param_alpha, param_beta, param_gamma, param_delta = 0.7, 0.6, 0.4, 0.6

    # Compute distribution
    knapsack_distribution = knapsack_instance.get_node_distribution(
        param_alpha, param_beta, param_gamma, param_delta, problem_type=ProblemType.OPTIMISATION
    )

    # Print distribution
    knapsack_instance.print_node_distribution(knapsack_distribution, parameters, print_threshold=0.01)


if __name__ == "__main__":
    main()
