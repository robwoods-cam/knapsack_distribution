import time
from knapsack_cls import KnapsackProblem, KnapsackItem

start = time.time()

knapsack_items = [KnapsackItem(535, 236), KnapsackItem(214, 113), KnapsackItem(152, 96), KnapsackItem(342, 220), KnapsackItem(259, 172), KnapsackItem(268, 212), KnapsackItem(246, 220), KnapsackItem(137, 158), KnapsackItem(148, 184), KnapsackItem(24, 46), KnapsackItem(23, 64), KnapsackItem(47, 189)]
knapsack_capacity = 957
knapsack_problem = KnapsackProblem.create(knapsack_items, knapsack_capacity)
print(f'[RUN TIME] Knapsack Problem Created - {time.time() - start}')

print(len(KnapsackProblem.problems_by_hash))

print(f'Terminal knapsacks: {sum(knapsack_problem.is_terminal_node for knapsack_problem in KnapsackProblem.problems_by_hash.values())}')

param_alpha = 0.7
param_beta = 0.6
param_gamma = 0.0
param_delta = 0.0

distribution = dict(sorted(knapsack_problem.get_node_distribution(param_beta, param_alpha, param_gamma, param_delta).items(), key=lambda x: x[1], reverse=True))

print(f'[RUN TIME] Node Distribution Calculated - {time.time() - start}')

knapsack_problem.print_node_distribution(distribution, 0.01)

print(f'[RUN TIME] Node Distribution Printed - {time.time() - start}')
