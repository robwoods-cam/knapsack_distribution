"""
Tools for calculating probabilistic choice distributions in knapsack problem instances.

This module provides the the key functions `get_node_distribution`, `print_node_distribution`,
`solve_decision_variant`, and supporting functionality.
See README.md for full documentation and examples.


Copyright
---------
© 2026 Robert Woods - Code and implementation
© 2026 Roman Berlanger - Model and concept


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
    """ Build a dominance matrix over `knapsack_items`.

    An item *dominates* another when it is at least as valuable and no heavier, with at least one of
    those comparisons strict. Two items with identical `value` and `weight` are broken apart by
    `knapsack_item_id` (the lower-id item dominates), so a duplicated item is treated as a single
    choice rather than two competing ones.


    Parameters
    ----------
    knapsack_items : list[KnapsackItem] | tuple[KnapsackItem, ...]
        The items to compare. Every item must be distinct by `hash`.


    Raises
    ------
    TypeError
        if `knapsack_items` is not a `list`/`tuple` of `KnapsackItem`s.
    ValueError
        if `knapsack_items` contains the same item more than once (by `hash`).


    Returns
    -------
    knapsack_item_dominance_matrix : dict[int, set[int]]
        Maps each item's `hash` to the set of hashes of the items that dominate it.
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
    """ Validate the four behavioural parameters and `value_threshold` for the given problem type.

    Parameters
    ----------
    param_alpha : float
        Search / global-optimisation parameter. Must be in (0, 1] for an optimisation problem and in
        [0, 1] for a decision problem, where `param_alpha` = 0 is the special case of never searching
        for the global solution (pure 'item-by-item' search).
    param_beta : float
        Density-preference (local-optimisation) parameter, in [0, 1).
    param_gamma : float
        Complexity-aversion (weight-preference) parameter, in [0, 1).
    param_delta : float
        Item-level rationality (dominance-avoidance) parameter, in [0, 1].
    problem_type : ProblemType
        Whether the problem is optimisation or decision.
    value_threshold : int | None
        The target value for a decision problem; must be `None` for an optimisation problem.

    Raises
    ------
    TypeError
        if `problem_type` is not a `ProblemType`; if any of `param_alpha`, `param_beta`,
        `param_gamma`, `param_delta` is not a `float`; or if `value_threshold` is not an `int` for a
        decision problem / not `None` for an optimisation problem.
    ValueError
        if `problem_type` is unrecognised, any parameter falls outside its valid range, or
        `value_threshold` is negative for a decision problem.

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


def get_node_distribution(knapsack_instance: KnapsackInstance, param_alpha: float, param_beta: float, param_gamma: float, param_delta: float, problem_type: ProblemType = ProblemType.OPTIMISATION, value_threshold: int | None = None, verbose: bool = False) -> dict[int, float]:
    """ Compute the probability distribution over the terminal nodes reachable from `knapsack_instance`.

    Returns, for each reachable terminal node, the probability (a fraction of 1) that a
    decision-maker with the given behavioural parameters ends in that node. Only feasible (at or
    under capacity) terminal (no more items will fit in the knapsack) nodes are considered, and the
    probabilities sum to 1.

    At each node the probability mass is split between a brute-force search for the global solution
    (an optimum, or a witness for the decision variant) and probabilistically adding one more item
    and continuing from the resulting child node.

    Parameters
    ----------
    knapsack_instance : KnapsackInstance
        The node to compute the distribution from (typically the root / master knapsack).
    param_alpha : float
        Search / global-optimisation parameter. `param_alpha` = 0 is the special case of never
        searching for the global solution, used for 'item-by-item' search.
    param_beta : float
        Density-preference (local-optimisation) parameter.
    param_gamma : float
        Complexity-aversion (weight-preference) parameter.
    param_delta : float
        Item-level rationality (dominance-avoidance) parameter.
    problem_type : ProblemType, default ProblemType.OPTIMISATION
        Whether to search for an optimum (optimisation) or a witness (decision).
    value_threshold : int | None, default None
        The target value for a decision problem; must be `None` for an optimisation problem.
    verbose : bool, default False
        Prints each branch to a child with the probability and cause (optimal jump or item add)

    Raises
    ------
    RuntimeError
        if the computed node distribution does not sum to (close to) 1.
    TypeError
        if any of `param_alpha`, `param_beta`, `param_gamma`, `param_delta` is not a `float`; if
        `problem_type` is not a `ProblemType`; or if `value_threshold` is not an `int` for a
        decision problem / not `None` for an optimisation problem.
    ValueError
        if `problem_type` is unrecognised, any parameter is out of range, or `value_threshold` is
        negative for a decision problem.

    Returns
    -------
    node_distribution : dict[int, float]
        Maps each reachable terminal node's `hash` to the probability of ending in that node.
    """

    if verbose:
        print("Log of child node creation (verbose = True)\n")

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

            The search for a witness is easier than for an optimum, as any witness found along the way is sufficient. You do not
            need to remember and compare all possible terminal nodes.
            The search is split between fully removing dominated terminal nodes (from the perspective of this node) and including
            all dominated terminal nodes, in a ratio based on the individual's delta.
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

            The item added is probabilistic, based on the individual's alpha, beta, gamma, and delta.
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

                        # Only for verbose processing and printing the transitions
                        if verbose:
                            child_knapsack = KnapsackInstance.instance_by_hash[knapsack_instance_hash]
                            if hash(knapsack_item) in non_dominated_items:
                                distribution = percent_not_find_optimal * percent_not_remove_dominance * ((knapsack_item.density ** (param_beta / (1.0 - param_beta))) * (knapsack_item.weight ** (param_gamma / (1.0 - param_gamma)))) / transformed_divisor_all * distribution + percent_not_find_optimal * percent_remove_dominance * ((knapsack_item.density ** (param_beta / (1.0 - param_beta))) * (knapsack_item.weight ** (param_gamma / (1.0 - param_gamma)))) / transformed_divisor_non_dominated * distribution
                            else:
                                distribution = percent_not_find_optimal * percent_not_remove_dominance * ((knapsack_item.density ** (param_beta / (1.0 - param_beta))) * (knapsack_item.weight ** (param_gamma / (1.0 - param_gamma)))) / transformed_divisor_all * distribution

                            print(f"add item: {get_unmerged_item_inclusion_string(knapsack_instance.knapsack_items, knapsack_instance.master_knapsack.knapsack_items if knapsack_instance.master_knapsack else knapsack_instance.knapsack_items)} -> {get_unmerged_item_inclusion_string(child_knapsack.knapsack_items, child_knapsack.master_knapsack.knapsack_items)} = {distribution:.3f}")

            return node_distribution

        # Only for verbose processing and printing the transitions
        def get_unmerged_item_inclusion_string(terminal_node_knapsack_items: tuple[KnapsackItem, ...], master_knapsack_items: tuple[KnapsackItem, ...]) -> str:

            item_inclusions = [True] * len(master_knapsack_items)

            for terminal_node_item in terminal_node_knapsack_items:
                for i in range(len(master_knapsack_items) - 1, -1, -1):
                    if master_knapsack_items[i] is terminal_node_item and item_inclusions[i]:
                        item_inclusions[i] = False
                        break

            item_inclusion_string = str([1 if item_included else 0 for item_included in item_inclusions])

            return item_inclusion_string

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
        included_dominated_items_hashes: list[int] = [hash(knapsack_item) for knapsack_item in included_dominated_items]
        included_dominated_items_by_hash[hash(knapsack_instance)] = included_dominated_items

        # _non_dominated_terminal_nodes
        #     return [terminal_node for terminal_node in self._terminal_nodes if not KnapsackInstance.instance_by_hash[terminal_node]._is_dominated or all(terminal_included_dominated_item in self._included_dominated_items for terminal_included_dominated_item in KnapsackInstance.instance_by_hash[terminal_node]._included_dominated_items)]

        non_dominated_terminal_nodes = [terminal_node for terminal_node in knapsack_instance.terminal_nodes if len(included_dominated_items_by_hash[terminal_node]) == 0 or all(hash(terminal_included_dominated_item) in included_dominated_items_hashes for terminal_included_dominated_item in included_dominated_items_by_hash[terminal_node])]

        # _non_dominated_optimal_terminal_nodes
        #   return [terminal_node for terminal_node in self._optimal_terminal_nodes if not KnapsackInstance.instance_by_hash[terminal_node]._is_dominated or all(terminal_included_dominated_item in self._included_dominated_items for terminal_included_dominated_item in KnapsackInstance.instance_by_hash[terminal_node]._included_dominated_items)]

        non_dominated_optimal_terminal_nodes = [terminal_node for terminal_node in knapsack_instance.optimal_terminal_nodes if len(included_dominated_items_by_hash[terminal_node]) == 0 or all(hash(terminal_included_dominated_item) in included_dominated_items_hashes for terminal_included_dominated_item in included_dominated_items_by_hash[terminal_node])]

        # If this is a terminal node, there are no child nodes, so the distribution stops here.
        if knapsack_instance.is_terminal_node:
            node_distribution[hash(knapsack_instance)] = 1.0
            # Only for verbose processing and printing the transitions
            if verbose:
                print(f"terminal node: {get_unmerged_item_inclusion_string(knapsack_instance.knapsack_items, knapsack_instance.master_knapsack.knapsack_items if knapsack_instance.master_knapsack else knapsack_instance.knapsack_items)} -> terminal = 1.0")
            return node_distribution

        # Brute force search for optimum / witness

        # Depending on what problem type we need to search all terminal nodes and find the best (optimisation), or just find a terminal which meets a threshold (decision)
        if problem_type is ProblemType.OPTIMISATION:
            node_distribution = _search_for_optimum(node_distribution, param_delta, param_alpha)

            # Only for verbose processing and printing the transitions
            if verbose:
                for knapsack_hash, distribution in node_distribution.items():
                    child_knapsack = KnapsackInstance.instance_by_hash[knapsack_hash]
                    print(f"optimal jump: {get_unmerged_item_inclusion_string(knapsack_instance.knapsack_items, knapsack_instance.master_knapsack.knapsack_items if knapsack_instance.master_knapsack else knapsack_instance.knapsack_items)} -> {get_unmerged_item_inclusion_string(child_knapsack.knapsack_items, child_knapsack.master_knapsack.knapsack_items)} = {distribution:.3f}")

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

    child_node_distribution = _get_child_node_distribution(knapsack_instance, param_alpha, param_beta, param_gamma, param_delta, problem_type, value_threshold)

    if verbose:
        print("\n-------------------------------------\n")

    return child_node_distribution


def print_node_distribution(master_knapsack_instance: KnapsackInstance, distribution: dict[int, float], parameters: tuple[float, float, float, float] | None = None, print_threshold: float = 0.0001, show_unmerged_distribution: bool = False) -> None:
        """ Print the terminal-node distribution for a knapsack instance in a readable form.

        Each terminal node is shown as a binary (1 and 0) list of item inclusions, based on the order
        the items were supplied to the master node knapsack, together with its total value, total
        weight against capacity, and probability (as a percentage of 1); optimal nodes are marked
        with `***`. Only feasible (at or under capacity) terminal (no more items will fit in the
        knapsack) nodes appear. By default, terminal nodes that differ only by which copy of a
        repeated identical item was included are merged.

        Also prints the ordered list of knapsack items and the count of terminal nodes reached.

        Parameters
        ----------
        master_knapsack_instance : KnapsackInstance
            The root knapsack the `distribution` was computed from; its item order defines the
            inclusion strings.
        distribution : dict[int, float]
            The probability distribution to print, mapping each terminal node's `hash` to its
            probability (as produced by `get_node_distribution`).
        parameters : tuple[float, float, float, float] | None, default None
            The `(alpha, beta, gamma, delta)` parameters used to calculate the distribution, printed
            in the header when given.
        print_threshold : float, default 0.0001
            Only terminal nodes with a probability greater than or equal to this are printed.
        show_unmerged_distribution : bool, default False
            If `True`, additionally print the unmerged distribution, distinguishing which copy of a
            repeated identical item was included.

        Raises
        ------
        TypeError
            if `distribution` or the print parameters have the wrong types.
        ValueError
            if `distribution` does not sum to 1, or a print parameter is out of range.


        Returns
        -------
        None
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

            if not 0.0 <= print_threshold <= 1.0:
                raise ValueError


        def get_item_inclusion_string(terminal_node_knapsack_items_repr_hash: list[int], master_knapsack_items_repr_hashes: list[int]) -> str:
            """ Return a string of the items included (1s and 0s) base on the order they are specified in `master_knapsack_items_repr_hashes`.

            This more involved method is required due to repeated items. This gives strict priority to earlier instances of the repeated identical item.
            This means that two terminal nodes featuring a repeated item will give the same terminal distribution, regardless of which of the items was
            included. The reason for this is to a human, the two knapsacks are identical, hence, should not be considered split.
            One could also split choices evenly across the repeated items, but this adds more noise to the data unnecessarily."""

            item_inclusions = [True] * len(master_knapsack_items_repr_hashes)

            for terminal_node_item_hash in terminal_node_knapsack_items_repr_hash:
                for i in range(len(master_knapsack_items_repr_hashes) - 1, -1, -1):
                    if master_knapsack_items_repr_hashes[i] == terminal_node_item_hash and item_inclusions[i]:
                        item_inclusions[i] = False
                        break

            item_inclusion_string = str([1 if item_included else 0 for item_included in item_inclusions])

            return item_inclusion_string

        def get_unmerged_item_inclusion_string(terminal_node_knapsack_items: list[KnapsackItem], master_knapsack_items: list[KnapsackItem]) -> str:
            """ Return a string of the items included (1s and 0s) base on the order they are specified in `master_knapsack_items`.

            This method does not merge repeated items. It looks at which item was included and prints that, rather than shifting all distribution to the first instance of a repeated item."""
            item_inclusions = [True] * len(master_knapsack_items)

            for terminal_node_item in terminal_node_knapsack_items:
                for i in range(len(master_knapsack_items) - 1, -1, -1):
                    if master_knapsack_items[i] is terminal_node_item and item_inclusions[i]:
                        item_inclusions[i] = False
                        break

            item_inclusion_string = str([1 if item_included else 0 for item_included in item_inclusions])

            return item_inclusion_string

        validate_distribution(distribution)
        validate_print_parameters(parameters, print_threshold)

        print("Inputs\n")
        if parameters: print(f"Parameters: \u03b1 = {parameters[0]}, \u03B2 = {parameters[1]}, \u03b3 = {parameters[2]}, \u03B4 = {parameters[3]}\n")  # alpha (\u03b1), beta (\u03B2), gamma (\u03b3), delta (\u03B4)
        print("Knapsack Problem Variant: Optimisation\n")
        print("Items: " + ", ".join([str(knapsack_item) for knapsack_item in master_knapsack_instance.knapsack_items]) + "\n")
        print(f"Budget: {master_knapsack_instance.knapsack_capacity}\n")

        print("-------------------------------------\n")

        print("Output\n")
        print("Terminal Nodes (*** for optimal):")

        merged_distribution: dict[str, float] = {}
        item_inclusion_string_to_first_instance: dict[str, int] = {}

        for knapsack_instance_hash, distribution_percentage in distribution.items():
            child_knapsack_instance = KnapsackInstance.instance_by_hash[knapsack_instance_hash]
            item_inclusion_string = get_item_inclusion_string(child_knapsack_instance.knapsack_items_repr_hashes, master_knapsack_instance.knapsack_items_repr_hashes)

            if item_inclusion_string not in merged_distribution:
                merged_distribution[item_inclusion_string] = 0.0
                item_inclusion_string_to_first_instance[item_inclusion_string] = knapsack_instance_hash

            merged_distribution[item_inclusion_string] += distribution_percentage

        for item_inclusion_string, distribution_percentage in dict(sorted(merged_distribution.items(), key=lambda x: x[1], reverse=True)).items():
            if distribution_percentage >= print_threshold:

                child_knapsack_instance = KnapsackInstance.instance_by_hash[item_inclusion_string_to_first_instance[item_inclusion_string]]

                print(f"{item_inclusion_string} - Σv: {child_knapsack_instance.standing_value}, Σw: {master_knapsack_instance.knapsack_capacity - child_knapsack_instance.knapsack_capacity} / {master_knapsack_instance.knapsack_capacity} - {100.0 * distribution_percentage:.3f}%{" ***" if hash(child_knapsack_instance) in master_knapsack_instance.optimal_terminal_nodes else ""}")


        if show_unmerged_distribution:
            print("\n---\n\nUnmerged Terminal Nodes:")

            for knapsack_instance_hash, distribution_percentage in dict(sorted(distribution.items(), key=lambda x: x[1], reverse=True)).items():
                if distribution_percentage >= print_threshold:
                    child_knapsack_instance = KnapsackInstance.instance_by_hash[knapsack_instance_hash]
                    item_inclusion_string = get_unmerged_item_inclusion_string(child_knapsack_instance.knapsack_items, master_knapsack_instance.knapsack_items)

                    print(f"{item_inclusion_string} - Σv: {child_knapsack_instance.standing_value}, Σw: {master_knapsack_instance.knapsack_capacity - child_knapsack_instance.knapsack_capacity} / {master_knapsack_instance.knapsack_capacity} - {100.0 * distribution_percentage:.3f}%{" ***" if hash(child_knapsack_instance) in master_knapsack_instance.optimal_terminal_nodes else ""}")

        print(f"\nTotal Distribution: {sum(merged_distribution.values())}\n")
        print(f"Number of Terminal Nodes: {len(merged_distribution)} (unmerged: {len(distribution)})\n")


def solve_decision_variant(master_knapsack_instance: KnapsackInstance, param_alpha: float, param_beta: float, param_gamma: float, param_delta: float, value_threshold: int) -> float:
        """ Return the probability that a decision-maker finds a witness for the decision variant.

        Returns the expected fraction of the time (as a probability between 0 and 1) that a
        decision-maker with the given parameters reaches a feasible terminal node whose total value
        meets or exceeds `value_threshold` (the target).

        Parameters
        ----------
        master_knapsack_instance : KnapsackInstance
            The root knapsack to solve.
        param_alpha : float
            Search / global-optimisation parameter. `param_alpha` = 0 is the special case of never
            searching for a witness, used for 'item-by-item' search.
        param_beta : float
            Density-preference (local-optimisation) parameter.
        param_gamma : float
            Complexity-aversion (weight-preference) parameter.
        param_delta : float
            Item-level rationality (dominance-avoidance) parameter.
        value_threshold : int
            The target value a witness must reach.

        Raises
        ------
        TypeError
            if any of `param_alpha`, `param_beta`, `param_gamma`, `param_delta` is not a `float`, or
            `value_threshold` is not an `int`.
        ValueError
            if any parameter is out of range, or `value_threshold` is negative.

        Returns
        -------
        percent_witness_found : float
            The expected probability that a witness is successfully found.
        """

        _validate_parameters_and_value_threshold(param_alpha, param_beta, param_gamma, param_delta, ProblemType.DECISION, value_threshold)

        node_distribution = get_node_distribution(master_knapsack_instance, param_alpha, param_beta, param_gamma, param_delta, ProblemType.DECISION, value_threshold)
        percent_witness_found = sum([distribution_percentage for knapsack_instance_hash, distribution_percentage in node_distribution.items() if KnapsackInstance.instance_by_hash[knapsack_instance_hash].standing_value >= value_threshold])

        return percent_witness_found
