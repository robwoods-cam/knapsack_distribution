# Knapsack Choice Distribution Tool

## 📌 Overview
This repository provides a Python implementation for modeling and analyzing decision-making in **Knapsack Problems** under computational complexity. It uses a **tree-based approach** with dominance checks and probabilistic node distribution.

The knapsack problem is a classic combinatorial optimization problem where the goal is to maximize the total value of items placed in a knapsack without exceeding its weight capacity.

---

## ✅ Features
- **KnapsackItem Class**  
  Represents individual items with attributes:
  - `value`, `weight`, `density`
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
  - `param_alpha`: Search/global optimization
  - `param_beta`: Density preference (local optimization)
  - `param_gamma`: Complexity aversion (weight preference)
  - `param_delta`: Item-level rationality

- **Caching**  
  Uses hash-based caching to avoid redundant computations.

---

## 🛠 Requirements
- Python **3.14+** (due to modern type hints)
- Standard library only (`math`, `sys`)

---

## 📂 File Structure
```
knapsack_cls.py   # Core implementation
README.md         # Documentation
```

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
param_alpha, param_beta, param_gamma, param_delta = 0.7, 0.6, 0.4, 0.6

# Compute distribution
knapsack_distribution = knapsack_problem.get_node_distribution(param_beta, param_alpha, param_gamma, param_delta)

# Print distribution
knapsack_problem.print_node_distribution(knapsack_distribution, 0.001)
```

---

## 📖 Terminology
- **Node**: A knapsack state with a set of remaining items and capacity.
- **Child Node**: A new node created by adding one item to the current knapsack.
- **Master Node**: The founding node which created this knapsack problem.
- **Terminal Node**: A node with no feasible child nodes (capacity exhausted or no items left).
- **Dominated Item**: An item that is strictly worse than another (higher weight and lower or equal value).
- **Non-Dominated Item**: An item that is not dominated by any other in the current set.
- **Dominated Node**: A node containing at least one dominated item which is added from this node onwards. Items already added are ignored.
- **Optimal Node**: The terminal node(s) with the highest total value which are possible from this node. There may be better terminal nodes, but they cannot be reached from this branch.

## 🔓 License
This project is licensed under AGPLv3. Derivative works must be licensed under the same terms and source code must be made available.
