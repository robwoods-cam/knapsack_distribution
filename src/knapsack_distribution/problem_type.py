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
    """ The types of Knapsack Problem.

    OPTIMISATION: Find the maximum net value of a feasible selection of items.
    DECISION: Find any feasible selection of items, if it exists, to state (True or False) that a target
    net value can be reached.
    A feasible selection of items requires the net weight to be less than or equal to the capacity."""
    OPTIMISATION = auto()
    DECISION = auto()
