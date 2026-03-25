"""Schema version constants for the Character Pack format."""

CURRENT_SCHEMA_VERSION: str = "1.1"
MIN_COMPAT_SCHEMA_VERSION: str = "1.0"

SUPPORTED_SCHEMA_VERSIONS: frozenset[str] = frozenset({"1.0", "1.1"})


def is_supported(version: str) -> bool:
    """Return True if this version can be loaded by the current runtime."""
    return version in SUPPORTED_SCHEMA_VERSIONS


def is_current(version: str) -> bool:
    """Return True if this version matches the current schema exactly."""
    return version == CURRENT_SCHEMA_VERSION
