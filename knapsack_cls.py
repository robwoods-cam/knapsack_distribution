from __future__ import annotations
from typing import Optional
import math


LEAST_ITEMS_OPTIMALS_ONLY = True
REPEATED_ITEMS_CREATE_SINGLE_TERMINAL_NODE = True


def confirm_config(config_value: bool, config_true_message: str, config_false_message: str) -> None:
    """ alerts the users of the config being used and asks them to confirm they understand """
    input_text = ''
    while input_text.lower() != 'yes':
        if config_value:
            print('[IMPORT WARNING] ' + config_true_message + '\nDo you wish to proceed? (Type "Yes")')
        else:
            print('[IMPORT WARNING] ' + config_false_message + '\nDo you wish to proceed? (Type "Yes")')
        input_text = input()
        if input_text.lower() != 'yes':
            print(f'Unexpected response "{input_text}". Looking for "Yes"')


confirm_config(
    config_value=LEAST_ITEMS_OPTIMALS_ONLY,
    config_true_message='KnapsackProblem split optimal ONLY between terminal nodes with the LEAST number of KnapsackItems.',
    config_false_message='KnapsackProblem split optimal between ALL terminal nodes regardless of the number of KnapsackItems.',
)  # TODO out of date - remove - only go with ALL

confirm_config(
    config_value=REPEATED_ITEMS_CREATE_SINGLE_TERMINAL_NODE,
    config_true_message='Repeated identical KnapsackItems are only considered as a SINGLE terminal node for jumping to the optimal.',
    config_false_message='Repeated identical KnapsackItems are considered as MULTIPLE terminal nodes for jumping to the optimal.',
)


class KnapsackItem():
    """
    A class to represent a Knapsack Item.

    Attributes
    ----------
    value : int
        the value of the knapsack item
    weight : int
        the weight of the knapsack item
    density : float
        the density (`value` / `weight`) of the knapsack item
    __hash__ : int
        unique hash for the knapsack item (repeated identical items will have the same hash)  # TODO is this still true?


    Notes
    -----
    * `__eq__` and `__gt__` were reworked to allow sorting of `KnapsackItem`s to allow a `KnapsackProblem` to create
    a unique hash based on the items available to allow for nodes to merge and save computational resources.
    """
    _value: int
    _weight: int
    _density: float
    _hash: int
    _dominating_knapsack_item_hashes: Optional[set[int]]

    _knapsack_items_count = 0

    @classmethod
    def create_from_list(cls, values: list[int], weights: list[int]) -> list[KnapsackItem]:
        """ creates a `list` of `KnapsackItem` from a list of `values` and `weights`

        Parameters
        ----------
        values : list[int]
            The values of the `KnapsackItem`s to be created in order
        weights : list[int]
            The weights of the `KnapsackItem`s to be created in order

        Raises
        ------
        Exception
            if `values` and `weights` are not both `list`s of `int`s

        Exception
            if the length of `values` and `weights` are not both equal

        Returns
        -------
            knapsack_items : list[KnapsackItem]
                the newly created `KnapsackItem`s

        """
        assert isinstance(values, list) and all(isinstance(value, int) for value in values)
        assert isinstance(weights, list) and all(isinstance(weight, int) for weight in weights)
        assert len(values) == len(weights)
        # TODO convert these into errors

        knapsack_items = []
        for value, weight in zip(values, weights):
            knapsack_items.append(KnapsackItem(value, weight))

        return knapsack_items

    def __init__(self, value: int, weight: int) -> None:
        self._value: int = value
        self._weight: int = weight
        self._density: float = self._value / self._weight
        self._knapsack_item_id = KnapsackItem._knapsack_items_count
        self._hash = hash(str(self._value) + str(self._weight) + str(self._knapsack_item_id))
        self._dominating_knapsack_item_hashes = None

        KnapsackItem._knapsack_items_count += 1

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, KnapsackItem):
            raise NotImplementedError
        return self._density == other.density and self._value == other.value

    def __gt__(self, other: object) -> bool:
        if not isinstance(other, KnapsackItem):
            raise NotImplementedError
        return self._density > other.density or (self._density == other.density and self._value > other.value)  # TODO rework

    def __hash__(self) -> int:
        return self._hash

    def __str__(self) -> str:
        return f'(v: {self._value}, w: {self._weight})'

    def __repr__(self) -> str:
        if REPEATED_ITEMS_CREATE_SINGLE_TERMINAL_NODE:
            return f'KnapsackItem(value = {self._value}, weight = {self._weight})'
        return f'KnapsackItem(value = {self._value}, weight = {self._weight}, id = {self._knapsack_item_id})'

    @property
    def value(self) -> int:
        """ the value of the knapsack item """
        return self._value

    @property
    def weight(self) -> int:
        """ the weight of the knapsack item """
        return self._weight

    @property
    def density(self) -> float:
        """ the density (value / weight) of the knapsack item """
        return self._density

    def set_dominance(self, knapsack_items: list[KnapsackItem]) -> None:
        """
        Sets `_dominating_knapsack_item_hashes` to a `set` of `hash`es for all `knapsack_item`s in `knapsack_items` that dominate it.
        A knapsack item dominates another if both the value is greater than the other value and the weight is less than the other weight and at least one is strictly.

        Parameters
        ----------
        knapsack_items : list[KnapsackItem]
            A list of `KnapsacksItems` to be checked for dominance

        Raises
        ------
        Exception
            if the `hash` of another `KnapsackItem` matches its own

        Returns
        -------
            None
        """
        assert isinstance(knapsack_items, list) and all(isinstance(knapsack_item, KnapsackItem) for knapsack_item in knapsack_items)

        self._dominating_knapsack_item_hashes = set()

        for knapsack_item in knapsack_items:
            # if hash(self) == hash(knapsack_item):
            #     # TODO this logic will not work in the case of identical repeated knapsack items
            #     raise Exception('Cannot set dominance with self')
            if (knapsack_item.value > self.value and knapsack_item.weight <= self.weight) or (knapsack_item.value >= self.value and knapsack_item.weight < self.weight):
                self._dominating_knapsack_item_hashes.add(hash(knapsack_item))

    def check_dominance(self, knapsack_items: list[KnapsackItem]) -> bool:
        """
        Checks to see if any `knapsack_item`s in `knapsack_items` that dominate itself.
        A knapsack item dominates another if both the value is greater than the other value and the weight is less than the other weight and at least one is strictly.
        `set_dominance` must be run prior to `check_dominance`
        Parameters
        ----------
        knapsack_items : list[KnapsackItem]
            A list of `KnapsacksItems` to be checked for dominance

        Raises
        ------
        Exception
            if the `hash` of another `KnapsackItem` matches its own

        Returns
            is dominated : bool
            if the item is dominated by any of the `KnapsackItems` in `knapsack_items`
        -------

        """
        if self._dominating_knapsack_item_hashes is None:
            raise Exception('Dominating knapsack items have not been set yet')

        for knapsack_item in knapsack_items:
            if hash(knapsack_item) in self._dominating_knapsack_item_hashes:
                return True

        return False

    # TODO add  def transformed_weight(phi, beta) -> float so it can be used everywhere
    # Consider using a reference system for phi and beta as they currently dont change
    # this means it can be looked up rather than calculated each time


class KnapsackProblem():
    """ A class to represent a Knapsack Problem.

    Attributes
    ----------
    knapsack_items : list[KnapsackItem]
        a `list` of all the possible `KnapsackItem`s that should be considered
    knapsack_capacity : int
        the weight capacity of the `KnapsackProblem`, the remaining capacity for a child node (sub problem)
    hash : int
        a unique value for the `KnapsackProblem`, this allows for multiple pathways to reach the same node and not require recalculation
    standing_value : int, default 0
        the sum of values of items already included in the knapsack
    master_knapsack : Optional[KnapsackProblem]
        the original `KnapsackProblem` which this node spawned from. If this is the original node, `master_knapsack` will be `None`
    raw_pick_weights: dict[int, float]
        the raw pick weight for each `KnapsackItem` based on the greedy algorithm without transformations for alpha, phi, lambda. This prevents recomputation of densities
    child_nodes : Optional[list[KnapsackProblem]]
        a `list` of all feasible (at or under capacity) sub `KnapsackProblem`s that can be created by including one of the `knapsack_items` 
    is_terminal_node : bool
        if there are no possible feasible `child_nodes`
    optimal_terminal_node : KnapsackProblem
        the optimal (highest `standing_value`) feasible `child_node`

    Methods
    -------
    **create** : *Callable*
        `create` should be used rather than `__init__`
    **get_node_distribution** : *Callable*
        Get the distribution that someone will end in each terminal node from this given Knapsack Problem.

    Notes
    -----
    * hash includes the master_knapsack, this means if we get to an identical node but from a different starting knapsack, everything will be processed again.
    * Python salts hashes. This means hashes are only consistent within a single Python run, not across runs. Could change to a consistent hashing function like MD5 or SHA if needed, but not required for now
    """

    problems_by_hash: dict[int, KnapsackProblem] = {}
    distributions_by_hash: dict[int, dict[int, float]] = {}

    @classmethod
    def create(cls, knapsack_items: list[KnapsackItem], knapsack_capacity: int, standing_value: int = 0, master_knapsack: Optional[KnapsackProblem] = None) -> KnapsackProblem:
        """ `KnapsackProblem.create()` should be used rather than `__init__`

        Parameters
        ----------
        knapsack_items : list[KnapsackItem]
            a `list` of all the possible `KnapsackItem`s that should be considered
        knapsack_capacity : int
            the weight capacity of the `KnapsackProblem`, the remaining capacity for a child node (sub problem)
        standing_value : int, default 0
            the sum of values of items already included in the knapsack
        master_knapsack : Optional[KnapsackProblem]
            the original `KnapsackProblem` which this node spawned from. If this is the original node, `master_knapsack` will be `None`
        """

        # for i, item_1 in enumerate(knapsack_items):
        #     for item_2 in knapsack_items[i + 1:]:
        #         if item_1 == item_2:
        #             raise ValueError(f'Two or more knapsack items are the same ({item_1} & {item_2}). We dont have a way to deal with this when they are the optimal')

        knapsack_hash: int = hash(str(sorted(knapsack_items)) + str(knapsack_capacity) + str(standing_value) + str(master_knapsack))  # TODO master_knapsack not needed if not used

        if knapsack_hash in cls.problems_by_hash:
            return cls.problems_by_hash[knapsack_hash]
        return KnapsackProblem(knapsack_items, knapsack_capacity, knapsack_hash, standing_value, master_knapsack)

    def __init__(self, knapsack_items: list[KnapsackItem], knapsack_capacity: int, knapsack_hash: int, standing_value: int = 0, master_knapsack: Optional[KnapsackProblem] = None) -> None:
        """
        Important
        ---------
        `KnapsackProblem.create()` should be used rather than `__init__`

        Parameters
        ----------
        knapsack_items : list[KnapsackItem]
            a `list` of all the possible `KnapsackItem`s that should be considered
        knapsack_capacity : int
            the weight capacity of the `KnapsackProblem`, the remaining capacity for a child node (sub problem)
        hash : int
            a unique value for the `KnapsackProblem`, this allows for multiple pathways to reach the same node and not require recalculation
        standing_value : int, default 0
            the sum of values of items already included in the knapsack
        master_knapsack : Optional[KnapsackProblem]
            the original `KnapsackProblem` which this node spawned from. If this is the original node, `master_knapsack` will be `None`
        """
        assert isinstance(knapsack_items, list) and all(isinstance(knapsack_item, KnapsackItem) for knapsack_item in knapsack_items)
        assert isinstance(knapsack_capacity, int) and knapsack_capacity >= 0
        assert isinstance(knapsack_hash, int)
        assert isinstance(standing_value, int)
        assert isinstance(master_knapsack, KnapsackProblem | None)

        self._knapsack_items: list[KnapsackItem] = knapsack_items
        self._knapsack_capacity: int = knapsack_capacity
        self._hash: int = knapsack_hash
        self._standing_value: int = standing_value
        self._master_knapsack: Optional[KnapsackProblem] = master_knapsack

        # self._number_items: int = len(self._knapsack_items)
        # self._sum_value: int = sum(knapsack_item.value for knapsack_item in self._knapsack_items)
        # self._sum_weight: int = sum(knapsack_item.weight for knapsack_item in self._knapsack_items)
        # self._sum_density: float = sum(knapsack_item.density for knapsack_item in self._knapsack_items)  # TODO this is of all items, not just feasible ones

        if master_knapsack is None:
            for i, knapsack_item in enumerate(self._knapsack_items):
                knapsack_item.set_dominance(self._knapsack_items[:i] + self._knapsack_items[i + 1:])

        self._non_dominated_items: set[int] = set()
        for i, knapsack_item in enumerate(self._knapsack_items):
            if not knapsack_item.check_dominance(self._knapsack_items[:i] + self._knapsack_items[i + 1:]):
                self._non_dominated_items.add(knapsack_item._hash)

        # is I need the density of the item included, the child node only have the items remaining, not included
        self._child_nodes: Optional[list[tuple[KnapsackItem, KnapsackProblem]]] = self._create_child_nodes()
        
        self._is_terminal_node: bool = self._child_nodes is None
        
        self._terminal_nodes: set[int] = set()
        if self._child_nodes:
            for _, child_node in self._child_nodes:
                if child_node._is_terminal_node:
                    self._terminal_nodes.add(child_node._hash)
                else:
                    self._terminal_nodes.update(child_node._terminal_nodes)

        self._number_of_terminal_nodes: Optional[int] = None if self._is_terminal_node else len(self._terminal_nodes)  # TODO pick either if self._is_terminal_node or if self._child_nodes is None
        
        self._optimal_terminal_node_value: int = self._standing_value if not self._child_nodes else max(child_node._optimal_terminal_node_value for _, child_node in self._child_nodes)
        self._optimal_terminal_node_least_items: Optional[int] = len(self._knapsack_items) if not self._child_nodes else max(child_node._optimal_terminal_node_least_items for _, child_node in self._child_nodes if child_node._optimal_terminal_node_value == self._optimal_terminal_node_value)
        
        self._optimal_terminal_nodes: set[int] = set()
        if self._child_nodes:
            for _, child_node in self._child_nodes:
                if child_node._optimal_terminal_node_value == self._optimal_terminal_node_value and (not LEAST_ITEMS_OPTIMALS_ONLY or child_node._optimal_terminal_node_least_items == self._optimal_terminal_node_least_items):
                    if child_node._is_terminal_node:
                        self._optimal_terminal_nodes.add(child_node._hash)
                    else:
                        self._optimal_terminal_nodes.update(child_node._optimal_terminal_nodes)
                elif child_node._optimal_terminal_node_value > self._optimal_terminal_node_value:
                    raise Exception('Testing only')

        self._number_of_optimal_terminal_nodes: Optional[int] = None if self._is_terminal_node else len(self._optimal_terminal_nodes)
        
        if self._optimal_terminal_nodes:
            if len(set(len(self.problems_by_hash[optimal_terminal_node]._knapsack_items) for optimal_terminal_node in self._optimal_terminal_nodes)) > 1:
                raise NotImplementedError('Currently do not deal with dropping of terminal nodes with more items included')

        self.problems_by_hash[knapsack_hash] = self

    def __hash__(self) -> int:
        return self._hash

    def _create_child_nodes(self) -> Optional[list[tuple[KnapsackItem, KnapsackProblem]]]:
        if len(self._knapsack_items) == 1:
            return None

        child_nodes: list[tuple[KnapsackItem, KnapsackProblem]] = []

        for i, knapsack_item in enumerate(self._knapsack_items):
            knapsack_capacity = self._knapsack_capacity - self._knapsack_items[i].weight
            if knapsack_capacity >= 0:
                master_knapsack: KnapsackProblem = self._master_knapsack if self._master_knapsack else self
                standing_value = self._standing_value + self._knapsack_items[i].value
                child_node = KnapsackProblem.create(self._knapsack_items[:i] + self._knapsack_items[i + 1:],
                                                    knapsack_capacity, standing_value,
                                                    master_knapsack)
                child_nodes.append((knapsack_item, child_node))
        return child_nodes if child_nodes else None

    def get_node_distribution(self, param_alpha: float, param_phi: float, param_beta: float, param_lambda: float) -> dict[int, float]:
        """
        Get the distribution (as a percentage of 1) that someone will end in each terminal node from this given Knapsack Problem.
        Node distribution only considers feasible (at or under capacity) terminal (no more items will in the knapsack) nodes.

        Parameters
        ----------
        param_alpha : float
            # TODO
        param_phi : float
            # TODO
        param_beta : float
            # TODO
        param_lambda : float
            # TODO

        Raises
        ------
        Exception
            if the sum of node distribution is not close to 1

        Returns
        -------
        node_distribution : dict[int, float]
            A dict of the feasible terminal nodes with the percentage that one will end in each terminal node based on `alpha`
        """
        
        assert isinstance(param_alpha, float) and 0.0 <= param_alpha <= 1.0
        assert isinstance(param_phi, float) and 0.0 <= param_phi < 1.0
        assert isinstance(param_beta, float) and 0.0 <= param_beta < 1.0
        assert isinstance(param_lambda, float) and 0.0 <= param_lambda <= 1.0

        node_distribution_hash = hash(str(param_alpha) + str(param_phi) + str(param_beta) + str(param_lambda) + str(hash(self)))

        if node_distribution_hash in self.distributions_by_hash:
            return self.distributions_by_hash[node_distribution_hash]

        node_distribution: dict[int, float] = {}

        if self._is_terminal_node:
            node_distribution[self._hash] = 1.0
            return node_distribution

        percent_find_optimal = (1.0 / self._number_of_terminal_nodes) ** ((1.0 - param_alpha) / param_alpha)
        percent_not_find_optimal = 1.0 - percent_find_optimal

        percent_remove_dominance = param_lambda
        percent_not_remove_dominance = 1.0 - param_lambda

        # TODO still need to handle dropping off optimal terminal nodes of more items
        for optimal_terminal_node in self._optimal_terminal_nodes:
            node_distribution[optimal_terminal_node] = percent_find_optimal / self._number_of_optimal_terminal_nodes

        if self._child_nodes:

            transformed_divisor_all = sum((knapsack_item.density ** (param_phi / (1.0 - param_phi))) * (knapsack_item.weight ** (param_beta / (1.0 - param_beta))) for knapsack_item, _ in self._child_nodes)  # TODO make this  knapsack_item.transformed_weight(phi, beta) so it can be used everywhere 
            transformed_divisor_non_dominated = sum((knapsack_item.density ** (param_phi / (1.0 - param_phi))) * (knapsack_item.weight ** (param_beta / (1.0 - param_beta))) if hash(knapsack_item) in self._non_dominated_items else 0.0 for knapsack_item, _ in self._child_nodes)

            for knapsack_item, child_node in self._child_nodes:
                child_distribution = child_node.get_node_distribution(param_alpha, param_phi, param_beta, param_lambda)
                for knapsack_problem_hash, distribution in child_distribution.items():
                    if knapsack_problem_hash not in node_distribution:
                        node_distribution[knapsack_problem_hash] = 0.0
                    node_distribution[knapsack_problem_hash] += percent_not_find_optimal * percent_not_remove_dominance * ((knapsack_item.density ** (param_phi / (1.0 - param_phi))) * (knapsack_item.weight ** (param_beta / (1.0 - param_beta)))) / transformed_divisor_all * distribution

                    # Add the additional weights for non-dominate items
                    if hash(knapsack_item) in self._non_dominated_items:
                        node_distribution[knapsack_problem_hash] += percent_not_find_optimal * percent_remove_dominance * ((knapsack_item.density ** (param_phi / (1.0 - param_phi))) * (knapsack_item.weight ** (param_beta / (1.0 - param_beta)))) / transformed_divisor_non_dominated * distribution

        if not math.isclose(sum(node_distribution.values()), 1.00):
            raise Exception('node distribution must equal 1')

        self.distributions_by_hash[node_distribution_hash] = node_distribution

        return self.distributions_by_hash[node_distribution_hash]
