class Emotions:
    def __init__(self, initial_mood=0):
        self.mood = max(-100, min(100, initial_mood))  # от -100 до 100

    def update(self, delta):
        """Изменить настроение на delta (может быть отрицательным)"""
        self.mood += delta
        if self.mood > 100:
            self.mood = 100
        elif self.mood < -100:
            self.mood = -100

    def get_mood_label(self):
        if self.mood < -60:
            return "ужасное"
        elif self.mood < -20:
            return "плохое"
        elif self.mood < 20:
            return "нейтральное"
        elif self.mood < 60:
            return "хорошее"
        else:
            return "отличное"

    def get_mood_value(self):
        return self.mood