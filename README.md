# Knapsack Choice Distribution Tool

## 📌 Overview
This repository provides a Python implementation for modeling and analysing decision-making in the **Knapsack Problem**. It uses a **tree-based approach** with dominance checks and probabilistic node distribution.

This model may be be the first measure to give a truly instance specific metric of difficulty to the _NP-hard_ knapsack problem, not relying on heuristics to calculate the “average” difficulty of similar instances. It is also the first to predict choice distributions when individuals fail to find the optimal.

The knapsack problem is a classic combinatorial optimisation problem where the goal is to maximise the total value of items placed in a knapsack without exceeding its weight capacity (or if a target can be reach by a set of items within the budget constraint).

The formulation of the optimisation variant is shown below:
<div align="center"><img width="801" height="253" alt="image" src="https://github.com/user-attachments/assets/dbc1dae7-f22d-4c40-a16d-c124548a1803" /></div>

This tool takes a knapsack instance (featuring a set of items with values and weights, a capacity limit, and a target if the decision variant of the knapsack problem) and four individual parameters.

Given this, it will calculate the expected distribution of terminal nodes for the optimisation variant and the Boolean yes/no response to if the target is reachable, as well as the expected distribution of terminal witness nodes for the decision variant.

For full details of the model, including explanation and examples of the individual parameters refer to Chapter 1 of _Predicting decision-making under computational complexity_ by Roman Berlanger. 

---

## ✅ Features
- **KnapsackItem Class**  
  Represents individual items with attributes:
  - `value`, `weight`
  - Unique item ID and hash for efficient comparisons
  - Dominance checks between items

- **KnapsackProblem Class**  
  Represents a knapsack problem instance or node in the search tree:
  - Tracks remaining capacity, included items, and child nodes
  - Identifies terminal nodes and optimal solutions
  - Computes probabilistic distributions of reaching each terminal node

- **Dominance Handling**  
  Items and nodes are classified as dominated or non-dominated based on value and weight comparisons.

- **Node Distribution Calculation**  
  Computes probabilities based on behavioral parameters:
  - `param_alpha`: Search/global optimisation
  - `param_beta`: Density preference (local optimisation)
  - `param_gamma`: Complexity aversion (weight preference)
  - `param_delta`: Item-level rationality

- **Caching**  
  Uses hash-based caching to avoid redundant computations.

---

## 🛠 Requirements
- Python **3.14+** (due to modern type hints)
- Standard library only (`math`, `sys`)

---

## 🚀 Usage
### Example:
```python
from knapsack_cls import KnapsackItem, KnapsackProblem

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
knapsack_problem = KnapsackProblem.create(knapsack_items, knapsack_capacity)

# Define parameters
parameters = param_alpha, param_beta, param_gamma, param_delta = 0.7, 0.6, 0.4, 0.6

# Compute distribution
knapsack_distribution = knapsack_problem.get_node_distribution(param_beta, param_alpha, param_gamma, param_delta)

# Print distribution
knapsack_problem.print_node_distribution(knapsack_distribution, parameters, 0.01)
```
Output:
```
Inputs

Parameters: α = 0.7, β = 0.6, γ = 0.4, δ - 0.6

Knapsack Problem Variant: Optimisation

Items: (v: 535, w: 236), (v: 214, w: 113), (v: 152, w: 96), (v: 342, w: 220), (v: 259, w: 172), (v: 268, w: 212), (v: 246, w: 220), (v: 137, w: 158), (v: 148, w: 184), (v: 24, w: 46), (v: 23, w: 64), (v: 47, w: 189)

Budget: 957

-------------------------------------

Output

Terminal Nodes (*** for optimal):
[1, 1, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0] - Σv: 1618, Σw: 953 / 957 - 24.057% ***
[1, 0, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0] - Σv: 1556, Σw: 936 / 957 - 10.486%
[1, 1, 1, 1, 1, 0, 0, 0, 0, 1, 1, 0] - Σv: 1549, Σw: 947 / 957 - 10.305%
[1, 1, 1, 1, 0, 1, 0, 0, 0, 1, 0, 0] - Σv: 1535, Σw: 923 / 957 - 7.670%
[1, 1, 1, 0, 1, 1, 0, 0, 0, 1, 1, 0] - Σv: 1475, Σw: 939 / 957 - 4.337%
[1, 0, 1, 1, 1, 0, 1, 0, 0, 0, 0, 0] - Σv: 1534, Σw: 944 / 957 - 2.796%
[1, 1, 1, 1, 0, 0, 1, 0, 0, 1, 0, 0] - Σv: 1513, Σw: 931 / 957 - 2.670%
[1, 1, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0] - Σv: 1522, Σw: 953 / 957 - 2.590%
[1, 1, 0, 1, 1, 0, 0, 1, 0, 1, 0, 0] - Σv: 1511, Σw: 945 / 957 - 1.921%
[1, 1, 0, 1, 1, 0, 0, 0, 1, 0, 0, 0] - Σv: 1498, Σw: 925 / 957 - 1.843%
[1, 1, 1, 1, 0, 0, 0, 1, 0, 1, 1, 0] - Σv: 1427, Σw: 933 / 957 - 1.465%
[1, 1, 0, 1, 0, 1, 0, 1, 0, 0, 0, 0] - Σv: 1496, Σw: 939 / 957 - 1.373%
[0, 1, 1, 1, 1, 1, 0, 0, 0, 1, 1, 0] - Σv: 1282, Σw: 923 / 957 - 1.329%
[0, 1, 0, 1, 1, 1, 1, 0, 0, 0, 0, 0] - Σv: 1329, Σw: 937 / 957 - 1.222%
[1, 0, 0, 1, 0, 1, 1, 0, 0, 1, 0, 0] - Σv: 1415, Σw: 934 / 957 - 1.220%
[1, 0, 1, 1, 0, 1, 0, 0, 1, 0, 0, 0] - Σv: 1445, Σw: 948 / 957 - 1.130%
[1, 1, 1, 0, 1, 0, 1, 0, 0, 1, 1, 0] - Σv: 1453, Σw: 947 / 957 - 1.105%
[1, 1, 0, 0, 1, 1, 0, 0, 1, 0, 0, 0] - Σv: 1424, Σw: 917 / 957 - 1.038%

Total Distribution: 1.0

Number of Terminal Nodes: 338
```


---

## 📖 Terminology
- **Node**: A knapsack state with a set of remaining items and capacity.
- **Child Node**: A new node created by adding one item to the current knapsack.
- **Master Node**: The founding node which created this knapsack problem.
- **Terminal Node**: A node with no feasible child nodes (capacity exhausted or no items left).
- **Dominated Item**: An item that is strictly worse than another (higher weight and lower or equal value).
- **Non-Dominated Item**: An item that is not dominated by any other in the current set.
- **Dominated Child Node**: A node containing at least one dominated item which is added from this node onwards. Items already added are ignored.
- **Optimal Node**: The terminal node(s) with the highest total value which are possible from this node. There may be better terminal nodes from the master node, but they cannot be reached from this branch.

---

## 🔓 License
This project is licensed under AGPLv3. Derivative works must be licensed under the same terms and source code must be made available.

---

## Copyright
Copyright (c) 2025 Robert Woods

Copyright (c) 2025 Roman Berlanger
