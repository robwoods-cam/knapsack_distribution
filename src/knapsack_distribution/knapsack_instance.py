"""
Tools for calculating probabilistic choice distributions in knapsack problem instances.

This module provides the `KnapsackInstance` dataclass and supporting functionality.
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


from __future__ import annotations
from dataclasses import dataclass
from typing import ClassVar
import hashlib
from .knapsack_item import KnapsackItem


@dataclass(init=False, frozen=True, slots=True)
class KnapsackInstance:
    """ A node in the knapsack search tree, representing a (sub)problem reached by including zero or
    more items so far.

    The root node is the full problem (all items available, full capacity, nothing included). Each
    child node is reached by adding one feasible item: that item moves from `knapsack_items` to
    `standing_knapsack_items`, `knapsack_capacity` drops by its weight, and `standing_value` rises by
    its value. A node whose state has been seen before (under the same master knapsack) is reused
    rather than rebuilt — see `create` and `instance_by_hash`.

    Instances are immutable and must be built with `create`; `__init__` is disabled.


    Pure knapsack Attributes
    ------------------------
    knapsack_items : tuple[KnapsackItem, ...]
        The `KnapsackItem`s still available to add at this node. This is **not** the items already
        included in the knapsack so far (that is `standing_knapsack_items`).
    knapsack_capacity : int
        The remaining weight capacity at this node.

    Downward looking Attributes
    ---------------------------
    child_nodes : tuple[tuple[KnapsackItem, KnapsackInstance], ...] | None
        Every feasible child node, as `(item_added, resulting_node)` pairs, one per item that still
        fits within the remaining capacity. `None` at a terminal node.
    is_terminal_node : bool
        `True` when there are no feasible `child_nodes` (no remaining item fits, or no items are
        left). A terminal node is a complete, capacity-constrained knapsack.
    terminal_nodes : frozenset[int]
        The hashes of every terminal node reachable from this node. A terminal node contains only
        itself. Hashes are stored rather than instances because the custom `__hash__` makes
        instances unsafe as `set` members.
    optimal_terminal_nodes : frozenset[int]
        The hashes of the reachable terminal node(s) with the highest `standing_value`. A terminal
        node contains only itself. There may be higher-value terminal nodes under the master
        knapsack that are unreachable from this branch.
    _optimal_terminal_node_value : int
        The `standing_value` shared by the `optimal_terminal_nodes`.

    Upward looking Attributes
    -------------------------
    master_knapsack : KnapsackInstance | None
        The root `KnapsackInstance` this node descends from. If this is the root node,
        `master_knapsack` will be `None`.
    standing_value : int, default 0
        The total value of the items included so far (the items in `standing_knapsack_items`).
    standing_knapsack_items : tuple[KnapsackItem, ...]
        The `KnapsackItem`s included to reach this node from the master knapsack.

    Class Attributes
    ----------------
    instance_by_hash : dict[int, KnapsackInstance]
        Maps every created node's hash to the node, so a state reached by multiple paths is built
        once and then reused rather than recreated.


    Class Methods
    -------------
    **create** : *Callable*
        Builds (or reuses) a `KnapsackInstance`; use this rather than `__init__`.


    Notes
    -----
    * Use `create`, not `__init__` (which is fully disabled).
    * The hash includes `master_knapsack`, so an identical item/capacity state reached under a
        different master knapsack is treated as a distinct node and processed again.
    * `__hash__` is unique per node and is the only safe way to key or store a `KnapsackInstance`;
        instances must **not** be placed directly in a `set` or used as a `dict` key.
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
        """ Validate the types and values of the `create` parameters.

        Checks `knapsack_items`, `knapsack_capacity`, `standing_value`, `standing_knapsack_items`,
        and `master_knapsack`.


        Raises
        ------
        TypeError
            if any argument has the wrong type.
        ValueError
            if `knapsack_capacity` or `standing_value` is negative.
        """

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
        """ Create (or reuse) a `KnapsackInstance`; use this rather than `__init__`.

        If a node with the same state already exists in `instance_by_hash`, that existing instance is
        returned rather than creating a new one. Otherwise a new instance is created and its child
        nodes are built recursively, allowing efficient branching where distinct add-orders that
        reach the same state share a single node.


        Parameters
        ----------
        knapsack_items : tuple[KnapsackItem, ...] | list[KnapsackItem]
            All the possible `KnapsackItem`s available to add at this node.
        knapsack_capacity : int
            The remaining weight capacity at this node.
        standing_value : int, default 0
            The total value of the items already included in the knapsack.
        standing_knapsack_items : tuple[KnapsackItem, ...] | list[KnapsackItem] | None, default None
            The items already included to reach this node; `None` is treated as empty.
        master_knapsack : KnapsackInstance | None, default None
            The root `KnapsackInstance` this node descends from. If this is the root node,
            `master_knapsack` will be `None`.


        Raises
        ------
        TypeError
            if `knapsack_items` or `standing_knapsack_items` is not a `list`/`tuple` of
            `KnapsackItem`s, `knapsack_capacity` or `standing_value` is not an `int`, or
            `master_knapsack` is neither a `KnapsackInstance` nor `None`.
        ValueError
            if `knapsack_capacity` or `standing_value` is negative.
        RuntimeError
            if a hash collision is detected between two different nodes.


        Returns
        -------
        KnapsackInstance
            The newly created or previously cached node.
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

        # A terminal node is its own (only) terminal node
        terminal_nodes: set[int] = set() if self.child_nodes else {hash(self)}
        if self.child_nodes:
            for _, child_node in self.child_nodes:
                if child_node.is_terminal_node:
                    terminal_nodes.add(hash(child_node))
                else:
                    terminal_nodes.update(child_node.terminal_nodes)
        object.__setattr__(self, "terminal_nodes", frozenset(terminal_nodes))

        object.__setattr__(self, "_optimal_terminal_node_value", self.standing_value if not self.child_nodes
            else max(child_node._optimal_terminal_node_value for _, child_node in self.child_nodes))

        # A terminal node is its own (only, so optimal) terminal node
        optimal_terminal_nodes: set[int] = set() if self.child_nodes else {hash(self)}
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
        """ Return a 56-bit hash derived from the first 7 bytes of the node's SHA-256 digest.

        CPython uses 61-bit hashes on 64-bit builds, so 7 bytes (56 bits) fit safely; this requires
        a 64-bit interpreter.
        """
        return int.from_bytes(self._full_hash[:7], 'big')

    def _create_child_nodes(self) -> tuple[tuple[KnapsackItem, KnapsackInstance], ...] | None:
        """ Recursively build and return every feasible child node, or `None` if no item fits. """
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
        """ The `hash` of each available item's `repr`.

        Because `repr` omits `knapsack_item_id`, identical items share a value here. This lets
        `print_node_distribution` merge nodes that differ only by which copy of a repeated identical
        item was included.
        """
        return [hash(repr(knapsack_item)) for knapsack_item in self.knapsack_items]
