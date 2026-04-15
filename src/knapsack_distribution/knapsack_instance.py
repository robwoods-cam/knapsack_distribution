"""
Tools for calculating probabilistic choice distributions in knapsack problem instances.

This module provides the `KnapsackInstance` dataclass and supporting functionality.
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


from __future__ import annotations
from dataclasses import dataclass
from typing import ClassVar
import hashlib
from .knapsack_item import KnapsackItem


@dataclass(init=False, frozen=True, slots=True)
class KnapsackInstance:
    """ A dataclass to represent a Knapsack Problem Instance.


    Pure knapsack Attributes
    ------------------------
    knapsack_items : tuple[KnapsackItem, ...]
        All the possible `KnapsackItem`s to consider for addition to this node.
        This is **not** the items included in the knapsack so far (that is `standing_knapsack_items`)
    knapsack_capacity : int
        The weight capacity of the `KnapsackInstance`, the remaining capacity for a child node (sub instance)
    __hash__ : int
        A unique value for the `KnapsackInstance`, this allows for multiple pathways to reach the same node and not
        require recalculation

    Downward looking Attributes
    ---------------------------
    child_nodes : tuple[tuple[KnapsackItem, KnapsackInstance], ...] | None
        All feasible (fits within constraint) child nodes created by adding one item to this node.
        The `tuple` has the `KnapsackItem` to be added and the `KnapsackInstance` adding it creates.
    is_terminal_node : bool
        A node is a terminal node if there are no possible feasible `child_nodes`.
        A terminal node has no further child nodes, either because no further items fit or there are no items left.
        This is also known as a capacity-constrained node or knapsack.
    terminal_nodes  : frozenset[int]
        The hashes of all `child_nodes` which are `terminal`.
        Uses hash rather than KnapsackInstance instance due to set and the hash function being changed.
    optimal_terminal_nodes : frozenset[int]
        The hashes of all optimal (highest `standing_value`) feasible `child_node`.
        Uses hash rather than KnapsackInstance instance due to set and the hash function being changed.
    _optimal_terminal_node_value : int
        The value of the optimal terminal nodes (optimal only adding items from here)

    Upward looking Attributes
    -------------------------
    master_knapsack : KnapsackInstance | None
        The original `KnapsackInstance` which this node spawned from.
        If this is the original node, `master_knapsack` will be `None`
    standing_value : int, default 0
        The sum of values of items included in the knapsack
    standing_knapsack_items : tuple[KnapsackItem, ...]
        All `KnapsackItem`s included to create this node from the `master_node` knapsack

    Class Attributes
    ----------------
    instance_by_hash : dict[int, KnapsackInstance]
        a `dict` which can look up all created `KnapsackInstance`s based on their hash.
        This allows merging of nodes as the same node does not need to be recreated, but instead referenced.


    Class Methods
    -------------
    **create** : *Callable*
        create is used to create a `KnapsackInstance`.
        `create` should be used rather than `__init__`.


    Notes
    -----
    * `create` should be used rather than `__init__` (init is fully disabled)
    * hash includes the master_knapsack, this means if we get to an identical node but from a different starting
        knapsack, everything will be processed again.
    * self == other and hash(self) == hash(other) may give different results. __eq__ only compares the value and
        weight of the item, allowing for sorting. However, the hash looks for unique items for branching.
        This means that `KnapsackInstance`s should **not** be used as keys or in sets, but their hash instead.
    """
    knapsack_items: tuple[KnapsackItem, ...]
    knapsack_capacity: int
    standing_value: int
    standing_knapsack_items: tuple[KnapsackItem, ...]
    master_knapsack: KnapsackInstance | None

    _full_hash: bytes

    child_nodes: tuple[tuple[KnapsackItem, KnapsackInstance], ...] | None
    terminal_nodes: frozenset[int]
    is_terminal_node: bool
    optimal_terminal_nodes: frozenset[int]
    _optimal_terminal_node_value: int

    # class attributes
    instance_by_hash: ClassVar[dict[int, KnapsackInstance]] = {}

    @staticmethod
    def _validate_knapsack_parameters(
        knapsack_items: tuple[KnapsackItem, ...] | list[KnapsackItem],
        knapsack_capacity: int, standing_value: int,
        standing_knapsack_items: tuple[KnapsackItem, ...] | list[KnapsackItem],
        master_knapsack: KnapsackInstance | None
        ) -> None:
        """ Validate the type and value of `knapsack_items`, `knapsack_capacity`, `standing_value`,
        `standing_knapsack_items`, `master_knapsack` """

        if not (isinstance(knapsack_items, tuple | list) and
                all(isinstance(knapsack_item, KnapsackItem) for knapsack_item in knapsack_items)):
            raise TypeError("`knapsack_items` must be a `tuple` or `list` of `KnapsackItem`s.")

        if not isinstance(knapsack_capacity, int) or isinstance(knapsack_capacity, bool):
            raise TypeError(f"`knapsack_capacity` must be int, is {type(knapsack_capacity)}")

        if knapsack_capacity < 0:
            raise ValueError(f"`knapsack_capacity` must be positive, is {knapsack_capacity}.")

        if not isinstance(standing_value, int) or isinstance(standing_value, bool):
            raise TypeError(f"`standing_value` must be int, is {type(standing_value)}")

        if standing_value < 0:
            raise ValueError(f"`standing_value` must be non-negative, is {standing_value}.")

        if not (isinstance(standing_knapsack_items, tuple | list | None) and
                all(isinstance(knapsack_item, KnapsackItem) for knapsack_item in standing_knapsack_items)):
            raise TypeError("`standing_knapsack_items` must be a `tuple` or `list` of `KnapsackItem`s, or is None")

        if not isinstance(master_knapsack, KnapsackInstance | None):
            raise TypeError(f"`master_knapsack` must be of type `KnapsackInstance` or is None,"
                f" is {type(master_knapsack)}.")

    @classmethod
    def create(
        cls,
        knapsack_items: tuple[KnapsackItem, ...] | list[KnapsackItem],
        knapsack_capacity: int,
        standing_value: int = 0,
        standing_knapsack_items: tuple[KnapsackItem, ...] | list[KnapsackItem] | None = None,
        master_knapsack: KnapsackInstance | None = None
        ) -> KnapsackInstance:
        """ `KnapsackInstance.create()` should be used rather than `__init__`

        If a node (`KnapsackInstance`) already exists, the existing instance will be returned, rather than creating a
        new one. If it does not already exist, a new instance will be created allowing for efficient branching.


        Parameters
        ----------
        knapsack_items : tuple[KnapsackItem, ...] | list[KnapsackItem]
            a `list` of all the possible `KnapsackItem`s that should be considered
        knapsack_capacity : int
            the weight capacity of the `KnapsackInstance`, the remaining capacity for a child node (sub instance)
        standing_knapsack_items : tuple[KnapsackItem, ...] | list[KnapsackItem] | None (default None)
            the items already standing in the knapsack instance
        standing_value : int, default 0
            the sum of values of items already included in the knapsack
        master_knapsack : KnapsackInstance | None
            the original `KnapsackInstance` which this node spawned from. If this is the original node,
            `master_knapsack` will be `None`


        Raises
        ------
        TypeError
            if `knapsack_items` and `standing_knapsack_items` are not a list or tuples of `KnapsackItem`s,
            knapsack_capacity and standing_value are not `int`s,or `master_knapsack` is not either a `KnapsackInstance`
            or `None.
        ValueError
            if `knapsack_capacity` or `standing_value` are negative.


        Returns
        -------
            KnapsackInstance
        """
        standing_knapsack_items = [] if standing_knapsack_items is None else standing_knapsack_items
        cls._validate_knapsack_parameters(knapsack_items, knapsack_capacity, standing_value,
            standing_knapsack_items, master_knapsack)

        hash_string = str(sorted(knapsack_items, key=lambda knapsack_item: hash(knapsack_item))) + "," + str(knapsack_capacity) + \
            "," + str(standing_value) + "," + \
            str([hash(knapsack_item) for knapsack_item in sorted(standing_knapsack_items, key=lambda knapsack_item: hash(knapsack_item))]) + "," + \
            str(hash(master_knapsack))
        knapsack_full_hash = hashlib.sha256(hash_string.encode("utf-8")).digest()
        knapsack_hash = int.from_bytes(knapsack_full_hash[:7], 'big')

        if knapsack_hash in cls.instance_by_hash:
            if cls.instance_by_hash[knapsack_hash]._full_hash != knapsack_full_hash:
                raise RuntimeError(f"There is a hash collision (hash: {knapsack_hash})")
            return cls.instance_by_hash[knapsack_hash]

        self = object.__new__(cls)

        object.__setattr__(self, "knapsack_items", tuple(knapsack_items))
        object.__setattr__(self, "knapsack_capacity", knapsack_capacity)
        object.__setattr__(self, "standing_value", standing_value)
        object.__setattr__(self, "standing_knapsack_items", tuple(standing_knapsack_items))
        object.__setattr__(self, "master_knapsack", master_knapsack)
        object.__setattr__(self, "_full_hash", knapsack_full_hash)

        object.__setattr__(self, "child_nodes", self._create_child_nodes())

        object.__setattr__(self, "is_terminal_node", self.child_nodes is None)

        terminal_nodes: set[int] = set()
        if self.child_nodes:
            for _, child_node in self.child_nodes:
                if child_node.is_terminal_node:
                    terminal_nodes.add(hash(child_node))
                else:
                    terminal_nodes.update(child_node.terminal_nodes)
        object.__setattr__(self, "terminal_nodes", frozenset(terminal_nodes))

        object.__setattr__(self, "_optimal_terminal_node_value", self.standing_value if not self.child_nodes
            else max(child_node._optimal_terminal_node_value for _, child_node in self.child_nodes))

        optimal_terminal_nodes: set[int] = set()
        if self.child_nodes:
            for _, child_node in self.child_nodes:
                if child_node._optimal_terminal_node_value == self._optimal_terminal_node_value:
                    if child_node.is_terminal_node:
                        optimal_terminal_nodes.add(hash(child_node))
                    else:
                        optimal_terminal_nodes.update(child_node.optimal_terminal_nodes)
                elif child_node._optimal_terminal_node_value > self._optimal_terminal_node_value:
                    raise ValueError('There should be no child nodes with value greater than the optimal terminal node'
                        ' value')
        object.__setattr__(self, "optimal_terminal_nodes", frozenset(optimal_terminal_nodes))

        self.instance_by_hash[hash(self)] = self

        return self

    def __hash__(self) -> int:
        """ Python uses 61 bit hashes (64-bit implementations), so we use the first 7 bytes of the SHA-256 as the hash.

        This only works on 64-bit implementations of Python."""
        return int.from_bytes(self._full_hash[:7], 'big')

    def _create_child_nodes(self) -> tuple[tuple[KnapsackItem, KnapsackInstance], ...] | None:
        """ recursively create all the child nodes from this node """
        if len(self.knapsack_items) == 0:
            return None

        child_nodes: list[tuple[KnapsackItem, KnapsackInstance]] = []

        for i, knapsack_item in enumerate(self.knapsack_items):
            knapsack_capacity = self.knapsack_capacity - self.knapsack_items[i].weight
            if knapsack_capacity >= 0:
                master_knapsack: KnapsackInstance = self.master_knapsack if self.master_knapsack else self
                standing_value = self.standing_value + self.knapsack_items[i].value
                standing_knapsack_items = self.standing_knapsack_items + (self.knapsack_items[i], )
                child_node = KnapsackInstance.create(self.knapsack_items[:i] + self.knapsack_items[i + 1:],
                    knapsack_capacity, standing_value, standing_knapsack_items,
                    master_knapsack)
                child_nodes.append((knapsack_item, child_node))

        return tuple(child_nodes) if child_nodes else None

    @property
    def knapsack_items_repr_hashes(self) -> list[int]:
        """ The hash of repr of each item.
        This is used to merge identical items as repr will give the same hash for identical items."""
        return [hash(repr(knapsack_item)) for knapsack_item in self.knapsack_items]
