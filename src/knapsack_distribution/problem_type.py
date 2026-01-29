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


from enum import Enum, auto

class ProblemType(Enum):
    """ The types of Knapsack Problem.
    
    Optimisation requires finding the maximum net value of a feasible selection of items.
    Decision requires finding any feasible selection of items, if it exists, to state (True or False) that a target
    net value can be reached.
    A feasible selection of items requires the net weight to be less than or equal to the capacity."""
    OPTIMISATION = auto()
    DECISION = auto()
