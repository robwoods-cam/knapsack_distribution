"""
Knapsack Choice Distribution Tool.

Provides classes for the calculation of probabilistic choice distribution in knapsack problems.
See README.md for full documentation and examples.

Copyright
---------
© 2025 Robert Woods - Code and implementation  
© 2025 Roman Berlanger - Model and concept  

License
-------
This program is free software: you can redistribute it and/or modify it under the terms of the GNU Affero
General Public License as published by the Free Software Foundation, version 3.

See README.md and LICENSE for further details.
"""

import sys
import platform
import math
import hashlib
from enum import Enum, auto


# Enforce Python version
if sys.version_info < (3, 14):
    sys.exit("Python 3.14 or later is required.")

# Enforce Python architecture
if platform.architecture()[0] != "64bit":    
    sys.exit("Python 64-bit is required.")

# The major and minor version numbers should match the model version. Patch should be used for fixes and features
# added to the code.
__version__ = "2.0.0"


class ProblemType(Enum):
    """ The types of Knapsack Problem.
    
    Optimisation requires finding the maximum net value of a feasible selection of items.
    Decision requires finding any feasible selection of items, if it exists, to state (True or False) that a target
    net value can be reached.
    A feasible selection of items requires the net weight to be less than or equal to the capacity."""
    OPTIMISATION = auto()
    DECISION = auto()


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
    knapsack_item_id:
        an id for the knapsack item unique to the knapsack problem (not to the value and weight of the knapsack item)
    __hash__ : int
        unique hash for the knapsack item (repeated items have a unique hash based on their item id)


    Notes
    -----
    * `__eq__` and `__gt__` are overridden to allow sorting of `KnapsackItem`s to allow a `KnapsackProblem` to create
    a unique hash based on the items available to allow for nodes to merge and save computational resources.
    * self == other and hash(self) == hash(other) may give different results. __eq__ only compares the value and 
    weight of the item, allowing for sorting. However, the hash looks for unique items for branching.
    This means that `KnapsackItem`s should not be used as keys or in sets.
    """
    _value: int
    _weight: int
    _density: float
    _knapsack_item_id: int
    _full_hash: bytes
    _dominating_knapsack_item_hashes: set[int] | None

    # class attributes
    _knapsack_items_count: int = 0

    @classmethod
    def create_from_list(cls, values: list[int], weights: list[int]) -> list[KnapsackItem]:
        """ creates and returns a `list` of `KnapsackItem` from an equal list of `values` and `weights`

        Parameters
        ----------
        values : list[int]
            The values of the `KnapsackItem`s to be created in order
        weights : list[int]
            The weights of the `KnapsackItem`s to be created in order

        Raises
        ------
        TypeError
            if `values` and `weights` are not both `list`s of `int`s

        ValueError
            if the length of `values` and `weights` are not both equal

        Returns
        -------
            knapsack_items : list[KnapsackItem]
                the newly created `KnapsackItem`s

        """
        if not (isinstance(values, list) and all(isinstance(value, int) for value in values)):
            raise TypeError("values must be a list of ints.")
        if not (isinstance(weights, list) and all(isinstance(weight, int) for weight in weights)):
            raise TypeError("weights must be a list of ints.")
        if len(values) != len(weights):
            raise ValueError(f"Length of values and weights must be equal, got {len(values)} (values) and {len(weights)} (weights).")

        knapsack_items: list[KnapsackItem] = []
        for value, weight in zip(values, weights):
            knapsack_items.append(KnapsackItem(value, weight))

        return knapsack_items

    def __init__(self, value: int, weight: int) -> None:
        """ creates a `KnapsackItem`

        Parameters
        ----------
        value : int
            The value of the `KnapsackItem
        weights : int
            The weight of the `KnapsackItem`

        Raises
        ------
        TypeError
            if `value` and `weight` are not both `int`s
        ValueError
            if `value` is not positive or `weight` not non-negative
        """

        if not isinstance(value, int):
            raise TypeError(f"value must be of type int, is {type(value)}.")
        
        if value < 0:
            raise ValueError(f"value must be non-negative, is {value}.")        
        
        if not isinstance(weight, int):
            raise TypeError(f"weight must be of type int, is {type(weight)}.")
        
        if weight <= 0:
            raise ValueError(f"wight must be non-negative, is {weight}.")

        self._value = value
        self._weight = weight
        self._density = self._value / self._weight
        self._knapsack_item_id = KnapsackItem._knapsack_items_count
        # Each item gets it own unique hash, even if it matches in value and weight. Merging of identical nodes happens in final print processing
        hash_string = str(self._value) + "," + str(self._weight) + "," + str(self._knapsack_item_id)
        self._full_hash = hashlib.sha256(hash_string.encode("utf-8")).digest()
        self._dominating_knapsack_item_hashes = None

        KnapsackItem._knapsack_items_count += 1

    def __eq__(self, other: object) -> bool:
        """ Note that self == other and hash(self) == hash(other) do not return the same result """
        if not isinstance(other, KnapsackItem):
            raise NotImplementedError(f"Cannot compared `KnapsackItem` to type {type(other)}.")
        return self._density == other.density and self._value == other.value

    def __gt__(self, other: object) -> bool:
        if not isinstance(other, KnapsackItem):
            raise NotImplementedError(f"Cannot compared `KnapsackItem` to type {type(other)}.")
        return self._density > other.density or (self._density == other.density and self._value > other.value)

    def __hash__(self) -> int:
        """ Python uses 61 bit hashes (on 64-bit implementations), so we use the last 7 bytes of the SHA-256 as the hash. 
        
        This only works on 64-bit implementations of Python."""
        return int.from_bytes(self._full_hash[:7], 'big')

    def __str__(self) -> str:
        return f'(v: {self._value}, w: {self._weight})'

    def __repr__(self) -> str:
        return f'KnapsackItem(value = {self._value}, weight = {self._weight})'

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
    
    @property
    def knapsack_item_id(self) -> int:
        """ the id of the knapsack item unique to the knapsack problem """
        return self._knapsack_item_id

    @property
    def knapsack_detailed_repr(self) -> str:
        """ Returns the representation including the knapsack_item_id """
        return f'KnapsackItem(value = {self._value}, weight = {self._weight}, id = {self._knapsack_item_id})'

    def set_dominance(self, knapsack_items: list[KnapsackItem]) -> None:
        """ Sets the `KnapsackItem`s that dominate this `KnapsackItem`.
        
        Sets `_dominating_knapsack_item_hashes` to a `set` of `hash`es for all `knapsack_item`s in `knapsack_items` that dominate it.
        A knapsack item dominates another if both the value is greater than the other value and the weight is less than the other weight and at least one is strictly.

        Parameters
        ----------
        knapsack_items : list[KnapsackItem]
            A list of `KnapsacksItems` to be checked for dominance

        Raises
        ------
        TypeError
            if a list of `KnapsackItem`s is not supplied
        ValueError
            if the list of dominating `KnapsackItem`s includes this `KnapsackItem` (self dominance)

        Returns
        -------
            None
        """
        if not (isinstance(knapsack_items, list) and all(isinstance(knapsack_item, KnapsackItem) for knapsack_item in knapsack_items)):
            raise TypeError("knapsack_items must be a list of `KnapsackItem`")

        if hash(self) in [hash(knapsack_item) for knapsack_item in knapsack_items]:
            raise ValueError("`KnapsackItem` cannot be dominated by itself.")

        # must use hashes for sets due to the reworked hash function
        self._dominating_knapsack_item_hashes = set()

        for knapsack_item in knapsack_items:
            if (knapsack_item.value > self.value and knapsack_item.weight <= self.weight) or (knapsack_item.value >= self.value and knapsack_item.weight < self.weight) or (knapsack_item == self and knapsack_item.knapsack_item_id < self.knapsack_item_id):
                self._dominating_knapsack_item_hashes.add(hash(knapsack_item))

    def check_dominance(self, knapsack_items: list[KnapsackItem]) -> bool:
        """ Checks to see if any `KnapsackItem` in `knapsack_items` dominates this `KnapsackItem`.
        
        A knapsack item dominates another if both the value is greater than the other value and the weight is less than the other weight and at least one is strictly.
        `set_dominance` must be run prior to `check_dominance`
        
        Parameters
        ----------
        knapsack_items : list[KnapsackItem]
            A list of `KnapsacksItems` to be checked for dominance

        Raises
        ------
        TypeError
            if a list of `KnapsackItem`s is not supplied
        RuntimeError
            if `check_dominance` is called before dominance is set (using `set_dominance`)

        Returns
            is dominated : bool
            if the item is dominated by any of the `KnapsackItems` in `knapsack_items`
        -------

        """
        if not (isinstance(knapsack_items, list) and all(isinstance(knapsack_item, KnapsackItem) for knapsack_item in knapsack_items)):
            raise TypeError("knapsack_items must be a list of `KnapsackItem`.")

        if self._dominating_knapsack_item_hashes is None:
            raise RuntimeError('Dominating knapsack items have not been set yet. Use `set_dominance()` first.')

        for knapsack_item in knapsack_items:
            if hash(knapsack_item) in self._dominating_knapsack_item_hashes:
                return True

        return False


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
    master_knapsack : KnapsackProblem | None
        the original `KnapsackProblem` which this node spawned from. If this is the original node, `master_knapsack` will be `None`
    raw_pick_weights: dict[int, float]
        the raw pick weight for each `KnapsackItem` based on the greedy algorithm without transformations for beta, alpha, delta. This prevents recomputation of densities
    child_nodes : list[KnapsackProblem]  | None
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
    * `create` should be used rather than `__init__`
    * hash includes the master_knapsack, this means if we get to an identical node but from a different starting knapsack, everything will be processed again.
    * self == other and hash(self) == hash(other) may give different results. __eq__ only compares the value and 
    weight of the item, allowing for sorting. However, the hash looks for unique items for branching.
    This means that `KnapsackProblem`s should not be used as keys or in sets.
    """

    _knapsack_items: list[KnapsackItem]
    _knapsack_capacity: int
    _full_hash: bytes
    _standing_value: int
    _standing_knapsack_items: list[KnapsackItem]
    _master_knapsack: KnapsackProblem | None
    _knapsack_items_hashes: list[int]
    _non_dominated_items: set[int]
    _included_dominated_items: list[KnapsackItem]
    _is_dominated: bool
    _terminal_nodes: set[int]
    _child_nodes: list[tuple[KnapsackItem, KnapsackProblem]] | None
    _is_terminal_node: bool
    _optimal_terminal_nodes: set[int]
    _number_of_terminal_nodes: int | None
    _optimal_terminal_node_value: int
    _number_of_optimal_terminal_nodes: int | None

    # class attributes
    problems_by_hash: dict[int, KnapsackProblem] = {}
    distributions_by_hash: dict[int, dict[int, float]] = {}

    @classmethod
    def create(cls, knapsack_items: list[KnapsackItem], knapsack_capacity: int, standing_value: int = 0, standing_knapsack_items: list[KnapsackItem] = [], master_knapsack: KnapsackProblem | None = None) -> KnapsackProblem:
        """ `KnapsackProblem.create()` should be used rather than `__init__`

        If a node (`KnapsackProblem`) already exists, the existing instance will be returned, rather than creating a new one.
        If it does not, a new instance will be created.
        This allows for the efficient branching.

        Parameters
        ----------
        knapsack_items : list[KnapsackItem]
            a `list` of all the possible `KnapsackItem`s that should be considered
        knapsack_capacity : int
            the weight capacity of the `KnapsackProblem`, the remaining capacity for a child node (sub problem)
        standing_value : int, default 0
            the sum of values of items already included in the knapsack
        master_knapsack : KnapsackProblem | None
            the original `KnapsackProblem` which this node spawned from. If this is the original node, `master_knapsack` will be `None`
        
        Raises
        ------
        TypeError
            if `knapsack_items` and `standing_knapsack_items` are not a list of `KnapsackItem`s, knapsack_capacity and standing_value are not `int`s,
            or `master_knapsack` is not either a `KnapsackProblem` or `None.
        ValueError
            if `knapsack_capacity` or `standing_value` are negative.

        Returns
        -------
            KnapsackProblem
        """
        if not (isinstance(knapsack_items, list) and all(isinstance(knapsack_item, KnapsackItem) for knapsack_item in knapsack_items)):
            raise TypeError("`knapsack_items` must be a `list` of `KnapsackItem`s.")
        
        if not isinstance(knapsack_capacity, int):
            raise TypeError(f"`knapsack_capacity` must be int, is {type(knapsack_capacity)}")
        
        if knapsack_capacity < 0:
            raise ValueError(f"`knapsack_capacity` must be positive, is {knapsack_capacity}.")
        
        if not isinstance(standing_value, int):
            raise TypeError(f"`standing_value` must be int, is {type(standing_value)}")
        
        if standing_value < 0:
            raise ValueError(f"`standing_value` must be non-negative, is {standing_value}.")        
        
        if not (isinstance(standing_knapsack_items, list) and all(isinstance(knapsack_item, KnapsackItem) for knapsack_item in standing_knapsack_items)):
            raise TypeError("`standing_knapsack_items` must be a `list` of `KnapsackItem`s.")
        
        if not isinstance(master_knapsack, KnapsackProblem | None):
            raise TypeError(f"`master_knapsack` must be of type `KnapsackProblem` or is None, is {type(master_knapsack)}.")

        hash_string = str(sorted(knapsack_items)) + "," + str(knapsack_capacity) + "," + str(standing_value) + "," + str([hash(knapsack_item) for knapsack_item in sorted(standing_knapsack_items)]) + "," + str(hash(master_knapsack))
        knapsack_full_hash = hashlib.sha256(hash_string.encode("utf-8")).digest()
        knapsack_hash = int.from_bytes(knapsack_full_hash[:7], 'big')

        if knapsack_hash in cls.problems_by_hash:
            return cls.problems_by_hash[knapsack_hash]

        return KnapsackProblem(knapsack_items, knapsack_capacity, knapsack_full_hash, standing_value, standing_knapsack_items, master_knapsack)

    def __init__(self, knapsack_items: list[KnapsackItem], knapsack_capacity: int, knapsack_hash: bytes, standing_value: int = 0, standing_knapsack_items: list[KnapsackItem] = [], master_knapsack: KnapsackProblem | None = None) -> None:
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
        knapsack_hash : bytes
            a unique value for the `KnapsackProblem`, this allows for multiple pathways to reach the same node and not require recalculation
        standing_value : int, default 0
            the sum of values of items already included in the knapsack
        master_knapsack : KnapsackProblem | None
            the original `KnapsackProblem` which this node spawned from. If this is the original node, `master_knapsack` will be `None`

                
        Raises
        ------
        TypeError
            if `knapsack_items` and `standing_knapsack_items` are not a list of `KnapsackItem`s, `knapsack_hash` is not of type `bytes`,
            knapsack_capacity and standing_value are not `int`s, or `master_knapsack` is not either a `KnapsackProblem` or `None.
        ValueError
            if `knapsack_capacity` or `standing_value` are negative.
        """
        # TODO add to docstring

        if not (isinstance(knapsack_items, list) and all(isinstance(knapsack_item, KnapsackItem) for knapsack_item in knapsack_items)):
            raise TypeError("`knapsack_items` must be a `list` of `KnapsackItem`s.")
        
        if not isinstance(knapsack_capacity, int):
            raise TypeError(f"`knapsack_capacity` must be int, is {type(knapsack_capacity)}")
        
        if not isinstance(knapsack_hash, bytes):
            raise TypeError(f"`knapsack_capacity` must be `bytes`, is {type(knapsack_hash)}")
        
        if knapsack_capacity < 0:
            raise ValueError(f"`knapsack_capacity` must be positive, is {knapsack_capacity}.")
        
        if not isinstance(standing_value, int):
            raise TypeError(f"`standing_value` must be int, is {type(standing_value)}")
        
        if standing_value < 0:
            raise ValueError(f"`standing_value` must be non-negative, is {standing_value}.")        
        
        if not (isinstance(standing_knapsack_items, list) and all(isinstance(knapsack_item, KnapsackItem) for knapsack_item in standing_knapsack_items)):
            raise TypeError("`standing_knapsack_items` must be a `list` of `KnapsackItem`s.")
        
        if not isinstance(master_knapsack, KnapsackProblem | None):
            raise TypeError(f"`master_knapsack` must be of type `KnapsackProblem` or is None, is {type(master_knapsack)}.")

        self._knapsack_items = knapsack_items
        self._knapsack_capacity = knapsack_capacity
        self._full_hash = knapsack_hash
        self._standing_value = standing_value
        self._standing_knapsack_items = standing_knapsack_items
        self._master_knapsack = master_knapsack

        if master_knapsack is None:
            for i, knapsack_item in enumerate(self._knapsack_items):
                knapsack_item.set_dominance(self._knapsack_items[:i] + self._knapsack_items[i + 1:])
            
            self._knapsack_items_hashes = [hash(knapsack_item) for knapsack_item in self._knapsack_items]

        self._non_dominated_items = set()
        for i, knapsack_item in enumerate(self._knapsack_items):
            if not knapsack_item.check_dominance(self._knapsack_items[:i] + self._knapsack_items[i + 1:]):
                self._non_dominated_items.add(hash(knapsack_item))
 
        self._included_dominated_items = [standing_knapsack_item for standing_knapsack_item in self._standing_knapsack_items if standing_knapsack_item.check_dominance(self._knapsack_items)]
        self._is_dominated = len(self._included_dominated_items) >= 1

        # is I need the density of the item included, the child node only have the items remaining, not included
        self._child_nodes = self._create_child_nodes()
        
        self._is_terminal_node = self._child_nodes is None
        
        self._terminal_nodes = set()
        if self._child_nodes:
            for _, child_node in self._child_nodes:
                if child_node._is_terminal_node:
                    self._terminal_nodes.add(hash(child_node))
                else:
                    self._terminal_nodes.update(child_node._terminal_nodes)

        self._number_of_terminal_nodes = None if self._is_terminal_node else len(self._terminal_nodes)  # TODO pick either if self._is_terminal_node or if self._child_nodes is None
        
        self._optimal_terminal_node_value = self._standing_value if not self._child_nodes else max(child_node._optimal_terminal_node_value for _, child_node in self._child_nodes)
        
        self._optimal_terminal_nodes = set()
        if self._child_nodes:
            for _, child_node in self._child_nodes:
                if child_node._optimal_terminal_node_value == self._optimal_terminal_node_value:
                    if child_node._is_terminal_node:
                        self._optimal_terminal_nodes.add(hash(child_node))
                    else:
                        self._optimal_terminal_nodes.update(child_node._optimal_terminal_nodes)
                elif child_node._optimal_terminal_node_value > self._optimal_terminal_node_value:
                    raise ValueError('There should be no child nodes with value greater than the optimal terminal node value')

        self._number_of_optimal_terminal_nodes = None if self._is_terminal_node else len(self._optimal_terminal_nodes)

        self.problems_by_hash[hash(self)] = self

    def __hash__(self) -> int:
        """ Python uses 61 bit hashes (on 64-bit implementations), so we use the last 7 bytes of the SHA-256 as the hash. 
        
        This only works on 64-bit implementations of Python."""
        return int.from_bytes(self._full_hash[:7], 'big')

    def _create_child_nodes(self) -> list[tuple[KnapsackItem, KnapsackProblem]] | None:
        """ recursively create all the child nodes from this node """
        if len(self._knapsack_items) == 1:
            return None

        child_nodes: list[tuple[KnapsackItem, KnapsackProblem]] = []

        for i, knapsack_item in enumerate(self._knapsack_items):
            knapsack_capacity = self._knapsack_capacity - self._knapsack_items[i].weight
            if knapsack_capacity >= 0:
                master_knapsack: KnapsackProblem = self._master_knapsack if self._master_knapsack else self
                standing_value = self._standing_value + self._knapsack_items[i].value
                standing_knapsack_items = self._standing_knapsack_items + [self._knapsack_items[i]]
                child_node = KnapsackProblem.create(self._knapsack_items[:i] + self._knapsack_items[i + 1:],
                                                    knapsack_capacity, standing_value, standing_knapsack_items,
                                                    master_knapsack)
                child_nodes.append((knapsack_item, child_node))
        
        return child_nodes if child_nodes else None
    
    @property
    def knapsack_items(self) -> list[KnapsackItem]:
        """ List of all items which can be considered for addition to this node.
        
        This is NOT the items included in the knapsack so far."""
        return self._knapsack_items
    
    @property
    def knapsack_items_hashes(self) -> list[int]:
        """ The hashes of each item. Only included for master nodes. 
        
        Hashes are unique for each item, even if they are identical in value and weight."""
        if self._master_knapsack is not None:
            raise Exception("Non-master nodes do not have item hashes recorded.")

        return self._knapsack_items_hashes
    
    @property
    def knapsack_items_repr_hashes(self) -> list[int]:
        """ The repr of each item. Only included for master nodes. This merges identical items."""
        if self._master_knapsack is not None:
            raise Exception("Non-master nodes do not have item hashes recorded.")

        return [hash(repr(knapsack_item)) for knapsack_item in self._knapsack_items]
    
    @property
    def is_terminal_node(self) -> bool:
        """ Is this node a terminal node.
        
        A terminal node has no further child nodes, either because no further items fit or there are no items left.
        This is also known as a capacity-constrained node or knapsack."""
        return self._is_terminal_node

    def get_node_distribution(self, param_beta: float, param_alpha: float, param_gamma: float, param_delta: float, problem_type: ProblemType = ProblemType.OPTIMISATION, value_threshold: int | None = None) -> dict[int, float]:
        """
        Get the distribution (as a percentage of 1) that someone will end in each terminal node from this given Knapsack Problem.
        This is based on the supplied alpha, beta, gamma, and delta parameters.
        Node distribution only considers feasible (at or under capacity) terminal (no more items will fit in the knapsack) nodes.

        Parameters
        ----------
        param_beta : float
            density preference/local optimisation parameter
        param_alpha : float
            search/global optimisation parameter
            alpha = 0 is a special case where we do not jump to the optimal at all, used for 'item-by-item' search
        param_gamma : float
            complexity aversion/weight preference parameter
        param_delta : float
            item-level rationality parameter
        problem_type: ProblemType
            if the problem is optimisation or decision (default = optimisation)
        value_threshold: int | None
            the value target for the decision problem

        Raises
        ------
        RuntimeError
            if the sum of node distribution is not close to 1
        ValueError("Cannot process node distribution for a node which _number_of_terminal_nodes is set to None")
        raise ValueError(f"Unexpected problem type: {problem_type}")

        Returns
        -------
        node_distribution : dict[int, float]
            A dict of the feasible terminal nodes with the percentage that one will end in each terminal node based on `beta`
        """
        # TODO add to docstring

        if not isinstance(param_beta, float):
            raise TypeError(f"`param_beta` must be of type float, but is {type(param_beta)}.")
        if not 0.0 <= param_beta < 1.0:
            raise ValueError(f"`param_beta` be greater than or equal to 0.0 and less than 1.0, but is {param_beta}.")
        
        if not isinstance(param_gamma, float):
            raise TypeError(f"`param_gamma` must be of type float, but is {type(param_gamma)}.")
        if not 0.0 <= param_gamma < 1.0:
            raise ValueError(f"`param_gamma` be greater than or equal to 0.0 and less than 1.0, but is {param_gamma}.")
        
        if not isinstance(param_delta, float):
            raise TypeError(f"`param_delta` must be of type float, but is {type(param_delta)}.")
        if not 0.0 <= param_delta <= 1.0:            
            raise ValueError(f"`param_delta` be greater than or equal to 0.0 and less than or equal to 1.0, but is {param_delta}.")

        if not isinstance(param_alpha, float):
            raise TypeError(f"`param_alpha` must be of type float, but is {type(param_alpha)}.")
        
        if not isinstance(problem_type, ProblemType):
            raise TypeError(f"`problem_type` must be of type `ProblemType`, but is {type(problem_type)}.")
        
        if problem_type is ProblemType.DECISION:
            if not 0.0 <= param_alpha <= 1.0:
                raise ValueError(f"`param_alpha` be greater than or equal to 0.0 and less than or equal to 1.0 for the decision problem, but is {param_alpha}.")
        
            if not isinstance(value_threshold, int):
                raise TypeError(f"`value_threshold` must be int for decision problem, is {type(value_threshold)}.")
            if value_threshold < 0:
                raise ValueError(f"`value_threshold` must be positive for decision problem, is {value_threshold}.")
        
        elif problem_type is ProblemType.OPTIMISATION:
            if not 0.0 < param_alpha <= 1.0:
                raise ValueError(f"`param_alpha` be greater than 0.0 and less than or equal to 1.0 for the optimisation problem, but is {param_alpha}.")
            
            if value_threshold is not None:
                raise TypeError(f"`value_threshold` must be None for optimisation problem, is {type(value_threshold)}.")
    
        else:
            raise ValueError(f"`problem_type` expected to be `DECISION` or `OPTIMISATION`, is {problem_type}.")

        hash_string = str(param_beta)  + "," + str(param_alpha) + "," + str(param_gamma) + "," + str(param_delta) + "," + str(problem_type) + "," + str(hash(self))
        node_distribution_hash = int(hashlib.sha256(hash_string.encode("utf-8")).hexdigest(), 16)
        if node_distribution_hash in self.distributions_by_hash:
            return self.distributions_by_hash[node_distribution_hash]

        node_distribution: dict[int, float] = {}

        if self._is_terminal_node:
            node_distribution[hash(self)] = 1.0
            return node_distribution

        if self._number_of_terminal_nodes is None:
            raise ValueError("Cannot process node distribution for a node which _number_of_terminal_nodes is set to None")
        
        # Brute force search for optima / witness
        
        # This should be considered as such:
        # The terminal node includes no items which are:
        #   - dominated at that node
        #   - and not yet included

        # Non-dominated terminal nodes is from the perspective that no items are added from this node onwards which are dominated.
        # Dominated items may already have been added, as long as no further items are added
        # Mathematically, at the terminal node, there are no-dominated items included unless the item was already included at this node
        number_of_non_dominated_terminal_nodes = len([terminal_node for terminal_node in self._terminal_nodes if not KnapsackProblem.problems_by_hash[terminal_node]._is_dominated or all(terminal_included_dominated_item in self._included_dominated_items for terminal_included_dominated_item in KnapsackProblem.problems_by_hash[terminal_node]._included_dominated_items)])
        non_dominated_optimal_terminal_nodes = [terminal_node for terminal_node in self._optimal_terminal_nodes if not KnapsackProblem.problems_by_hash[terminal_node]._is_dominated or all(terminal_included_dominated_item in self._included_dominated_items for terminal_included_dominated_item in KnapsackProblem.problems_by_hash[terminal_node]._included_dominated_items)]
        # self._number_of_non_dominated_terminal_nodes = number_of_non_dominated_terminal_nodes
        
        # Check depending on what problem type if we need to search all terminal nodes and find the best (optimisation), or just find a terminal which meets a threshold (decision)
        if problem_type is ProblemType.OPTIMISATION:
            percent_find_optimal_full_set = ((1 - param_delta) * math.exp((1 - self._number_of_terminal_nodes) * ((1 - param_alpha) / param_alpha)))
            percent_find_optimal_non_dominated = (param_delta * math.exp((1 - number_of_non_dominated_terminal_nodes) * ((1 - param_alpha) / param_alpha)))
        
        elif problem_type is ProblemType.DECISION:
            if value_threshold is None:
                raise ValueError("`value_threshold` must be set in Decision task.")  # TODO tidy
            if param_alpha == 0.0:
                percent_find_optimal_full_set = 0.0
                percent_find_optimal_non_dominated = 0.0
            else:
                distribution_search_delta_0 = self.get_node_distribution(0.0, 0.0, 0.0, 0.0, ProblemType.DECISION, value_threshold)
                distribution_search_delta_1 = self.get_node_distribution(0.0, 0.0, 0.0, 1.0, ProblemType.DECISION, value_threshold)
                percent_witness_found_delta_0 = sum([distribution_percentage for knapsack_problem_hash, distribution_percentage in distribution_search_delta_0.items() if KnapsackProblem.problems_by_hash[knapsack_problem_hash]._standing_value >= value_threshold])
                percent_witness_found_delta_1 = sum([distribution_percentage for knapsack_problem_hash, distribution_percentage in distribution_search_delta_1.items() if KnapsackProblem.problems_by_hash[knapsack_problem_hash]._standing_value >= value_threshold])
                
                # distribution_search_delta_delta = self.get_node_distribution(0.0, 0.0, 0.0, param_delta, ProblemType.DECISION, value_threshold)
                # percent_witness_found = sum([distribution_percentage for knapsack_problem_hash, distribution_percentage in distribution_search_delta_delta.items() if KnapsackProblem.problems_by_hash[knapsack_problem_hash]._standing_value >= value_threshold])

                # # HACK to use true delta
                # percent_witness_found_delta_0 = percent_witness_found
                # percent_witness_found_delta_1 = percent_witness_found

                percent_find_optimal_full_set = ((1 - param_delta) * (percent_witness_found_delta_0 ** ((1 - param_alpha) / param_alpha)))
                percent_find_optimal_non_dominated = (param_delta * (percent_witness_found_delta_1 ** ((1 - param_alpha) / param_alpha)))
        
        else:
            raise ValueError(f"Unexpected problem type: {problem_type}")
        
        percent_not_find_optimal = 1.0 - (percent_find_optimal_full_set + percent_find_optimal_non_dominated)

        percent_remove_dominance = param_delta
        percent_not_remove_dominance = 1.0 - param_delta

        if problem_type is ProblemType.OPTIMISATION:
            for optimal_terminal_node in self._optimal_terminal_nodes:
                if self._number_of_optimal_terminal_nodes is None:
                    raise Exception("_number_of_optimal_terminal_nodes should not be None")
                node_distribution[optimal_terminal_node] = percent_find_optimal_full_set / self._number_of_optimal_terminal_nodes
            
            for optimal_non_dominated_terminal_node in non_dominated_optimal_terminal_nodes:
                node_distribution[optimal_non_dominated_terminal_node] += percent_find_optimal_non_dominated / len(non_dominated_optimal_terminal_nodes)
        
        elif problem_type is ProblemType.DECISION:
            if value_threshold is None:
                raise ValueError("`value_threshold` must be set in Decision task.")  # TODO tidy
            if param_alpha != 0.0:  # TODO move this up so all in the same if part
                for knapsack_problem_hash, distribution_percentage in distribution_search_delta_0.items():
                    if KnapsackProblem.problems_by_hash[knapsack_problem_hash]._standing_value >= value_threshold:
                        node_distribution[knapsack_problem_hash] = percent_find_optimal_full_set * (distribution_percentage / percent_witness_found_delta_0)
                
                for knapsack_problem_hash, distribution_percentage in distribution_search_delta_1.items():
                    if KnapsackProblem.problems_by_hash[knapsack_problem_hash]._standing_value >= value_threshold:
                        node_distribution[knapsack_problem_hash] += percent_find_optimal_non_dominated * (distribution_percentage / percent_witness_found_delta_1)

        # Brute search failed - Add an item to simplify the task
        if self._child_nodes:

            transformed_divisor_all = sum((knapsack_item.density ** (param_beta / (1.0 - param_beta))) * (knapsack_item.weight ** (param_gamma / (1.0 - param_gamma))) for knapsack_item, _ in self._child_nodes)  # TODO make this  knapsack_item.transformed_weight(alpha, gamma) so it can be used everywhere 
            transformed_divisor_non_dominated = sum((knapsack_item.density ** (param_beta / (1.0 - param_beta))) * (knapsack_item.weight ** (param_gamma / (1.0 - param_gamma))) if hash(knapsack_item) in self._non_dominated_items else 0.0 for knapsack_item, _ in self._child_nodes)

            for knapsack_item, child_node in self._child_nodes:
                child_distribution = child_node.get_node_distribution(param_beta, param_alpha, param_gamma, param_delta, problem_type, value_threshold)
                for knapsack_problem_hash, distribution in child_distribution.items():
                    if knapsack_problem_hash not in node_distribution:
                        node_distribution[knapsack_problem_hash] = 0.0
                    node_distribution[knapsack_problem_hash] += percent_not_find_optimal * percent_not_remove_dominance * ((knapsack_item.density ** (param_beta / (1.0 - param_beta))) * (knapsack_item.weight ** (param_gamma / (1.0 - param_gamma)))) / transformed_divisor_all * distribution

                    # Add the additional weights for non-dominate items
                    if hash(knapsack_item) in self._non_dominated_items:
                        node_distribution[knapsack_problem_hash] += percent_not_find_optimal * percent_remove_dominance * ((knapsack_item.density ** (param_beta / (1.0 - param_beta))) * (knapsack_item.weight ** (param_gamma / (1.0 - param_gamma)))) / transformed_divisor_non_dominated * distribution

        if not math.isclose(sum(node_distribution.values()), 1.00):
            raise RuntimeError('node distribution must equal 1')

        self.distributions_by_hash[node_distribution_hash] = node_distribution

        return self.distributions_by_hash[node_distribution_hash]


    def print_node_distribution(self, distribution: dict[int, float], parameters: tuple[float, float, float, float] | None = None, print_threshold: float = 0.0001) -> None:
        """ Print the knapsack node distribution with all relevant information.

        Prints the distribution (as a percentage of 1) that someone will end in each terminal node from this given Knapsack Problem.
        This is based on the supplied distribution, using the alpha, beta, gamma, and delta parameters to calculate the distribution.
        Node distribution only considers feasible (at or under capacity) terminal (no more items will fit in the knapsack) nodes.
        Nodes are converted back to the a 1 and 0 binary list of item inclusions, based on the order the items were supplied to the
        master node Knapsack.

        Also prints the ordered list of knapsack items and the count of total terminal nodes reached.

        Parameters
        ----------
        distribution : dict[int, float]
            the probability distribution of each node, by node hash and percentage
        parameters : tuple[float, float, float, float] | None
            the parameters used to calculate the distribution (default = None)
        print_threshold : float
            print any node with a distribution greater than to equal to the print threshold (default = 0.0001)

        Returns: None
        """
        print("Inputs\n")

        if parameters: print(f"Parameters: α = {parameters[0]}, β = {parameters[1]}, γ = {parameters[2]}, δ = {parameters[3]}\n")

        print("Knapsack Problem Variant: Optimisation\n")

        print("Items: " + ", ".join([str(knapsack_item) for knapsack_item in self.knapsack_items]) + "\n")

        print(f"Budget: {self._knapsack_capacity}\n")

        print("-------------------------------------\n")

        print("Output\n")

        print("Terminal Nodes (*** for optimal):")

        distribution = dict(sorted(distribution.items(), key=lambda x: x[1], reverse=True))

        for knapsack_problem_hash, distribution_percentage in distribution.items():
            if distribution_percentage > print_threshold:
                knapsack_problem = KnapsackProblem.problems_by_hash[knapsack_problem_hash]
                terminal_node_item_hashes = [hash(repr(terminal_node_knapsack_item)) for terminal_node_knapsack_item in knapsack_problem.knapsack_items]

                item_inclusions = [True] * len(self.knapsack_items)

                for terminal_node_item_hash in terminal_node_item_hashes:
                    index_offset = 0
                    while True:
                        knapsack_item_match_index = self.knapsack_items_repr_hashes.index(terminal_node_item_hash, index_offset)
                        if item_inclusions[knapsack_item_match_index] == True:
                            item_inclusions[knapsack_item_match_index] = False
                            break
                        else:
                            index_offset = knapsack_item_match_index

                item_inclusion_string = str([1 if item_included else 0 for item_included in item_inclusions])

                if item_inclusion_string != str([0 if hash(repr(master_node_knapsack_item)) in terminal_node_item_hashes else 1 for master_node_knapsack_item in self.knapsack_items]):
                    raise Exception("There is a difference between inclusion strings. This is HOPEFULLY as one method accounts for repeated items and the other does not. If this is occurring without repeated items, this is a problem.")
                
                if knapsack_problem._master_knapsack is None:
                    raise RuntimeError
                print(f"{item_inclusion_string} - Σv: {knapsack_problem._standing_value}, Σw: {knapsack_problem._master_knapsack._knapsack_capacity - knapsack_problem._knapsack_capacity} / {knapsack_problem._master_knapsack._knapsack_capacity} - {100.0 * distribution_percentage:.3f}%{" ***" if hash(knapsack_problem) in knapsack_problem._master_knapsack._optimal_terminal_nodes else ""}")
    
        print()
        print(f"Total Distribution: {sum(distribution.values())}\n")
        print(f"Number of Terminal Nodes: {len(distribution)}\n")


    def solve_decision_variant(self, param_beta: float, param_alpha: float, param_gamma: float, param_delta: float, value_threshold: int) -> float:
        # TODO add docstring here
        """
        Docstring for solve_decision_variant
        
        :param self: Description
        :param param_beta: Description
        :type param_beta: float
        :param param_alpha: Description
        :type param_alpha: float
        :param param_gamma: Description
        :type param_gamma: float
        :param param_delta: Description
        :type param_delta: float
        :param value_threshold: Description
        :type value_threshold: int
        :return: Description
        :rtype: float
        """

        if not isinstance(param_beta, float):
            raise TypeError(f"`param_beta` must be of type float, but is {type(param_beta)}.")
        if not 0.0 <= param_beta < 1.0:
            raise ValueError(f"`param_beta` be greater than or equal to 0.0 and less than 1.0, but is {param_beta}.")
        
        if not isinstance(param_alpha, float):
            raise TypeError(f"`param_alpha` must be of type float, but is {type(param_alpha)}.")
        if not 0.0 <= param_alpha <= 1.0:
            raise ValueError(f"`param_alpha` be greater than or equal to 0.0 and less than or equal to 1.0 for the decision problem, but is {param_alpha}.")
        
        if not isinstance(param_gamma, float):
            raise TypeError(f"`param_gamma` must be of type float, but is {type(param_gamma)}.")
        if not 0.0 <= param_gamma < 1.0:
            raise ValueError(f"`param_gamma` be greater than or equal to 0.0 and less than 1.0, but is {param_gamma}.")
        
        if not isinstance(param_delta, float):
            raise TypeError(f"`param_delta` must be of type float, but is {type(param_delta)}.")
        if not 0.0 <= param_delta <= 1.0:            
            raise ValueError(f"`param_delta` be greater than or equal to 0.0 and less than or equal to 1.0, but is {param_delta}.")
        
        distribution_search_delta_delta = self.get_node_distribution(param_beta, param_alpha, param_gamma, param_delta, ProblemType.DECISION, value_threshold)
        percent_witness_found = sum([distribution_percentage for knapsack_problem_hash, distribution_percentage in distribution_search_delta_delta.items() if KnapsackProblem.problems_by_hash[knapsack_problem_hash]._standing_value >= value_threshold])
        return percent_witness_found
