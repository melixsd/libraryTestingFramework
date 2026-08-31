"""Shared pytest configuration for the Library Management test suite."""
import pytest


def pytest_collection_modifyitems(config, items):
    """Auto-mark tests based on their directory."""
    for item in items:
        path = str(item.fspath).replace("\\", "/")
        if "/unit/" in path:
            item.add_marker(pytest.mark.unit)
        elif "/integration/" in path:
            item.add_marker(pytest.mark.integration)
        elif "/e2e/" in path:
            item.add_marker(pytest.mark.e2e)
            item.add_marker(pytest.mark.selenium)
