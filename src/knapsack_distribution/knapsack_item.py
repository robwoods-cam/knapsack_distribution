"""
Tools for calculating probabilistic choice distributions in knapsack problem instances.

This module provides the `KnapsackItem` dataclass and supporting functionality.
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

import hashlib
from dataclasses import dataclass, field
from typing import ClassVar


@dataclass(frozen=True, slots=True)
class KnapsackItem:
    """
    An immutable item that can be placed in a knapsack, defined by its `value` and `weight`.

    Items are created directly (``KnapsackItem(value, weight)``) or in bulk via `create_from_list`.
    Each item is assigned a globally unique `knapsack_item_id`, so two items with identical `value`
    and `weight` are still distinguished by their hash.

    Attributes
    ----------
    value : int
        The value of the knapsack item (positive).
    weight : int
        The weight of the knapsack item (positive).
    density : float
        The density (`value` / `weight`) of the knapsack item, computed on creation.
    knapsack_item_id : int
        An id unique to this `KnapsackItem` instance (not to its `value` and `weight`); two items
        with the same `value` and `weight` receive different ids.


    Class Attributes
    ----------------
    _knapsack_items_count : int
        A running count of `KnapsackItem`s created, used to assign each new item's
        `knapsack_item_id` and hash.


    Notes
    -----
    * `__eq__`, `__gt__`, and `__lt__` are overridden so `KnapsackItem`s can be sorted by density.
        Equality and ordering compare only `value` and `weight`, which lets `KnapsackInstance` build
        a stable hash from the items available at a node and merge equivalent nodes to save
        computation.
    * `__eq__` and `__hash__` are deliberately inconsistent: ``self == other`` compares only `value`
        and `weight` (for sorting), whereas `__hash__` is unique per item (for branching). Because of
        this, `KnapsackItem`s must **not** be used directly as `set` elements or `dict` keys; use
        their `hash` instead.
    """

    value: int
    weight: int
    density: float = field(init=False)
    knapsack_item_id: int = field(init=False)
    _full_hash: bytes = field(init=False, repr=False)

    # class attributes
    _knapsack_items_count: ClassVar[int] = 0

    @classmethod
    def create_from_list(cls, values: list[int], weights: list[int]) -> list[KnapsackItem]:
        """ Create and return a `list` of `KnapsackItem`s from equal-length lists of `values` and `weights`.


        Parameters
        ----------
        values : list[int]
            The values of the `KnapsackItem`s to be created, in order.
        weights : list[int]
            The weights of the `KnapsackItem`s to be created, in order.


        Raises
        ------
        TypeError
            if `values` and `weights` are not both `list`s of `int`s.
        ValueError
            if `values` and `weights` are not of equal length.


        Returns
        -------
        knapsack_items : list[KnapsackItem]
            the newly created `KnapsackItem`s.
        """
        if not (isinstance(values, list) and all((isinstance(value, int)
            and not isinstance(value, bool)) for value in values)):
            raise TypeError("values must be a list of ints.")
        if not (isinstance(weights, list) and all((isinstance(weight, int)
            and not isinstance(weight, bool)) for weight in weights)):
            raise TypeError("weights must be a list of ints.")
        if len(values) != len(weights):
            raise ValueError(f"Length of values and weights must be equal, got {len(values)} (values) and"
                f" {len(weights)} (weights).")

        knapsack_items: list[KnapsackItem] = []
        for value, weight in zip(values, weights):
            knapsack_items.append(cls(value, weight))

        return knapsack_items

    def __post_init__(self) -> None:
        """ Validate inputs and finish initialising the `KnapsackItem`.

        Computes `density`, assigns the unique `knapsack_item_id`, and builds the item's hash.


        Raises
        ------
        TypeError
            if `value` or `weight` is not an `int`.
        ValueError
            if `value` or `weight` is not positive.
        """
        if not (isinstance(self.value, int) and not isinstance(self.value, bool)):
            raise TypeError(f"value must be of type int, is {type(self.value)}.")

        # Zero-value items never need to be added, so are not allowed (their zero density also breaks the distribution)
        if self.value <= 0:
            raise ValueError(f"value must be positive, is {self.value}. Items with zero or negative value make no sense to include in a knapsack, so should be removed from the instance before analysing.")

        if not (isinstance(self.weight, int) and not isinstance(self.weight, bool)):
            raise TypeError(f"weight must be of type int, is {type(self.weight)}.")

        if self.weight <= 0:
            raise ValueError(f"weight must be positive, is {self.weight}.")

        object.__setattr__(self, "density", self.value / self.weight)
        object.__setattr__(self, "knapsack_item_id", self.__class__._knapsack_items_count)

        full_hash = hashlib.sha256(
            f"{self.value},{self.weight},{self.knapsack_item_id}".encode()
        ).digest()
        object.__setattr__(self, "_full_hash", full_hash)

        KnapsackItem._knapsack_items_count += 1

    def __eq__(self, other: object) -> bool:
        """ Compare two `KnapsackItem`s by `value` and `weight` only.

        Note that ``self == other`` and ``hash(self) == hash(other)`` need not agree: equality
        ignores `knapsack_item_id` but the hash does not.
        """
        if not isinstance(other, KnapsackItem):
            return NotImplemented
        return self.value == other.value and self.weight == other.weight

    def __gt__(self, other: object) -> bool:
        """ Order by density (greater density is greater), breaking ties by `value`; equal items are neither greater nor less. """
        if not isinstance(other, KnapsackItem):
            return NotImplemented
        # self.value * other.weight is used as a proxy for density to avoid float comparisons
        return self != other and (self.value * other.weight > other.value * self.weight or
            (self.value * other.weight == other.value * self.weight and self.value > other.value))

    def __lt__(self, other: object) -> bool:
        """ Order by density (lesser density is less), breaking ties by `value`; equal items are neither greater nor less. """
        if not isinstance(other, KnapsackItem):
            return NotImplemented
        # self.value * other.weight is used as a proxy for density to avoid float comparisons
        return self != other and (self.value * other.weight < other.value * self.weight or
            (self.value * other.weight == other.value * self.weight and self.value < other.value))

    def __hash__(self) -> int:
        """ Return a 56-bit hash derived from the first 7 bytes of the item's SHA-256 digest.

        CPython uses 61-bit hashes on 64-bit builds, so 7 bytes (56 bits) fit safely; this requires
        a 64-bit interpreter. The hash is unique per item: note that ``self == other`` and
        ``hash(self) == hash(other)`` need not agree (see `__eq__`).
        """
        return int.from_bytes(self._full_hash[:7], 'big')

    def __str__(self) -> str:
        return f'(v: {self.value}, w: {self.weight})'

    def __repr__(self) -> str:
        return f'KnapsackItem(value = {self.value}, weight = {self.weight})'

    @property
    def knapsack_detailed_repr(self) -> str:
        """ Return a `repr`-style string that also includes the `knapsack_item_id`. """
        return f'KnapsackItem(value = {self.value}, weight = {self.weight}, id = {self.knapsack_item_id})'
