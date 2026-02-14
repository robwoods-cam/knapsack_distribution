"""
Tools for calculating probabilistic choice distributions in knapsack problem instances.

This module provides the the key functions `get_node_distribution`, `print_node_distribution`,
`solve_decision_variant`, and supporting functionality.  
See README.md for full documentation and examples.


Copyright
---------
© 2025 Robert Woods - Code and implementation
© 2025 Roman Berlanger - Model and concept


License
-------
This program is free software under the GNU Affero General Public License v3.  
See the LICENSE file for full terms.
"""


import hashlib
import math

from .knapsack_item import KnapsackItem
from .knapsack_instance import KnapsackInstance
from .problem_type import ProblemType


def _get_knapsack_item_dominance_matrix(knapsack_items: list[KnapsackItem] | tuple[KnapsackItem, ...]) -> dict[int, set[int]]:
    """ Sets the `KnapsackItem`s that dominate this `KnapsackItem`. TODO 
    
    #     Sets `_dominating_knapsack_item_hashes` to a `set` of `hash`es for all `knapsack_item`s in `knapsack_items` that dominate it.
    #     A knapsack item dominates another if both the value is greater than the other value and the weight is less than the other weight and at least one is strictly.

    Checks to see if any `KnapsackItem` in `knapsack_items` dominates this `KnapsackItem`.
        
    #     A knapsack item dominates another if both the value is greater than the other value and the weight is less than the other weight and at least one is strictly.

    #     Parameters
    #     ----------
    #     knapsack_items : list[KnapsackItem]
    #         A list of `KnapsacksItems` to be checked for dominance

    #     Raises
    #     ------
    #     TypeError
    #         if a list of `KnapsackItem`s is not supplied
    #     ValueError
    #         if the list of dominating `KnapsackItem`s includes this `KnapsackItem` (self dominance) TODO

    #     Returns
    #     -------
#         knapsack_item_dominance_matrix : dict[int, set[int]]
            TODO
    
    """

    knapsack_item_dominance_matrix: dict[int, set[int]] = {}

    if not (isinstance(knapsack_items, list | tuple) and all(isinstance(knapsack_item, KnapsackItem) for knapsack_item in knapsack_items)):
        raise TypeError("knapsack_items must be a list of `KnapsackItem`")
    
    if len(knapsack_items) != len(set([hash(knapsack_item) for knapsack_item in knapsack_items])):
        raise ValueError("Repeated `KnapsackItem` cannot be set in dominance matrix.")
    
    for knapsack_item_1 in knapsack_items:
        knapsack_item_dominance_matrix[hash(knapsack_item_1)] = set()

        for knapsack_item_2 in knapsack_items:
            if hash(knapsack_item_1) != hash(knapsack_item_2):
                if (knapsack_item_2.value > knapsack_item_1.value and knapsack_item_2.weight <= knapsack_item_1.weight) or (knapsack_item_2.value >= knapsack_item_1.value and knapsack_item_2.weight < knapsack_item_1.weight) or (knapsack_item_2 == knapsack_item_1 and knapsack_item_2.knapsack_item_id < knapsack_item_1.knapsack_item_id):
                    knapsack_item_dominance_matrix[hash(knapsack_item_1)].add(hash(knapsack_item_2))

    return knapsack_item_dominance_matrix


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
    
        if not isinstance(value_threshold, int) or isinstance(value_threshold, bool):
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


def get_node_distribution(knapsack_instance: KnapsackInstance, param_alpha: float, param_beta: float, param_gamma: float, param_delta: float, problem_type: ProblemType = ProblemType.OPTIMISATION, value_threshold: int | None = None) -> dict[int, float]:
    """ Get the distribution that someone will end in each terminal node from this given Knapsack Instance.
    Get the distribution (as a percentage of 1) that someone will end in each terminal node from this given Knapsack Instance.
    This is based on the supplied alpha, beta, gamma, and delta parameters.
    Node distribution only considers feasible (at or under capacity) terminal (no more items will fit in the knapsack) nodes.

    
    #     Non-dominated terminal nodes is from the perspective that no items are added from this node onwards which are dominated.
    #     Dominated items may already have been added, as long as no further items are added.
    #     Mathematically, in these nodes, there are no-dominated items included unless the item was already included at this node.
    
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

    distribution_by_hash: dict[int, dict[int, float]] = {}
    included_dominated_items_by_hash: dict[int, list[KnapsackItem]] = {} 
    knapsack_item_dominance_matrix: dict[int, set[int]] = _get_knapsack_item_dominance_matrix(knapsack_instance.knapsack_items)

    for terminal_node in knapsack_instance.terminal_nodes:
        included_dominated_items: list[KnapsackItem] = [standing_knapsack_item for standing_knapsack_item in KnapsackInstance.instance_by_hash[terminal_node].standing_knapsack_items if any(hash(knapsack_item_x) in knapsack_item_dominance_matrix[hash(standing_knapsack_item)] for knapsack_item_x in KnapsackInstance.instance_by_hash[terminal_node].knapsack_items)]
        included_dominated_items_by_hash[terminal_node] = included_dominated_items

    def _get_child_node_distribution(knapsack_instance: KnapsackInstance, param_alpha: float, param_beta: float, param_gamma: float, param_delta: float, problem_type: ProblemType = ProblemType.OPTIMISATION, value_threshold: int | None = None) -> dict[int, float]:
        def _search_for_optimum(node_distribution: dict[int, float], param_delta: float, param_alpha: float) -> dict[int, float]:
            """ Return the distribution of optimal terminal nodes reached in the search.

            The search for the optimum is hard, it requires 'remembering' all possible terminal nodes.
            When there are multiple optimal terminal nodes, an individual is indifferent between the nodes, so they are selected
            with equal probability.
            """

            percent_find_optimal_full_set = ((1 - param_delta) * math.exp((1 - len(knapsack_instance.terminal_nodes)) * ((1 - param_alpha) / param_alpha)))
            percent_find_optimal_non_dominated = (param_delta * math.exp((1 - len(non_dominated_terminal_nodes)) * ((1 - param_alpha) / param_alpha)))

            for optimal_terminal_node in knapsack_instance.optimal_terminal_nodes:
                node_distribution[optimal_terminal_node] = percent_find_optimal_full_set / len(knapsack_instance.optimal_terminal_nodes)

            for optimal_non_dominated_terminal_node in non_dominated_optimal_terminal_nodes:
                node_distribution[optimal_non_dominated_terminal_node] += percent_find_optimal_non_dominated / len(non_dominated_optimal_terminal_nodes)

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

            distribution_search_delta_0 = _get_child_node_distribution(knapsack_instance, 0.0, 0.0, 0.0, 0.0, ProblemType.DECISION, value_threshold)
            distribution_search_delta_1 = _get_child_node_distribution(knapsack_instance, 0.0, 0.0, 0.0, 1.0, ProblemType.DECISION, value_threshold)
            percent_witness_found_delta_0 = sum([distribution_percentage for knapsack_instance_hash, distribution_percentage in distribution_search_delta_0.items() if KnapsackInstance.instance_by_hash[knapsack_instance_hash].standing_value >= value_threshold])
            percent_witness_found_delta_1 = sum([distribution_percentage for knapsack_instance_hash, distribution_percentage in distribution_search_delta_1.items() if KnapsackInstance.instance_by_hash[knapsack_instance_hash].standing_value >= value_threshold])

            # If to use true 'deltas', rather than a delta weighted average between delta-0 and delta-1
            # distribution_search_delta_delta = self._get_child_node_distribution(0.0, 0.0, 0.0, param_delta, ProblemType.DECISION, value_threshold)
            # percent_witness_found = sum([distribution_percentage for knapsack_instance_hash, distribution_percentage in distribution_search_delta_delta.items() if KnapsackInstance.instance_by_hash[knapsack_instance_hash]._standing_value >= value_threshold])
            # percent_witness_found_delta_0 = percent_witness_found
            # percent_witness_found_delta_1 = percent_witness_found

            percent_find_optimal_full_set = ((1 - param_delta) * (percent_witness_found_delta_0 ** ((1 - param_alpha) / param_alpha)))
            percent_find_optimal_non_dominated = (param_delta * (percent_witness_found_delta_1 ** ((1 - param_alpha) / param_alpha)))            

            for knapsack_instance_hash, distribution_percentage in distribution_search_delta_0.items():
                if KnapsackInstance.instance_by_hash[knapsack_instance_hash].standing_value >= value_threshold:
                    node_distribution[knapsack_instance_hash] = percent_find_optimal_full_set * (distribution_percentage / percent_witness_found_delta_0)

            for knapsack_instance_hash, distribution_percentage in distribution_search_delta_1.items():
                if KnapsackInstance.instance_by_hash[knapsack_instance_hash].standing_value >= value_threshold:
                    node_distribution[knapsack_instance_hash] += percent_find_optimal_non_dominated * (distribution_percentage / percent_witness_found_delta_1)

            return node_distribution

        def _add_item_and_continue_search(node_distribution: dict[int, float], param_alpha: float, param_beta: float, param_gamma: float, param_delta: float, problem_type: ProblemType, value_threshold: int | None) -> dict[int, float]:
            """ Return the node_distribution of subnodes based on adding an item to the knapsack and continuing the search.

            The item added is probabilistic, based on the individuals alpha, beta, gamma, and delta. 
            """

            if knapsack_instance.child_nodes:

                percent_remove_dominance = param_delta
                percent_not_remove_dominance = 1.0 - param_delta

                transformed_divisor_all = sum((knapsack_item.density ** (param_beta / (1.0 - param_beta))) * (knapsack_item.weight ** (param_gamma / (1.0 - param_gamma))) for knapsack_item, _ in knapsack_instance.child_nodes)
                transformed_divisor_non_dominated = sum((knapsack_item.density ** (param_beta / (1.0 - param_beta))) * (knapsack_item.weight ** (param_gamma / (1.0 - param_gamma))) if hash(knapsack_item) in non_dominated_items else 0.0 for knapsack_item, _ in knapsack_instance.child_nodes)

                for knapsack_item, child_node in knapsack_instance.child_nodes:
                    child_distribution = _get_child_node_distribution(child_node, param_alpha, param_beta, param_gamma, param_delta, problem_type, value_threshold)
                    for knapsack_instance_hash, distribution in child_distribution.items():
                        if knapsack_instance_hash not in node_distribution:
                            node_distribution[knapsack_instance_hash] = 0.0
                        node_distribution[knapsack_instance_hash] += percent_not_find_optimal * percent_not_remove_dominance * ((knapsack_item.density ** (param_beta / (1.0 - param_beta))) * (knapsack_item.weight ** (param_gamma / (1.0 - param_gamma)))) / transformed_divisor_all * distribution

                        # Add the additional weights for non-dominate items
                        if hash(knapsack_item) in non_dominated_items:
                            node_distribution[knapsack_instance_hash] += percent_not_find_optimal * percent_remove_dominance * ((knapsack_item.density ** (param_beta / (1.0 - param_beta))) * (knapsack_item.weight ** (param_gamma / (1.0 - param_gamma)))) / transformed_divisor_non_dominated * distribution

            return node_distribution

        # If the distribution for the node with the given parameters already exists, return the node to prevent recalculation
        hash_string = str(param_beta)  + "," + str(param_alpha) + "," + str(param_gamma) + "," + str(param_delta) + "," + str(problem_type) + "," + str(hash(knapsack_instance))
        full_hash = hashlib.sha256(hash_string.encode("utf-8")).digest()
        node_distribution_hash = int.from_bytes(full_hash[:7], 'big')
        
        if node_distribution_hash in distribution_by_hash:
            return distribution_by_hash[node_distribution_hash]
        
        # Otherwise, validate the parameters and calculate the node distribution
        _validate_parameters_and_value_threshold(param_alpha, param_beta, param_gamma, param_delta, problem_type, value_threshold)
        node_distribution: dict[int, float] = {}


        # TODO calc:
        # NOTE FIXME this may all need to happen before any distribution search happens, Im not sure.
        # Maybe can just take the master node knapsack and do for all its terminal nodes, because I think it only matters for them

        # _non_dominated_items
        non_dominated_items: set[int] = set()
        for i, knapsack_item in enumerate(knapsack_instance.knapsack_items):        
            if not any(hash(knapsack_item_x) in knapsack_item_dominance_matrix[hash(knapsack_item)] for knapsack_item_x in knapsack_instance.knapsack_items[:i] + knapsack_instance.knapsack_items[i + 1:]):
                non_dominated_items.add(hash(knapsack_item))
        
        # TODO fix (if can) issue is this need to be done 
        # TODO this probably doesnt need to be redone
        included_dominated_items: list[KnapsackItem] = [standing_knapsack_item for standing_knapsack_item in knapsack_instance.standing_knapsack_items if any(hash(knapsack_item_x) in knapsack_item_dominance_matrix[hash(standing_knapsack_item)] for knapsack_item_x in knapsack_instance.knapsack_items)]
        included_dominated_items_by_hash[hash(knapsack_instance)] = included_dominated_items
        
        # _non_dominated_terminal_nodes
        #     return [terminal_node for terminal_node in self._terminal_nodes if not KnapsackInstance.instance_by_hash[terminal_node]._is_dominated or all(terminal_included_dominated_item in self._included_dominated_items for terminal_included_dominated_item in KnapsackInstance.instance_by_hash[terminal_node]._included_dominated_items)] 
        
        non_dominated_terminal_nodes = [terminal_node for terminal_node in knapsack_instance.terminal_nodes if not len(included_dominated_items_by_hash[terminal_node]) >= 1 or all(terminal_included_dominated_item in included_dominated_items for terminal_included_dominated_item in included_dominated_items_by_hash[terminal_node])] 
        
        # _non_dominated_optimal_terminal_nodes
        #   return [terminal_node for terminal_node in self._optimal_terminal_nodes if not KnapsackInstance.instance_by_hash[terminal_node]._is_dominated or all(terminal_included_dominated_item in self._included_dominated_items for terminal_included_dominated_item in KnapsackInstance.instance_by_hash[terminal_node]._included_dominated_items)]

        non_dominated_optimal_terminal_nodes = [terminal_node for terminal_node in knapsack_instance.optimal_terminal_nodes if not len(included_dominated_items_by_hash[terminal_node]) >= 1 or all(terminal_included_dominated_item in included_dominated_items for terminal_included_dominated_item in included_dominated_items_by_hash[terminal_node])]

        # If this is a terminal node, there are no child nodes, so the distribution stops here.
        if knapsack_instance.is_terminal_node:
            node_distribution[hash(knapsack_instance)] = 1.0
            return node_distribution

        # Brute force search for optimum / witness

        # Depending on what problem type we need to search all terminal nodes and find the best (optimisation), or just find a terminal which meets a threshold (decision)
        if problem_type is ProblemType.OPTIMISATION:
            node_distribution = _search_for_optimum(node_distribution, param_delta, param_alpha)

        elif problem_type is ProblemType.DECISION:
            if value_threshold is None:
                raise Exception("TODO: Decision Problem must have a value threshold!")
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
        distribution_by_hash[node_distribution_hash] = node_distribution

        return distribution_by_hash[node_distribution_hash]  # is node_distribution

    return _get_child_node_distribution(knapsack_instance, param_alpha, param_beta, param_gamma, param_delta, problem_type, value_threshold)


def print_node_distribution(knapsack_instance_x: KnapsackInstance, distribution: dict[int, float], parameters: tuple[float, float, float, float] | None = None, print_threshold: float = 0.0001) -> None:
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
            
            if not all((isinstance(key, int) and not isinstance(key, bool)) for key in distribution.keys()):
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
        print("Items: " + ", ".join([str(knapsack_item) for knapsack_item in knapsack_instance_x.knapsack_items]) + "\n")
        print(f"Budget: {knapsack_instance_x.knapsack_capacity}\n")

        print("-------------------------------------\n")

        print("Output\n")
        print("Terminal Nodes (*** for optimal):")

        for knapsack_instance_hash, distribution_percentage in distribution.items():
            if distribution_percentage > print_threshold:
                knapsack_instance_x_2 = KnapsackInstance.instance_by_hash[knapsack_instance_hash]
                item_inclusion_string = get_item_inclusion_string(knapsack_instance_x_2.knapsack_items_repr_hashes, knapsack_instance_x.knapsack_items_repr_hashes)
                
                if knapsack_instance_x_2.master_knapsack is None:  # This is mainly for type hint errors
                    raise RuntimeError("Cannot print for knapsack without master knapsack.")  # Note: This will crash if master knapsack has no items which will fit.
                
                print(f"{item_inclusion_string} - Σv: {knapsack_instance_x_2.standing_value}, Σw: {knapsack_instance_x_2.master_knapsack.knapsack_capacity - knapsack_instance_x_2.knapsack_capacity} / {knapsack_instance_x_2.master_knapsack.knapsack_capacity} - {100.0 * distribution_percentage:.3f}%{" ***" if hash(knapsack_instance_x_2) in knapsack_instance_x_2.master_knapsack.optimal_terminal_nodes else ""}")
    
        print(f"\nTotal Distribution: {sum(distribution.values())}\n")
        print(f"Number of Terminal Nodes: {len(distribution)}\n")


def solve_decision_variant(knapsack_instance_x: KnapsackInstance, param_alpha: float, param_beta: float, param_gamma: float, param_delta: float, value_threshold: int) -> float:
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

        _validate_parameters_and_value_threshold(param_alpha, param_beta, param_gamma, param_delta, ProblemType.DECISION, value_threshold)
    
        node_distribution = get_node_distribution(knapsack_instance_x, param_alpha, param_beta, param_gamma, param_delta, ProblemType.DECISION, value_threshold)
        percent_witness_found = sum([distribution_percentage for knapsack_instance_hash, distribution_percentage in node_distribution.items() if KnapsackInstance.instance_by_hash[knapsack_instance_hash].standing_value >= value_threshold])
        
        return percent_witness_found
