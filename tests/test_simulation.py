"""
Тесты симуляции — world.py (управление скоростью, загрузка агентов).
"""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock

from backend.simulation.world import set_speed, get_speed, is_running


# ── Скорость симуляции ───────────────────────────────────────────────

class TestSpeed:
    def test_default_speed(self):
        set_speed(1.0)
        assert get_speed() == 1.0

    def test_set_valid_speed(self):
        set_speed(2.5)
        assert get_speed() == 2.5

    def test_clamp_upper(self):
        set_speed(10.0)
        assert get_speed() == 5.0

    def test_clamp_lower(self):
        set_speed(0.1)
        assert get_speed() == 0.5

    def test_initial_not_running(self):
        assert is_running() is False
