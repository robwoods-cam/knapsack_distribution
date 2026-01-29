from knapsack_distribution import KnapsackItem, KnapsackInstance

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

    # Define target
    knapsack_target = 1562

    # Create knapsack problem
    knapsack_instance = KnapsackInstance.create(knapsack_items, knapsack_capacity)

    # Define parameters
    param_alpha, param_beta, param_gamma, param_delta = 0.7, 0.6, 0.4, 0.6

    # Solve the decision variant
    find_witness_probability = knapsack_instance.solve_decision_variant(param_alpha, param_beta, param_gamma, param_delta, value_threshold=knapsack_target)

    # Print the result
    print(f"The probability of finding a witness is: {find_witness_probability * 100:.2f}%.")


if __name__ == "__main__":
    main()
