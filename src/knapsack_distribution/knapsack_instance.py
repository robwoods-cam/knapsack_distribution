"""
Knapsack Choice Distribution Tool.

Provides classes for the calculation of probabilistic choice distribution in knapsack problem instances.
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


import hashlib
import math

from .knapsack_item import KnapsackItem
from .problem_type import ProblemType

class KnapsackInstance():
    """ A class to represent a Knapsack Problem Instance.

    Attributes
    ----------
    knapsack_items : list[KnapsackItem]
        a `list` of all the possible `KnapsackItem`s that should be considered
    knapsack_capacity : int
        the weight capacity of the `KnapsackInstance`, the remaining capacity for a child node (sub instance)
    hash : int
        a unique value for the `KnapsackInstance`, this allows for multiple pathways to reach the same node and not require recalculation
    standing_value : int, default 0
        the sum of values of items already included in the knapsack
    master_knapsack : KnapsackInstance | None
        the original `KnapsackInstance` which this node spawned from. If this is the original node, `master_knapsack` will be `None`
    child_nodes : list[KnapsackInstance]  | None
        a `list` of all feasible (at or under capacity) sub `KnapsackInstance`s that can be created by including one of the `knapsack_items` 
    is_terminal_node : bool
        if there are no possible feasible `child_nodes`
    optimal_terminal_node : KnapsackInstance
        the optimal (highest `standing_value`) feasible `child_node`

    Methods
    -------
    **create** : *Callable*
        `create` should be used rather than `__init__`
    **get_node_distribution** : *Callable*
        Get the distribution that someone will end in each terminal node from this given Knapsack Instance.

    TODO print_node_distribution
    TODO solve_decision_variant

    Notes
    -----
    * `create` should be used rather than `__init__`
    * hash includes the master_knapsack, this means if we get to an identical node but from a different starting knapsack, everything will be processed again.
    * self == other and hash(self) == hash(other) may give different results. __eq__ only compares the value and 
    weight of the item, allowing for sorting. However, the hash looks for unique items for branching.
    This means that `KnapsackInstance`s should not be used as keys or in sets.
    """

    _knapsack_items: list[KnapsackItem]
    _knapsack_capacity: int
    _full_hash: bytes
    _standing_value: int
    _standing_knapsack_items: list[KnapsackItem]
    _master_knapsack: KnapsackInstance | None
    _non_dominated_items: set[int]
    _included_dominated_items: list[KnapsackItem]
    _is_dominated: bool
    _terminal_nodes: set[int]
    _child_nodes: list[tuple[KnapsackItem, KnapsackInstance]] | None
    _is_terminal_node: bool
    _optimal_terminal_nodes: set[int]
    _optimal_terminal_node_value: int

    # class attributes
    instance_by_hash: dict[int, KnapsackInstance] = {}
    distribution_by_hash: dict[int, dict[int, float]] = {}

    @staticmethod
    def _validate_knapsack_parameters(knapsack_items: list[KnapsackItem], knapsack_capacity: int, standing_value: int, standing_knapsack_items: list[KnapsackItem], master_knapsack: KnapsackInstance | None) -> None:
        """ Validate the type and value of `knapsack_items`, `knapsack_capacity`, `standing_value`, `standing_knapsack_items`, `master_knapsack` """
        
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
        
        if not isinstance(master_knapsack, KnapsackInstance | None):
            raise TypeError(f"`master_knapsack` must be of type `KnapsackInstance` or is None, is {type(master_knapsack)}.")

    @classmethod
    def create(cls, knapsack_items: list[KnapsackItem], knapsack_capacity: int, standing_value: int = 0, standing_knapsack_items: list[KnapsackItem] = [], master_knapsack: KnapsackInstance | None = None) -> KnapsackInstance:
        """ `KnapsackInstance.create()` should be used rather than `__init__`

        If a node (`KnapsackInstance`) already exists, the existing instance will be returned, rather than creating a new one.
        If it does not, a new instance will be created.
        This allows for the efficient branching.

        Parameters
        ----------
        knapsack_items : list[KnapsackItem]
            a `list` of all the possible `KnapsackItem`s that should be considered
        knapsack_capacity : int
            the weight capacity of the `KnapsackInstance`, the remaining capacity for a child node (sub instance)
        standing_value : int, default 0
            the sum of values of items already included in the knapsack
        master_knapsack : KnapsackInstance | None
            the original `KnapsackInstance` which this node spawned from. If this is the original node, `master_knapsack` will be `None`
        
        Raises
        ------
        TypeError
            if `knapsack_items` and `standing_knapsack_items` are not a list of `KnapsackItem`s, knapsack_capacity and standing_value are not `int`s,
            or `master_knapsack` is not either a `KnapsackInstance` or `None.
        ValueError
            if `knapsack_capacity` or `standing_value` are negative.

        Returns
        -------
            KnapsackInstance
        """
        cls._validate_knapsack_parameters(knapsack_items, knapsack_capacity, standing_value, standing_knapsack_items, master_knapsack)

        hash_string = str(sorted(knapsack_items)) + "," + str(knapsack_capacity) + "," + str(standing_value) + "," + str([hash(knapsack_item) for knapsack_item in sorted(standing_knapsack_items)]) + "," + str(hash(master_knapsack))
        knapsack_full_hash = hashlib.sha256(hash_string.encode("utf-8")).digest()
        knapsack_hash = int.from_bytes(knapsack_full_hash[:7], 'big')

        if knapsack_hash in cls.instance_by_hash:
            return cls.instance_by_hash[knapsack_hash]

        return KnapsackInstance(knapsack_items, knapsack_capacity, knapsack_full_hash, standing_value, standing_knapsack_items, master_knapsack)

    def __init__(self, knapsack_items: list[KnapsackItem], knapsack_capacity: int, knapsack_hash: bytes, standing_value: int = 0, standing_knapsack_items: list[KnapsackItem] = [], master_knapsack: KnapsackInstance | None = None) -> None:
        """
        Important
        ---------
        `KnapsackInstance.create()` should be used rather than `__init__`

        Parameters
        ----------
        knapsack_items : list[KnapsackItem]
            a `list` of all the possible `KnapsackItem`s that should be considered
        knapsack_capacity : int
            the weight capacity of the `KnapsackInstance`, the remaining capacity for a child node (sub instance)
        knapsack_hash : bytes
            a unique value for the `KnapsackInstance`, this allows for multiple pathways to reach the same node and not require recalculation
        standing_value : int, default 0
            the sum of values of items already included in the knapsack
        master_knapsack : KnapsackInstance | None
            the original `KnapsackInstance` which this node spawned from. If this is the original node, `master_knapsack` will be `None`

        Raises
        ------
        TypeError
            if `knapsack_items` and `standing_knapsack_items` are not a list of `KnapsackItem`s, `knapsack_hash` is not of type `bytes`,
            knapsack_capacity and standing_value are not `int`s, or `master_knapsack` is not either a `KnapsackInstance` or `None.
        ValueError
            if `knapsack_capacity` or `standing_value` are negative.
        """
        
        if not isinstance(knapsack_hash, bytes):
            raise TypeError(f"`knapsack_hash` must be `bytes`, is {type(knapsack_hash)}")
        
        self._validate_knapsack_parameters(knapsack_items, knapsack_capacity, standing_value, standing_knapsack_items, master_knapsack)

        self._knapsack_items = knapsack_items
        self._knapsack_capacity = knapsack_capacity
        self._full_hash = knapsack_hash
        self._standing_value = standing_value
        self._standing_knapsack_items = standing_knapsack_items
        self._master_knapsack = master_knapsack

        if master_knapsack is None:
            for i, knapsack_item in enumerate(self._knapsack_items):
                knapsack_item.set_dominance(self._knapsack_items[:i] + self._knapsack_items[i + 1:])

        self._non_dominated_items = set()
        for i, knapsack_item in enumerate(self._knapsack_items):
            if not knapsack_item.check_dominance(self._knapsack_items[:i] + self._knapsack_items[i + 1:]):
                self._non_dominated_items.add(hash(knapsack_item))
 
        self._included_dominated_items = [standing_knapsack_item for standing_knapsack_item in self._standing_knapsack_items if standing_knapsack_item.check_dominance(self._knapsack_items)]
        self._is_dominated = len(self._included_dominated_items) >= 1

        self._child_nodes = self._create_child_nodes()
        
        self._is_terminal_node = self._child_nodes is None
        
        self._terminal_nodes = set()
        if self._child_nodes:
            for _, child_node in self._child_nodes:
                if child_node._is_terminal_node:
                    self._terminal_nodes.add(hash(child_node))
                else:
                    self._terminal_nodes.update(child_node._terminal_nodes)

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

        self.instance_by_hash[hash(self)] = self

    def __hash__(self) -> int:
        """ Python uses 61 bit hashes (on 64-bit implementations), so we use the last 7 bytes of the SHA-256 as the hash. 
        
        This only works on 64-bit implementations of Python."""
        return int.from_bytes(self._full_hash[:7], 'big')

    def _create_child_nodes(self) -> list[tuple[KnapsackItem, KnapsackInstance]] | None:
        """ recursively create all the child nodes from this node """
        if len(self._knapsack_items) == 1:
            return None

        child_nodes: list[tuple[KnapsackItem, KnapsackInstance]] = []

        for i, knapsack_item in enumerate(self._knapsack_items):
            knapsack_capacity = self._knapsack_capacity - self._knapsack_items[i].weight
            if knapsack_capacity >= 0:
                master_knapsack: KnapsackInstance = self._master_knapsack if self._master_knapsack else self
                standing_value = self._standing_value + self._knapsack_items[i].value
                standing_knapsack_items = self._standing_knapsack_items + [self._knapsack_items[i]]
                child_node = KnapsackInstance.create(self._knapsack_items[:i] + self._knapsack_items[i + 1:],
                                                    knapsack_capacity, standing_value, standing_knapsack_items,
                                                    master_knapsack)
                child_nodes.append((knapsack_item, child_node))
        
        return child_nodes if child_nodes else None
    
    @property
    def knapsack_items(self) -> list[KnapsackItem]:
        """ List of all items which can be considered for addition to this node.
        
        This is **not** the items included in the knapsack so far."""
        return self._knapsack_items
    
    @property
    def knapsack_items_repr_hashes(self) -> list[int]:
        """ The hash of repr of each item. This is used to merge identical items as repr will give the same hash for identical items."""
        # if self._master_knapsack is not None:
        #     raise Exception("Non-master nodes do not have item hashes recorded.")

        return [hash(repr(knapsack_item)) for knapsack_item in self._knapsack_items]
    
    @property
    def is_terminal_node(self) -> bool:
        """ Is this node a terminal node.
        
        A terminal node has no further child nodes, either because no further items fit or there are no items left.
        This is also known as a capacity-constrained node or knapsack."""
        return self._is_terminal_node
    
    @property
    def _non_dominated_terminal_nodes(self) -> list[int]:
        """ Return the hashes of the non-dominated terminal nodes.
        
        Non-dominated terminal nodes is from the perspective that no items are added from this node onwards which are dominated.
        Dominated items may already have been added, as long as no further items are added.
        Mathematically, in these nodes, there are no-dominated items included unless the item was already included at this node.
        """
        return [terminal_node for terminal_node in self._terminal_nodes if not KnapsackInstance.instance_by_hash[terminal_node]._is_dominated or all(terminal_included_dominated_item in self._included_dominated_items for terminal_included_dominated_item in KnapsackInstance.instance_by_hash[terminal_node]._included_dominated_items)] 

    @property
    def _non_dominated_optimal_terminal_nodes(self) -> list[int]:
        """ Return the hashes of the non-dominated optimal terminal nodes. 
        
        Non-dominated terminal nodes is from the perspective that no items are added from this node onwards which are dominated.
        Dominated items may already have been added, as long as no further items are added.
        Mathematically, in these nodes, there are no-dominated items included unless the item was already included at this node.
        """
        return [terminal_node for terminal_node in self._optimal_terminal_nodes if not KnapsackInstance.instance_by_hash[terminal_node]._is_dominated or all(terminal_included_dominated_item in self._included_dominated_items for terminal_included_dominated_item in KnapsackInstance.instance_by_hash[terminal_node]._included_dominated_items)]

    @staticmethod
    def _validate_parameters_and_value_threshold(param_alpha: float, param_beta: float, param_gamma: float, param_delta: float, problem_type: ProblemType, value_threshold: int | None) -> None:
        """ Validate all parameters and the value threshold for the given problem type.

        Parameters
        ----------
        param_alpha : float
            search/global optimisation parameter
            alpha = 0 is a special case where we do not jump to the optimal at all, used for 'item-by-item' search
        param_beta : float
            density preference/local optimisation parameter
        param_gamma : float
            complexity aversion/weight preference parameter
        param_delta : float
            item-level rationality parameter
        problem_type: ProblemType
            if the problem is optimisation or decision
        value_threshold: int | None
            the value target for the decision problem

        Raises
        ------
        TypeError
            `problem_type` is not `ProblemType`
            `param_alpha`, `param_beta`, `param_gamma`, or `param_delta` are not float
            `value_threshold` is not int for decision task and None for optimisation task 
        ValueError
            `problem_type` is not recognised
            `param_alpha`, `param_beta`, `param_gamma`, or `param_delta` are not in valid range
            `value_threshold` is negative for decision task
        
        Returns
        -------
        None
        """       
        
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

    def get_node_distribution(self, param_alpha: float, param_beta: float, param_gamma: float, param_delta: float, problem_type: ProblemType = ProblemType.OPTIMISATION, value_threshold: int | None = None) -> dict[int, float]:
        """
        Get the distribution (as a percentage of 1) that someone will end in each terminal node from this given Knapsack Instance.
        This is based on the supplied alpha, beta, gamma, and delta parameters.
        Node distribution only considers feasible (at or under capacity) terminal (no more items will fit in the knapsack) nodes.

        Parameters
        ----------
        param_alpha : float
            search/global optimisation parameter
            alpha = 0 is a special case where we do not jump to the optimal at all, used for 'item-by-item' search
        param_beta : float
            density preference/local optimisation parameter
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
        TypeError
            `param_alpha`, `param_beta`, `param_gamma`, or `param_delta` are not float
            `problem_type` is not `ProblemType`
            `value_threshold` is not int for decision task and None for optimisation task 
        ValueError
            `problem_type` is not recognised
            `param_alpha`, `param_beta`, `param_gamma`, or `param_delta` are not in valid range
            `value_threshold` is negative for decision task
        
        Returns
        -------
        node_distribution : dict[int, float]
            A dict of the feasible terminal nodes with the percentage that one will end in each terminal node based on `beta`
        """

        def _search_for_optimum(node_distribution: dict[int, float], param_delta: float, param_alpha: float) -> dict[int, float]:
            """ Return the distribution of optimal terminal nodes reached in the search.
             
            The search for the optimum is hard, it requires 'remembering' all possible terminal nodes.
            When there are multiple optimal terminal nodes, an individual is indifferent between the nodes, so they are selected
            with equal probability.
            """

            percent_find_optimal_full_set = ((1 - param_delta) * math.exp((1 - len(self._terminal_nodes)) * ((1 - param_alpha) / param_alpha)))
            percent_find_optimal_non_dominated = (param_delta * math.exp((1 - len(self._non_dominated_terminal_nodes)) * ((1 - param_alpha) / param_alpha)))

            for optimal_terminal_node in self._optimal_terminal_nodes:
                node_distribution[optimal_terminal_node] = percent_find_optimal_full_set / len(self._optimal_terminal_nodes)
            
            for optimal_non_dominated_terminal_node in self._non_dominated_optimal_terminal_nodes:
                node_distribution[optimal_non_dominated_terminal_node] += percent_find_optimal_non_dominated / len(self._non_dominated_optimal_terminal_nodes)

            return node_distribution
            
        
        def _search_for_witness(node_distribution: dict[int, float], value_threshold: int, param_delta: float, param_alpha: float) -> dict[int, float]:
            """ Return the distribution of witness nodes reached in the search. 
            
            The search for a witness is easier than an optima, as any witness found along the way is sufficient. You do not need
            to remember and compare all possible terminal nodes..
            The search is split between fully removing dominated terminal nodes (from the perspective of this node) and including
            all dominated terminal nodes, in a ratio based on the individuals delta.
            When there are multiple witness terminal nodes, the probability of finding each one is given by the likelihood
            of running into the given terminal node in the search by adding 'random' items.
            """
            
            distribution_search_delta_0 = self.get_node_distribution(0.0, 0.0, 0.0, 0.0, ProblemType.DECISION, value_threshold)
            distribution_search_delta_1 = self.get_node_distribution(0.0, 0.0, 0.0, 1.0, ProblemType.DECISION, value_threshold)
            percent_witness_found_delta_0 = sum([distribution_percentage for knapsack_instance_hash, distribution_percentage in distribution_search_delta_0.items() if KnapsackInstance.instance_by_hash[knapsack_instance_hash]._standing_value >= value_threshold])
            percent_witness_found_delta_1 = sum([distribution_percentage for knapsack_instance_hash, distribution_percentage in distribution_search_delta_1.items() if KnapsackInstance.instance_by_hash[knapsack_instance_hash]._standing_value >= value_threshold])
            
            # If to use true 'deltas', rather than a delta weighted average between delta-0 and delta-1
            # distribution_search_delta_delta = self.get_node_distribution(0.0, 0.0, 0.0, param_delta, ProblemType.DECISION, value_threshold)
            # percent_witness_found = sum([distribution_percentage for knapsack_instance_hash, distribution_percentage in distribution_search_delta_delta.items() if KnapsackInstance.instance_by_hash[knapsack_instance_hash]._standing_value >= value_threshold])
            # percent_witness_found_delta_0 = percent_witness_found
            # percent_witness_found_delta_1 = percent_witness_found

            percent_find_optimal_full_set = ((1 - param_delta) * (percent_witness_found_delta_0 ** ((1 - param_alpha) / param_alpha)))
            percent_find_optimal_non_dominated = (param_delta * (percent_witness_found_delta_1 ** ((1 - param_alpha) / param_alpha)))            

            for knapsack_instance_hash, distribution_percentage in distribution_search_delta_0.items():
                if KnapsackInstance.instance_by_hash[knapsack_instance_hash]._standing_value >= value_threshold:
                    node_distribution[knapsack_instance_hash] = percent_find_optimal_full_set * (distribution_percentage / percent_witness_found_delta_0)
            
            for knapsack_instance_hash, distribution_percentage in distribution_search_delta_1.items():
                if KnapsackInstance.instance_by_hash[knapsack_instance_hash]._standing_value >= value_threshold:
                    node_distribution[knapsack_instance_hash] += percent_find_optimal_non_dominated * (distribution_percentage / percent_witness_found_delta_1)

            return node_distribution
        
        def _add_item_and_continue_search(node_distribution: dict[int, float], param_alpha: float, param_beta: float, param_gamma: float, param_delta: float, problem_type: ProblemType, value_threshold: int | None) -> dict[int, float]:
            """ Return the node_distribution of subnodes based on adding an item to the knapsack and continuing the search.
              
            The item added is probabilistic, based on the individuals alpha, beta, gamma, and delta. 
            """

            if self._child_nodes:
            
                percent_remove_dominance = param_delta
                percent_not_remove_dominance = 1.0 - param_delta

                transformed_divisor_all = sum((knapsack_item.density ** (param_beta / (1.0 - param_beta))) * (knapsack_item.weight ** (param_gamma / (1.0 - param_gamma))) for knapsack_item, _ in self._child_nodes)
                transformed_divisor_non_dominated = sum((knapsack_item.density ** (param_beta / (1.0 - param_beta))) * (knapsack_item.weight ** (param_gamma / (1.0 - param_gamma))) if hash(knapsack_item) in self._non_dominated_items else 0.0 for knapsack_item, _ in self._child_nodes)

                for knapsack_item, child_node in self._child_nodes:
                    child_distribution = child_node.get_node_distribution(param_alpha, param_beta, param_gamma, param_delta, problem_type, value_threshold)
                    for knapsack_instance_hash, distribution in child_distribution.items():
                        if knapsack_instance_hash not in node_distribution:
                            node_distribution[knapsack_instance_hash] = 0.0
                        node_distribution[knapsack_instance_hash] += percent_not_find_optimal * percent_not_remove_dominance * ((knapsack_item.density ** (param_beta / (1.0 - param_beta))) * (knapsack_item.weight ** (param_gamma / (1.0 - param_gamma)))) / transformed_divisor_all * distribution

                        # Add the additional weights for non-dominate items
                        if hash(knapsack_item) in self._non_dominated_items:
                            node_distribution[knapsack_instance_hash] += percent_not_find_optimal * percent_remove_dominance * ((knapsack_item.density ** (param_beta / (1.0 - param_beta))) * (knapsack_item.weight ** (param_gamma / (1.0 - param_gamma)))) / transformed_divisor_non_dominated * distribution

            return node_distribution

        # If the distribution for the node with the given parameters already exists, return the node to prevent recalculation
        hash_string = str(param_beta)  + "," + str(param_alpha) + "," + str(param_gamma) + "," + str(param_delta) + "," + str(problem_type) + "," + str(hash(self))
        full_hash = hashlib.sha256(hash_string.encode("utf-8")).digest()
        node_distribution_hash = int.from_bytes(full_hash[:7], 'big')
        if node_distribution_hash in self.distribution_by_hash:
            return self.distribution_by_hash[node_distribution_hash]

        # Otherwise, validate the parameters and calculate the node distribution
        self._validate_parameters_and_value_threshold(param_alpha, param_beta, param_gamma, param_delta, problem_type, value_threshold)
        node_distribution: dict[int, float] = {}

        # If this is a terminal node, there are no child nodes, so the distribution stops here.
        if self._is_terminal_node:
            node_distribution[hash(self)] = 1.0
            return node_distribution
        
        # Brute force search for optimum / witness
        
        # Depending on what problem type we need to search all terminal nodes and find the best (optimisation), or just find a terminal which meets a threshold (decision)
        if problem_type is ProblemType.OPTIMISATION:
            node_distribution = _search_for_optimum(node_distribution, param_delta, param_alpha)
    
        elif problem_type is ProblemType.DECISION:
            # If alpha is 0.0, we never find a witness.
            # To prevent infinite recursions, we skip the search entirely.
            if param_alpha != 0.0:
                node_distribution = _search_for_witness(node_distribution, value_threshold, param_delta, param_alpha)

        else:
            raise ValueError(f"Unexpected problem type: {problem_type}")
        
        percent_not_find_optimal = 1.0 - sum(node_distribution.values())

        # Brute search failed - Add an item to simplify the task
        if percent_not_find_optimal:
            node_distribution = _add_item_and_continue_search(node_distribution, param_alpha, param_beta, param_gamma, param_delta, problem_type, value_threshold)

        # Check the sum distribution equals 1
        if not math.isclose(sum(node_distribution.values()), 1.0):
            raise RuntimeError('node distribution must equal 1')

        # Store the node distribution so that if this node is reached by another path, the distribution can be fetched without additional calculations 
        self.distribution_by_hash[node_distribution_hash] = node_distribution

        return self.distribution_by_hash[node_distribution_hash]

    def print_node_distribution(self, distribution: dict[int, float], parameters: tuple[float, float, float, float] | None = None, print_threshold: float = 0.0001) -> None:
        """ Print the knapsack node distribution with all relevant information.

        Prints the distribution (as a percentage of 1) that someone will end in each terminal node from this given Knapsack Instance.
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

        Raises
        ------
        RuntimeError
            Difference in inclusion strings
            No `master_knapsack`


        Returns: None
        """

        def validate_distribution(distribution: dict[int, float]) -> None:
            """ Validate the supplied distribution. """
            
            if not isinstance(distribution, dict):
                raise TypeError
            
            if not all(isinstance(key, int) for key in distribution.keys()):
                raise TypeError
            
            if not all(isinstance(value, float) for value in distribution.values()):
                raise TypeError
            
            if not math.isclose(sum(distribution.values()), 1.0):
                raise ValueError

        def validate_print_parameters(parameters: tuple[float, float, float, float] | None, print_threshold: float ) -> None:
            """ Validate the supplied print parameters. """
            
            if parameters is not None:
                if not isinstance(parameters, tuple):
                    raise TypeError

                if not len(parameters) == 4:
                    raise ValueError

                if not all(isinstance(parameter, float) for parameter in parameters):
                    raise TypeError

                if not all(0.0 <= parameter <= 1 for parameter in parameters):
                    raise ValueError

            if not isinstance(print_threshold, float):
                raise TypeError

            if not 0.0 < print_threshold <= 1.0:
                raise ValueError

        
        def get_item_inclusion_string(terminal_node_knapsack_items_repr_hash: list[int], master_knapsack_items_repr_hashes: list[int]) -> str:
            """ Return a string of the items included (1s and 0s) base on the order they are specified in `master_knapsack_items_repr_hashes`. 
            
            This more involved method is required due to repeated items. This gives strict priority to earlier instances of the repeated identical item.
            This means that two terminal nodes featuring a repeated item will give the same terminal distribution, regardless of which of the items was
            included. The reason for this is to a human, the two knapsacks are identical, hence, should not be considered split.
            One could also split choices evenly across the repeated items, but this adds more noise to the data unnecessarily."""

            item_inclusions = [True] * len(master_knapsack_items_repr_hashes)

            for terminal_node_item_hash in terminal_node_knapsack_items_repr_hash:
                index_offset = 0
                while True:
                    knapsack_item_match_index = master_knapsack_items_repr_hashes.index(terminal_node_item_hash, index_offset)
                    if item_inclusions[knapsack_item_match_index] == True:
                        item_inclusions[knapsack_item_match_index] = False
                        break
                    else:
                        index_offset = knapsack_item_match_index

            item_inclusion_string = str([1 if item_included else 0 for item_included in item_inclusions])

            return item_inclusion_string
        
        validate_distribution(distribution)
        validate_print_parameters(parameters, print_threshold)
        
        distribution = dict(sorted(distribution.items(), key=lambda x: x[1], reverse=True))

        print("Inputs\n")
        if parameters: print(f"Parameters: \u03b1 = {parameters[0]}, \u03B2 = {parameters[1]}, \u03b3 = {parameters[2]}, \u03B4 = {parameters[3]}\n")  # alpha (\u03b1), beta (\u03B2), gamma (\u03b3), delta (\u03B4)
        print("Knapsack Problem Variant: Optimisation\n")
        print("Items: " + ", ".join([str(knapsack_item) for knapsack_item in self.knapsack_items]) + "\n")
        print(f"Budget: {self._knapsack_capacity}\n")

        print("-------------------------------------\n")

        print("Output\n")
        print("Terminal Nodes (*** for optimal):")

        for knapsack_instance_hash, distribution_percentage in distribution.items():
            if distribution_percentage > print_threshold:
                knapsack_instance = KnapsackInstance.instance_by_hash[knapsack_instance_hash]
                item_inclusion_string = get_item_inclusion_string(knapsack_instance.knapsack_items_repr_hashes, self.knapsack_items_repr_hashes)
                
                if knapsack_instance._master_knapsack is None:  # This is mainly for type hint errors
                    raise RuntimeError("Cannot print for knapsack without master knapsack.")  # Note: This will crash if master knapsack has no items which will fit.
                
                print(f"{item_inclusion_string} - Σv: {knapsack_instance._standing_value}, Σw: {knapsack_instance._master_knapsack._knapsack_capacity - knapsack_instance._knapsack_capacity} / {knapsack_instance._master_knapsack._knapsack_capacity} - {100.0 * distribution_percentage:.3f}%{" ***" if hash(knapsack_instance) in knapsack_instance._master_knapsack._optimal_terminal_nodes else ""}")
    
        print(f"\nTotal Distribution: {sum(distribution.values())}\n")
        print(f"Number of Terminal Nodes: {len(distribution)}\n")

    def solve_decision_variant(self, param_alpha: float, param_beta: float, param_gamma: float, param_delta: float, value_threshold: int) -> float:
        """
        Return the expectation (as a percent) of the the time a witness will be found in the knapsack decision problem instance for the given parameters and value threshold (target).
        
        Parameters
        ----------
        param_alpha : float
            search/global optimisation parameter
            alpha = 0 is a special case where we do not jump to the optimal at all, used for 'item-by-item' search
        param_beta : float
            density preference/local optimisation parameter
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
        TypeError
            `param_alpha`, `param_beta`, `param_gamma`, or `param_delta` are not float
            `value_threshold` is not int
        ValueError
            `param_alpha`, `param_beta`, `param_gamma`, or `param_delta` are not in valid range
            `value_threshold` is negative
        
        Returns
        -------
        percent_witness_found : float
            the expected percentage of the time that a witness is successfully found
        """

        self._validate_parameters_and_value_threshold(param_alpha, param_beta, param_gamma, param_delta, ProblemType.DECISION, value_threshold)
    
        node_distribution = self.get_node_distribution(param_alpha, param_beta, param_gamma, param_delta, ProblemType.DECISION, value_threshold)
        percent_witness_found = sum([distribution_percentage for knapsack_instance_hash, distribution_percentage in node_distribution.items() if KnapsackInstance.instance_by_hash[knapsack_instance_hash]._standing_value >= value_threshold])
        
        return percent_witness_found
