from abc import ABC, abstractmethod

from app.community.domain.balance_game import BalanceGame


class BalanceGameRepositoryPort(ABC):
    """밸런스 게임 저장소 포트 인터페이스"""

    @abstractmethod
    def save(self, game: BalanceGame) -> None:
        """밸런스 게임을 저장한다"""
        pass

    @abstractmethod
    def find_by_id(self, game_id: str) -> BalanceGame | None:
        """id로 밸런스 게임을 조회한다"""
        pass

    @abstractmethod
    def find_current_active(self) -> BalanceGame | None:
        """현재 활성화된 밸런스 게임을 조회한다"""
        pass

    @abstractmethod
    def find_all(self) -> list[BalanceGame]:
        """모든 밸런스 게임을 조회한다 (최신순 정렬)"""
        pass
