"""
simpl-temp - Professional Python library for temporary data management.

Author: Kozosvyst Stas (StasX)
Year: 2025
License: MIT
"""

from .core import sTemp
from .exceptions import SimplTempError, ConfigurationError, StorageError, ExpiredDataError

__version__ = "1.0.0"
__author__ = "Kozosvyst Stas (StasX)"
__license__ = "MIT"

__all__ = [
    "sTemp",
    "SimplTempError",
    "ConfigurationError", 
    "StorageError",
    "ExpiredDataError",
]
