# =========================
# 질문형 역질문 생성 코드
# print("역질문") 형식 유지 버전
# =========================

FOLLOWUP_PROMPT = """
너는 사용자의 오늘 놀이 선택을 도와주는 추천 도우미다.

사용자는 보드게임, 방탈출, 머더미스터리 중 하나를 하고 싶어 한다.
너의 역할은 선택지를 나열하는 것이 아니라,
사용자가 원하는 방향을 더 잘 찾을 수 있도록 자연스러운 질문을 던지는 것이다.

규칙:
1. 모든 문장은 반드시 질문형으로 끝낸다.
2. 번호 목록으로 출력하지 않는다.
3. 점수, RRF, 랭킹, 내부 계산 과정은 말하지 않는다.
4. 너무 기계적으로 묻지 말고 실제 사람이 추천 전에 물어보는 느낌으로 작성한다.
5. 질문은 최대 3개만 출력한다.
"""


# =========================
# 역질문 생성 함수
# =========================

def generate_question_style_followups(
    query,
    category,
    group=None,
    top_result=None,
    max_questions=3
):
    if group is None:
        group = {}

    questions = []

    headcount = group.get("headcount")
    play_time = group.get("play_time")
    relation = group.get("relation")
    horror_tolerance = group.get("horror_tolerance")
    weight_pref = group.get("weight_pref")

    # =========================
    # 공통 질문
    # =========================

    if not headcount and not any(k in query for k in ["명", "인"]):
        questions.append(
            "몇 명이서 함께하실 예정인가요?"
        )

    if not relation:
        questions.append(
            "같이 하는 분들은 친구, 연인, 가족, 처음 만나는 사람 중 어디에 가까우신가요?"
        )

    if (
        not play_time
        and not any(k in query for k in [
            "분", "시간", "짧게", "길게"
        ])
    ):
        questions.append(
            "플레이 시간은 짧고 가볍게 즐기는 쪽이 좋으신가요, 아니면 오래 몰입하는 쪽이 좋으신가요?"
        )

    # =========================
    # 보드게임 질문
    # =========================

    if category == "boardgame":

        if not any(k in query for k in [
            "파티", "전략", "협력",
            "추리", "가족"
        ]):
            questions.append(
                "다 같이 웃고 떠들 수 있는 분위기가 좋으신가요, 아니면 머리 쓰면서 진득하게 하는 게임이 좋으신가요?"
            )

        if not weight_pref:
            questions.append(
                "룰이 쉽고 바로 시작할 수 있는 게임이 좋으신가요, 아니면 배우는 재미가 있는 게임도 괜찮으신가요?"
            )

    # =========================
    # 방탈출 질문
    # =========================

    elif category == "escape":

        if (
            horror_tolerance is None
            and not any(k in query for k in [
                "공포", "무서운",
                "안 무서운", "호러"
            ])
        ):
            questions.append(
                "공포가 있는 테마도 괜찮으신가요, 아니면 무섭지 않은 테마를 찾고 계신가요?"
            )

        if not any(k in query for k in [
            "스토리", "장치",
            "연출", "퍼즐"
        ]):
            questions.append(
                "문제를 푸는 재미가 더 중요하신가요, 아니면 스토리와 연출, 몰입감이 더 중요하신가요?"
            )

        if not any(k in query for k in [
            "서울", "강남", "홍대",
            "건대", "부천", "인천"
        ]):
            questions.append(
                "이동 가능한 지역은 어디까지 생각하고 계신가요?"
            )

    # =========================
    # 머더미스터리 질문
    # =========================

    elif category in ["murder", "murdermystery"]:

        if not any(k in query for k in [
            "추리", "스토리",
            "RP", "롤플레잉", "몰입"
        ]):
            questions.append(
                "추리 중심으로 범인을 찾는 느낌이 좋으신가요, 아니면 역할에 몰입해서 스토리를 즐기는 느낌이 좋으신가요?"
            )

        if not any(k in query for k in [
            "입문", "처음", "초보"
        ]):
            questions.append(
                "처음 하는 분들도 함께하시나요, 아니면 다들 익숙한 멤버들이신가요?"
            )

    # =========================
    # 추천 결과 기반 질문
    # =========================

    if top_result and len(questions) < max_questions:
        title = top_result.get("title", "추천작")

        questions.append(
            f"현재 추천된 '{title}' 같은 분위기가 괜찮으신가요, 아니면 다른 느낌을 원하시나요?"
        )

    # =========================
    # 중복 제거
    # =========================

    final_questions = []
    seen = set()

    for q in questions:
        if q not in seen:
            final_questions.append(q)
            seen.add(q)

    return final_questions[:max_questions]


# =========================
# 출력 함수
# =========================

def print_question_style_followups(
    query,
    category,
    results=None,
    group=None,
    max_questions=3
):
    if results is None:
        results = []

    top_result = results[0] if results else None

    questions = generate_question_style_followups(
        query=query,
        category=category,
        group=group,
        top_result=top_result,
        max_questions=max_questions
    )

    print("\n==============================")
    print("역질문")
    print("==============================")

    for question in questions:
        print(question)


# =========================
# 테스트 실행부
# =========================

if __name__ == "__main__":

    query = "오늘은 방탈출 하고 싶어"
    category = "escape"

    results = [
        {
            "title": "세인트 블랙"
        }
    ]

    group = {
        "headcount": None,
        "play_time": None,
        "relation": None,
        "horror_tolerance": None,
        "weight_pref": None,
    }

    print(FOLLOWUP_PROMPT)

    print_question_style_followups(
        query=query,
        category=category,
        results=results,
        group=group,
        max_questions=3
    )