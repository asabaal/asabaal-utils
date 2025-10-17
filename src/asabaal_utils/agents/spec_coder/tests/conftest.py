"""
Pytest configuration for spec_coder tests.

This file defines custom markers and configuration for running different types of tests.
"""

import pytest


def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests that require real AI models"
    )
    config.addinivalue_line(
        "markers", "slow: marks tests as slow-running tests"
    )
    config.addinivalue_line(
        "markers", "requires_ollama: marks tests that require Ollama to be running"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on test names."""
    for item in items:
        # Add integration marker to integration tests
        if "integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)
            item.add_marker(pytest.mark.slow)
            item.add_marker(pytest.mark.requires_ollama)
        
        # Add slow marker to known slow tests
        if "test_generate_from_spec" in item.nodeid:
            item.add_marker(pytest.mark.slow)