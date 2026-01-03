from app.community.application.port.balance_game_repository_port import BalanceGameRepositoryPort
from app.community.domain.balance_game import BalanceGame


class FakeBalanceGameRepository(BalanceGameRepositoryPort):
    """테스트용 Fake 밸런스 게임 저장소"""

    def __init__(self):
        self._games: dict[str, BalanceGame] = {}

    def save(self, game: BalanceGame) -> None:
        self._games[game.id] = game

    def find_by_id(self, game_id: str) -> BalanceGame | None:
        return self._games.get(game_id)

    def find_current_active(self) -> BalanceGame | None:
        for game in self._games.values():
            if game.is_active:
                return game
        return None

    def find_all(self) -> list[BalanceGame]:
        games = list(self._games.values())
        return sorted(games, key=lambda g: g.created_at, reverse=True)
