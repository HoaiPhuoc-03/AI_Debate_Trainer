class StorageError(RuntimeError):
    """Base error for configured storage backends."""


class StorageConfigurationError(StorageError):
    """Raised when a selected storage backend is not configured."""
