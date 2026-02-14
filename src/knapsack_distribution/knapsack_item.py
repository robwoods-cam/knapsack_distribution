"""
Tools for calculating probabilistic choice distributions in knapsack problem instances.

This module provides the `KnapsackItem` dataclass and supporting functionality.  
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
from dataclasses import dataclass, field
from typing import ClassVar
import hashlib


@dataclass(frozen=True, slots=True)
class KnapsackItem:
    """
    A dataclass to represent a Knapsack Item.

    Attributes
    ----------
    value : int
        the value of the knapsack item
    weight : int
        the weight of the knapsack item
    density : float
        the density (`value` / `weight`) of the knapsack item
    knapsack_item_id:
        an id for the knapsack item unique to the knapsack problem instance (not to the value and weight of the knapsack item)
    __hash__ : int
        unique hash for the knapsack item (repeated items have a unique hash based on their `knapsack_item_id`)

    Class Attributes
    ----------------
    _knapsack_items_count : int
        the number of knapsack items created, used for internal ids and hashes

    Notes
    -----
    * `__eq__` and `__gt__` are overridden to allow sorting of `KnapsackItem`s so `KnapsackInstance` can create
    a unique hash based on the items available to allow for nodes to merge and save computational resources.
    * self == other and hash(self) == hash(other) may give different results. __eq__ only compares the value and 
    weight of the item, allowing for sorting. However, the hash looks for unique items for branching.
    This means that `KnapsackItem`s should not be used as keys or in sets.
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
        """ creates and returns a `list` of `KnapsackItem`s from an equal list of `values` and `weights`

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
        if not (isinstance(values, list) and all((isinstance(value, int) and not isinstance(value, bool)) for value in values)):
            raise TypeError("values must be a list of ints.")
        if not (isinstance(weights, list) and all((isinstance(weight, int) and not isinstance(weight, bool)) for weight in weights)):
            raise TypeError("weights must be a list of ints.")
        if len(values) != len(weights):
            raise ValueError(f"Length of values and weights must be equal, got {len(values)} (values) and {len(weights)} (weights).")

        knapsack_items: list[KnapsackItem] = []
        for value, weight in zip(values, weights):
            knapsack_items.append(cls(value, weight))

        return knapsack_items

    def __post_init__(self) -> None:
        """ creates (post) a `KnapsackItem`

        Raises
        ------
        TypeError
            if `value` and `weight` are not both `int`s
        ValueError
            if `value` is negative or `weight` is not positive 
        """

        if not (isinstance(self.value, int) and not isinstance(self.value, bool)):
            raise TypeError(f"value must be of type int, is {type(self.value)}.")
        
        if self.value < 0:
            raise ValueError(f"value must be non-negative, is {self.value}.")        
        
        if not (isinstance(self.weight, int) and not isinstance(self.weight, bool)):
            raise TypeError(f"weight must be of type int, is {type(self.weight)}.")
        
        if self.weight <= 0:
            raise ValueError(f"weight must be positive, is {self.weight}.")
        
        object.__setattr__(self, "density", self.value / self.weight)
        object.__setattr__(self, "knapsack_item_id", self.__class__._knapsack_items_count)

        h = hashlib.sha256(
            f"{self.value},{self.weight},{self.knapsack_item_id}".encode()
        ).digest()
        object.__setattr__(self, "_full_hash", h)

        KnapsackItem._knapsack_items_count += 1

    def __eq__(self, other: object) -> bool:
        """ Note that self == other and hash(self) == hash(other) do not return the same result """
        if not isinstance(other, KnapsackItem):
            return NotImplemented
        return self.value == other.value and self.weight == other.weight

    def __gt__(self, other: object) -> bool:
        if not isinstance(other, KnapsackItem):
            return NotImplemented
        return self != other and (self.density > other.density or (self.density == other.density and self.value > other.value))
    
    def __lt__(self, other: object) -> bool:
        if not isinstance(other, KnapsackItem):
            return NotImplemented
        return self != other and (self.density < other.density or (self.density == other.density and self.value < other.value))

    def __hash__(self) -> int:
        """ Python uses 61 bit hashes (on 64-bit implementations), so we use the first 7 bytes of the SHA-256 as the hash. 
        
        This only works on 64-bit implementations of Python.
        Note that self == other and hash(self) == hash(other) do not return the same result.
        """
        return int.from_bytes(self._full_hash[:7], 'big')

    def __str__(self) -> str:
        return f'(v: {self.value}, w: {self.weight})'

    def __repr__(self) -> str:
        return f'KnapsackItem(value = {self.value}, weight = {self.weight})'

    @property
    def knapsack_detailed_repr(self) -> str:
        """ Returns the representation including the knapsack_item_id """
        return f'KnapsackItem(value = {self.value}, weight = {self.weight}, id = {self.knapsack_item_id})'
