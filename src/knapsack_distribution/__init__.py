"""
Tools for calculating probabilistic choice distributions in knapsack problem instances.

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


import sys
import struct

# Enforce 64-bit interpreter for long hashes
if struct.calcsize("P") * 8 != 64:
    raise EnvironmentError("This package requires a 64-bit Python interpreter.")

# Enforce Python version (3.12+
if sys.version_info < (3, 12):
    sys.exit("Python 3.12 or later is required.")

from ._version import __version__

from .knapsack_item import KnapsackItem
from .knapsack_instance import KnapsackInstance
from .problem_type import ProblemType
from .distribution import get_node_distribution, print_node_distribution, solve_decision_variant

__all__ = [
    "KnapsackItem",
    "KnapsackInstance",
    "ProblemType",
    "get_node_distribution",
    "print_node_distribution",
    "solve_decision_variant",
    "__version__"
]
