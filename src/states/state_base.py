from abc import ABC, abstractmethod

class GameState(ABC):
    def __init__(self, game):
        self.game = game

    @abstractmethod
    def handle_events(self, events):
        pass

    @abstractmethod
    def update(self):
        pass

    @abstractmethod
    def draw(self, tela):
        pass
