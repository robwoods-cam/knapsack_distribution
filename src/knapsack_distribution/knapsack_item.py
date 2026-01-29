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
        an id for the knapsack item unique to the knapsack problem instance (not to the value and weight of the knapsack item)
    __hash__ : int
        unique hash for the knapsack item (repeated items have a unique hash based on their item id)


    Notes
    -----
    * `__eq__` and `__gt__` are overridden to allow sorting of `KnapsackItem`s to allow a `KnapsackInstance` to create
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
    _dominating_knapsack_item_hashes: set[int] | None  # move out of class

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
        """ the id of the knapsack item unique to the knapsack problem instance """
        return self._knapsack_item_id

    @property
    def knapsack_detailed_repr(self) -> str:
        """ Returns the representation including the knapsack_item_id """
        return f'KnapsackItem(value = {self._value}, weight = {self._weight}, id = {self._knapsack_item_id})'

    def set_dominance(self, knapsack_items: list[KnapsackItem]) -> None:  # move out of class
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

    def check_dominance(self, knapsack_items: list[KnapsackItem]) -> bool:  # move out of class
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

