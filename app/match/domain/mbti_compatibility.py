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
        all_mbtis = set(cls.ALL_MBTI)
        best_matches = set(cls._BEST_MATCH.get(my_mbti, []))
        bad_and_avg_matches = cls._get_bad_and_average(my_mbti)

        # Level 2 (좋은 관계)는 전체에서 최악, 무난, 천생연분을 제외한 나머지
        good_matches = all_mbtis - best_matches - bad_and_avg_matches
        
        # Level 3 (무난한 관계)
        average_matches = cls._get_average_only(my_mbti)

        target_set: Set[str] = set()
        if level == 1:
            target_set.update(best_matches)
        elif level == 2:
            target_set.update(best_matches)
            target_set.update(good_matches)
        elif level == 3:
            target_set.update(best_matches)
            target_set.update(good_matches)
            target_set.update(average_matches)
        elif level >= 4:
            target_set.update(all_mbtis)

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