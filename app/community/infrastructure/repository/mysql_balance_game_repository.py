from sqlalchemy.orm import Session

from app.community.application.port.balance_game_repository_port import BalanceGameRepositoryPort
from app.community.domain.balance_game import BalanceGame
from app.community.infrastructure.model.balance_game_model import BalanceGameModel


class MySQLBalanceGameRepository(BalanceGameRepositoryPort):
    """MySQL 기반 밸런스 게임 저장소"""

    def __init__(self, db_session: Session):
        self._db = db_session

    def save(self, game: BalanceGame) -> None:
        """밸런스 게임을 저장한다 (insert 또는 update)"""
        game_model = BalanceGameModel(
            id=game.id,
            question=game.question,
            option_left=game.option_left,
            option_right=game.option_right,
            week_of=game.week_of,
            is_active=game.is_active,
            created_at=game.created_at,
        )
        self._db.merge(game_model)
        self._db.commit()

    def find_by_id(self, game_id: str) -> BalanceGame | None:
        """id로 밸런스 게임을 조회한다"""
        game_model = self._db.query(BalanceGameModel).filter(
            BalanceGameModel.id == game_id
        ).first()

        if game_model is None:
            return None

        return self._to_domain(game_model)

    def find_current_active(self) -> BalanceGame | None:
        """현재 활성화된 밸런스 게임을 조회한다"""
        game_model = self._db.query(BalanceGameModel).filter(
            BalanceGameModel.is_active == True
        ).order_by(BalanceGameModel.created_at.desc()).first()

        if game_model is None:
            return None

        return self._to_domain(game_model)

    def find_all(self) -> list[BalanceGame]:
        """모든 밸런스 게임을 조회한다 (최신순 정렬)"""
        game_models = self._db.query(BalanceGameModel).order_by(
            BalanceGameModel.created_at.desc()
        ).all()

        return [self._to_domain(model) for model in game_models]

    def _to_domain(self, model: BalanceGameModel) -> BalanceGame:
        """ORM 모델을 도메인 객체로 변환한다"""
        return BalanceGame(
            id=model.id,
            question=model.question,
            option_left=model.option_left,
            option_right=model.option_right,
            week_of=model.week_of,
            is_active=model.is_active,
            created_at=model.created_at,
        )