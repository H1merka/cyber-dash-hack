"""
Тесты модуля Emotions — управление настроением агента.
"""

import pytest

from backend.agents.emotions import Emotions


# ── Инициализация ────────────────────────────────────────────────────

class TestEmotionsInit:
    def test_default_mood(self):
        emo = Emotions()
        assert emo.get_mood_value() == 0

    def test_custom_initial_mood(self):
        emo = Emotions(initial_mood=50)
        assert emo.get_mood_value() == 50

    def test_clamp_upper_on_init(self):
        emo = Emotions(initial_mood=200)
        assert emo.get_mood_value() == 100

    def test_clamp_lower_on_init(self):
        emo = Emotions(initial_mood=-150)
        assert emo.get_mood_value() == -100


# ── update ───────────────────────────────────────────────────────────

class TestEmotionsUpdate:
    def test_positive_delta(self):
        emo = Emotions(initial_mood=0)
        emo.update(30)
        assert emo.get_mood_value() == 30

    def test_negative_delta(self):
        emo = Emotions(initial_mood=10)
        emo.update(-25)
        assert emo.get_mood_value() == -15

    def test_clamp_upper(self):
        emo = Emotions(initial_mood=90)
        emo.update(50)
        assert emo.get_mood_value() == 100

    def test_clamp_lower(self):
        emo = Emotions(initial_mood=-80)
        emo.update(-50)
        assert emo.get_mood_value() == -100

    def test_multiple_updates(self):
        emo = Emotions(initial_mood=0)
        emo.update(40)
        emo.update(-10)
        emo.update(5)
        assert emo.get_mood_value() == 35


# ── get_mood_label ───────────────────────────────────────────────────

class TestMoodLabel:
    @pytest.mark.parametrize("value,expected", [
        (-100, "ужасное"),
        (-80, "ужасное"),
        (-61, "ужасное"),
        (-60, "плохое"),
        (-30, "плохое"),
        (-21, "плохое"),
        (-20, "нейтральное"),
        (0, "нейтральное"),
        (19, "нейтральное"),
        (20, "хорошее"),
        (40, "хорошее"),
        (59, "хорошее"),
        (60, "отличное"),
        (80, "отличное"),
        (100, "отличное"),
    ])
    def test_mood_label_boundaries(self, value: int, expected: str):
        emo = Emotions(initial_mood=value)
        assert emo.get_mood_label() == expected
