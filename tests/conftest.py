"""Pytest configuration for loop-engineering."""

import pytest


@pytest.fixture
def sample_config():
    """Sample configuration for testing."""
    return {
        "model": "gpt-4o-mini",
        "temperature": 0.3,
        "max_tokens": 1000,
    }
