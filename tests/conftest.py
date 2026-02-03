"""pytest 配置"""

import pytest


def pytest_configure(config):
    """註冊自定義 marker"""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
