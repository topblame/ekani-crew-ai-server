from typing import List, Dict, Set
from app.shared.vo.mbti import MBTI


class MBTICompatibility:
    # 전체 MBTI 목록
    ALL_MBTI = [
        "INFP", "ENFP", "INFJ", "ENFJ", "INTJ", "ENTJ", "INTP", "ENTP",
        "ISFP", "ESFP", "ISTP", "ESTP", "ISFJ", "ESFJ", "ISTJ", "ESTJ"
    ]

    # Level 1: 천생연분 (Pink Hearts)
    _BEST_MATCH: Dict[str, List[str]] = {
        "INFP": ["ENFJ", "ENTJ"], "ENFP": ["INFJ", "INTJ"],
        "INFJ": ["ENFP", "ENTP"], "ENFJ": ["INFP", "ISFP"],
        "INTJ": ["ENFP", "ENTP"], "ENTJ": ["INFP", "INTP"],
        "INTP": ["ENTJ", "ESTJ"], "ENTP": ["INFJ", "INTJ"],
        "ISFP": ["ENFJ", "ESFJ"], "ESFP": ["ISFJ", "ISTJ"],
        "ISTP": ["ESFJ", "ESTJ"], "ESTP": ["ISFJ", "ISTJ"],
        "ISFJ": ["ESFP", "ESTP"], "ESFJ": ["ISFP", "ISTP"],
        "ISTJ": ["ESFP", "ESTP"], "ESTJ": ["INTP", "ISTP"],
    }

    # Level 3용 그룹 정의 (NT <-> S)
    _AVERAGE_GROUP = {
        "NT": ["INTJ", "ENTJ", "INTP", "ENTP"],
        "S": ["ISFP", "ESFP", "ISTP", "ESTP", "ISFJ", "ESFJ", "ISTJ", "ESTJ"]
    }

    # Level 4용(Bad) 그룹 정의 (NF <-> S)
    _BAD_GROUP = {
        "NF": ["INFP", "ENFP", "INFJ", "ENFJ"],
        "S": ["ISFP", "ESFP", "ISTP", "ESTP", "ISFJ", "ESFJ", "ISTJ", "ESTJ"]
    }

    @classmethod
    def get_targets(cls, my_mbti: str, level: int = 1) -> List[MBTI]:
        target_set: Set[str] = set()

        # Level 1: 천생연분
        if level >= 1:
            target_set.update(cls._BEST_MATCH.get(my_mbti, []))

        # Level 2: 좋은 관계 (전체 - (천생연분 + 무난 + 최악))
        if level >= 2:
            all_others = set(cls.ALL_MBTI)
            bad_and_avg = cls._get_bad_and_average(my_mbti)
            best = set(cls._BEST_MATCH.get(my_mbti, []))
            target_set.update(all_others - bad_and_avg - best)

        # Level 3: 무난한 관계
        if level >= 3:
            target_set.update(cls._get_average_only(my_mbti))

        # Level 4: 전체 (최악 포함)
        if level >= 4:
            return [MBTI(m) for m in cls.ALL_MBTI]

        return [MBTI(m) for m in list(target_set)]

    @classmethod
    def _get_average_only(cls, mbti: str) -> Set[str]:
        if mbti in cls._AVERAGE_GROUP["NT"]: return set(cls._AVERAGE_GROUP["S"])
        if mbti in cls._AVERAGE_GROUP["S"]: return set(cls._AVERAGE_GROUP["NT"])
        return set()

    @classmethod
    def _get_bad_and_average(cls, mbti: str) -> Set[str]:
        bad_set = set()
        if mbti in cls._BAD_GROUP["NF"]:
            bad_set.update(cls._BAD_GROUP["S"])
            if mbti == "ENFJ" and "ISFP" in bad_set: bad_set.remove("ISFP")
        elif mbti in cls._BAD_GROUP["S"]:
            bad_set.update(cls._BAD_GROUP["NF"])
            if mbti == "ISFP" and "ENFJ" in bad_set: bad_set.remove("ENFJ")

        return bad_set.union(cls._get_average_only(mbti))