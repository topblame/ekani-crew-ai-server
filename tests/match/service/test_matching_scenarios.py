import pytest
from app.shared.vo.mbti import MBTI
from app.match.domain.match_ticket import MatchTicket
from app.match.application.service.match_service import MatchService
from tests.match.fixtures.fake_match_queue_adapter import FakeMatchQueueAdapter


@pytest.mark.asyncio
async def test_match_expansion_level_logic():
    """
    [시나리오 1: 단계별 탐색 확장 테스트]
    상황: INFP의 천생연분(ENFJ)은 없고, 좋은 관계(INTP)만 대기 중.

    1. Level 1(천생연분) 요청 -> 매칭 실패 (None)
    2. Level 2(좋은 관계) 요청 -> 매칭 성공 (INTP)
    """
    # Given
    fake_queue = FakeMatchQueueAdapter()
    service = MatchService(match_queue_port=fake_queue)

    # INTP 유저 등록 (INFP 입장에서는 Level 2 '좋은 관계' 파트너)
    good_partner_ticket = MatchTicket("partner_intp", MBTI("INTP"))
    await fake_queue.enqueue(good_partner_ticket)

    me = MatchTicket("me_infp", MBTI("INFP"))

    # When 1: Level 1 요청
    result_lvl_1 = await service.find_partner(me, level=1)

    # Then 1: 천생연분이 아니므로 매칭되지 않아야 함
    assert result_lvl_1 is None

    # When 2: Level 2 요청
    result_lvl_2 = await service.find_partner(me, level=2)

    # Then 2: 매칭 성공
    assert result_lvl_2 is not None
    assert result_lvl_2.user_id == "partner_intp"
    assert result_lvl_2.mbti.value == "INTP"


@pytest.mark.asyncio
async def test_match_worst_case_at_level_4():
    """
    [시나리오 2: 최악의 궁합 매칭 테스트]
    상황: INFP의 최악의 궁합인 ISTJ만 대기 중.

    1. Level 1~3 요청 -> 매칭 실패
    2. Level 4(전체) 요청 -> 매칭 성공
    """
    # Given
    fake_queue = FakeMatchQueueAdapter()
    service = MatchService(match_queue_port=fake_queue)

    # ISTJ 유저 등록 (INFP와는 빨간색/최악 관계)
    istj_ticket = MatchTicket("partner_istj", MBTI("ISTJ"))
    await fake_queue.enqueue(istj_ticket)

    me = MatchTicket("me_infp", MBTI("INFP"))

    # When & Then
    assert await service.find_partner(me, level=1) is None
    assert await service.find_partner(me, level=2) is None
    assert await service.find_partner(me, level=3) is None

    # Level 4에서는 아무나 매칭
    match = await service.find_partner(me, level=4)
    assert match is not None
    assert match.user_id == "partner_istj"


@pytest.mark.asyncio
async def test_skip_cancelled_ghost_user():
    """
    [시나리오 3: 유령 티켓(취소된 유저) 건너뛰기]
    상황:
    1. 유저 A(ENFJ)가 대기열 등록 후 취소함 (List에는 남지만 Set에서는 삭제된 상태 가정)
    2. 유저 B(ENFJ)가 대기열 등록 (정상 대기)
    3. INFP가 매칭 요청 시, 취소된 유저 A를 건너뛰고 B와 매칭되어야 함.
    """
    # Given
    fake_queue = FakeMatchQueueAdapter()
    service = MatchService(match_queue_port=fake_queue)

    # 파트너 A (등록 후 취소)
    user_a = MatchTicket("ghost_user", MBTI("ENFJ"))
    await fake_queue.enqueue(user_a)
    await fake_queue.remove(user_a.user_id, user_a.mbti)  # 취소 처리

    # 파트너 B (정상 대기)
    user_b = MatchTicket("real_user", MBTI("ENFJ"))
    await fake_queue.enqueue(user_b)

    # When: INFP 입장
    me = MatchTicket("me_infp", MBTI("INFP"))
    match = await service.find_partner(me, level=1)

    # Then: 취소한 ghost_user가 아니라 real_user와 매칭되어야 함
    assert match is not None
    assert match.user_id == "real_user"

    # 큐 사이즈 검증 (둘 다 처리되었으므로 0이어야 함)
    # Ghost는 dequeue 시점에 버려지고, Real은 매칭되어 나감
    # (참고: FakeAdapter 구현 방식에 따라 remove시 아예 리스트에서 빠질 수도 있지만,
    #  Redis 로직상 '취소된 유저는 매칭되지 않는다'는 결과는 동일해야 함)
    assert await fake_queue.get_queue_size(MBTI("ENFJ")) == 0


@pytest.mark.asyncio
async def test_complex_load_balancing():
    """
    [시나리오 4: 복합 우선순위 (레벨 vs 인원수)]
    상황:
    - Target A (Level 1, Best): 대기자 1명
    - Target B (Level 1, Best): 대기자 100명

    기대: 같은 Level 1이라면 대기자가 많은 Target B와 먼저 매칭되어야 함.
    """
    # Given
    fake_queue = FakeMatchQueueAdapter()
    service = MatchService(match_queue_port=fake_queue)

    # INFP 기준 Best Match: ENFJ, ENTJ

    # ENFJ: 1명 대기
    await fake_queue.enqueue(MatchTicket("enfj_solo", MBTI("ENFJ")))

    # ENTJ: 3명 대기 (더 많음)
    await fake_queue.enqueue(MatchTicket("entj_1", MBTI("ENTJ")))
    await fake_queue.enqueue(MatchTicket("entj_2", MBTI("ENTJ")))
    await fake_queue.enqueue(MatchTicket("entj_3", MBTI("ENTJ")))

    # When
    me = MatchTicket("me_infp", MBTI("INFP"))
    match = await service.find_partner(me, level=1)

    # Then: 사람이 많은 ENTJ 그룹에서 먼저 매칭되어야 함
    assert match is not None
    assert match.mbti.value == "ENTJ"


@pytest.mark.asyncio
async def test_match_specific_exception_rule():
    """
    [시나리오 5: 궁합표 예외 규칙 검증]
    일반적으로 NF(감성)와 S(현실)는 '최악(Level 4)'이지만,
    'ENFJ'와 'ISFP'는 예외적으로 '천생연분(Level 1)'이다.

    이 예외 규칙이 제대로 적용되어 Level 1에서 매칭되는지 확인한다.
    """
    # Given
    fake_queue = FakeMatchQueueAdapter()
    service = MatchService(match_queue_port=fake_queue)

    # ISFP 대기 등록
    await fake_queue.enqueue(MatchTicket("isfp_user", MBTI("ISFP")))

    # When: ENFJ 입장 (Level 1 요청)
    me = MatchTicket("me_enfj", MBTI("ENFJ"))
    match = await service.find_partner(me, level=1)

    # Then: Level 1에서 매칭 성공해야 함
    assert match is not None
    assert match.mbti.value == "ISFP"


@pytest.mark.asyncio
async def test_match_same_mbti_logic():
    """
    [시나리오 6: 동일 MBTI 매칭 검증]
    INFP끼리는 '좋은 관계(Level 2)'이다.
    Level 1에서는 실패하고, Level 2에서는 성공해야 한다.
    """
    # Given
    fake_queue = FakeMatchQueueAdapter()
    service = MatchService(match_queue_port=fake_queue)

    # 다른 INFP 대기 중
    await fake_queue.enqueue(MatchTicket("other_infp", MBTI("INFP")))

    me = MatchTicket("me_infp", MBTI("INFP"))

    # When & Then
    # Level 1 (천생연분) -> 실패
    assert await service.find_partner(me, level=1) is None

    # Level 2 (좋은 관계) -> 성공
    match = await service.find_partner(me, level=2)
    assert match is not None
    assert match.user_id == "other_infp"


@pytest.mark.asyncio
async def test_load_balancing_across_tiers():
    """
    [시나리오 7: 티어 간 로드 밸런싱 (중요!)]
    상황: Level 2(Best + Good) 요청 시,
    - Best Match (ENFJ): 1명 대기
    - Good Match (INTP): 100명 대기

    우리의 로직(내림차순 정렬)에 따르면,
    궁합이 'Best'라도 대기자가 많은 'Good' 쪽(INTP)을 먼저 구출해야 한다.
    (시스템 전체 혼잡도 해소 우선 정책)
    """
    # Given
    fake_queue = FakeMatchQueueAdapter()
    service = MatchService(match_queue_port=fake_queue)

    # Best Match (ENFJ): 1명
    await fake_queue.enqueue(MatchTicket("best_enfj", MBTI("ENFJ")))

    # Good Match (INTP): 2명 (Best보다 많음)
    await fake_queue.enqueue(MatchTicket("good_intp_1", MBTI("INTP")))
    await fake_queue.enqueue(MatchTicket("good_intp_2", MBTI("INTP")))

    me = MatchTicket("me_infp", MBTI("INFP"))

    # When: Level 2 요청 (Best와 Good 모두 포함됨)
    match = await service.find_partner(me, level=2)

    # Then: 사람이 더 많은 INTP(Good)와 매칭되어야 함
    assert match is not None
    assert match.mbti.value == "INTP"


@pytest.mark.asyncio
async def test_queue_depletion_sequential_match():
    """
    [시나리오 8: 대기열 고갈 테스트]
    대기자가 2명일 때, 3번 연속 매칭 요청 시
    1번 성공 -> 2번 성공 -> 3번 실패(None) 확인
    """
    # Given
    fake_queue = FakeMatchQueueAdapter()
    service = MatchService(match_queue_port=fake_queue)

    # ENFJ 2명 대기
    await fake_queue.enqueue(MatchTicket("enfj_1", MBTI("ENFJ")))
    await fake_queue.enqueue(MatchTicket("enfj_2", MBTI("ENFJ")))

    me = MatchTicket("me_infp", MBTI("INFP"))

    # 1번째 시도
    match1 = await service.find_partner(me, level=1)
    assert match1.user_id == "enfj_1"

    # 2번째 시도
    match2 = await service.find_partner(me, level=1)
    assert match2.user_id == "enfj_2"

    # 3번째 시도 (대기열 빔)
    match3 = await service.find_partner(me, level=1)
    assert match3 is None


@pytest.mark.asyncio
async def test_level_3_average_match():
    """
    [시나리오 9: 무난한 관계 (Level 3) 검증]
    NT(분석가형)와 S(탐험가/관리자형)는 서로 무난한 관계(Yellow)이다.
    ENTJ(NT) <-> ISTJ(S) 케이스 테스트.
    """
    # Given
    fake_queue = FakeMatchQueueAdapter()
    service = MatchService(match_queue_port=fake_queue)

    # ISTJ 대기 (ENTJ 입장에서 Level 3)
    await fake_queue.enqueue(MatchTicket("istj_user", MBTI("ISTJ")))

    me = MatchTicket("me_entj", MBTI("ENTJ"))

    # When & Then
    # Level 2까지는 매칭 안됨
    assert await service.find_partner(me, level=2) is None

    # Level 3에서 매칭 성공
    match = await service.find_partner(me, level=3)
    assert match is not None
    assert match.mbti.value == "ISTJ"