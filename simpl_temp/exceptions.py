"""
Custom exceptions for simpl-temp library.
"""


class SimplTempError(Exception):
    """Base exception for simpl-temp library."""
    pass


class ConfigurationError(SimplTempError):
    """Raised when configuration is invalid or missing."""
    pass


class StorageError(SimplTempError):
    """Raised when storage operations fail."""
    pass


class ExpiredDataError(SimplTempError):
    """Raised when trying to access expired data."""
    pass
