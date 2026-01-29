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


import sys
import struct

# Enforce 64-bit interpreter for long hashes
if struct.calcsize("P") * 8 != 64:
    raise EnvironmentError("This package requires a 64-bit Python interpreter.")

# Enforce Python version (3.14+
if sys.version_info < (3, 14):
    sys.exit("Python 3.14 or later is required.")

from ._version import __version__

from .knapsack_item import KnapsackItem
from .knapsack_instance import KnapsackInstance
from .problem_type import ProblemType

__all__ = [
    "KnapsackItem",
    "KnapsackInstance",
    "ProblemType",
    "__version__"
]
