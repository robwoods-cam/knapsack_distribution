"""
Tools for calculating probabilistic choice distributions in knapsack problem instances.

This module provides the `ProblemType` Enum.
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


from enum import Enum, auto


class ProblemType(Enum):
    """ The variant of Knapsack Problem to solve.

    A selection of items is *feasible* when its total weight does not exceed the capacity.

    Attributes
    ----------
    OPTIMISATION
        Find the maximum total value achievable by a feasible selection of items.
    DECISION
        Determine (`True`/`False`) whether some feasible selection reaches a target total value.
        Such a satisfying selection is called a *witness*.
    """
    OPTIMISATION = auto()
    DECISION = auto()
