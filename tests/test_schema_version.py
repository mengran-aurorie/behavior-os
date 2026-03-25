from agentic_mindset.schema.version import (
    CURRENT_SCHEMA_VERSION,
    MIN_COMPAT_SCHEMA_VERSION,
    SUPPORTED_SCHEMA_VERSIONS,
    is_supported,
    is_current,
)


def test_current_schema_version():
    assert CURRENT_SCHEMA_VERSION == "1.1"


def test_min_compat_schema_version():
    assert MIN_COMPAT_SCHEMA_VERSION == "1.0"


def test_supported_versions_set():
    assert "1.0" in SUPPORTED_SCHEMA_VERSIONS
    assert "1.1" in SUPPORTED_SCHEMA_VERSIONS
    assert "0.9" not in SUPPORTED_SCHEMA_VERSIONS


def test_is_supported_true():
    assert is_supported("1.0") is True
    assert is_supported("1.1") is True


def test_is_supported_false():
    assert is_supported("2.0") is False
    assert is_supported("0.9") is False


def test_is_current_true():
    assert is_current("1.1") is True


def test_is_current_false():
    assert is_current("1.0") is False
    assert is_current("2.0") is False
