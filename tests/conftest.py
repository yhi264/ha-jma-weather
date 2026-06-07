"""Pytest fixtures for jma_weather tests."""
import pathlib
import sys

import pytest

# custom_components/ を import パスに追加
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

pytest_plugins = ["pytest_homeassistant_custom_component"]


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """全テストでカスタム統合を有効化。"""
    yield
