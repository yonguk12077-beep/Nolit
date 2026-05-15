# =========================
# 추천 이유 + 역질문 생성
# =========================

def generate_recommend_reason(review_item, stats_item, score_info):
    reasons = []

    title = review_item.get("title")
    store = review_item.get("store_name")

    rrf_score = score_info.get("rrf_score", 0)
    first_bonus = score_info.get("first_bonus", 0)
    second_bonus = score_info.get("second_bonus", 0)
    sentiment_bonus = score_info.get("sentiment_bonus", 0)
    pos_tags = score_info.get("pos_tags", [])
    neg_tags = score_info.get("neg_tags", [])

    # 지역 조건
    if stats_item.get("location"):
        reasons.append(
            f"{stats_item.get('location')} 지역 조건에 부합합니다."
        )

    # 만족도
    if stats_item.get("satisfaction") is not None:
        reasons.append(
            f"만족도 점수가 {stats_item.get('satisfaction')}점으로 비교적 높습니다."
        )

    # 스토리
    if stats_item.get("story") is not None:
        if stats_item.get("story") >= 3.0:
            reasons.append(
                "스토리 평가가 좋아 몰입감 있는 테마로 볼 수 있습니다."
            )

    # 퍼즐
    if stats_item.get("puzzle") is not None:
        if stats_item.get("puzzle") >= 3.0:
            reasons.append(
                "문제 구성 점수가 높아 퍼즐 풀이를 중요하게 보는 사용자에게 적합합니다."
            )

    # 인테리어
    if stats_item.get("interior") is not None:
        if stats_item.get("interior") >= 3.0:
            reasons.append(
                "인테리어 평가가 좋아 공간 몰입도가 기대됩니다."
            )

    # 연출
    if stats_item.get("production") is not None:
        if stats_item.get("production") >= 3.0:
            reasons.append(
                "연출 평가가 좋아 체험 완성도가 높은 편입니다."
            )

    # 공포도
    if stats_item.get("horror") is not None:
        horror = stats_item.get("horror")

        if horror <= 1.0:
            reasons.append(
                "공포도가 낮아 입문자도 부담 없이 즐길 수 있습니다."
            )

        elif horror >= 3.0:
            reasons.append(
                "공포도가 높은 편이라 무서운 테마를 원하는 사용자에게 적합합니다."
            )

    # 난이도
    if stats_item.get("difficulty") is not None:
        difficulty = stats_item.get("difficulty")

        if difficulty <= 2.5:
            reasons.append(
                "난이도가 낮아 초보자에게 적합합니다."
            )

        elif difficulty >= 3.5:
            reasons.append(
                "난이도가 높은 편이라 숙련자에게 적합합니다."
            )

    # 긍정 감정 태그
    if pos_tags:
        reasons.append(
            f"리뷰에서 긍정 태그({', '.join(pos_tags[:3])})가 확인되었습니다."
        )

    # 부정 감정 태그
    if neg_tags:
        reasons.append(
            f"다만 부정 태그({', '.join(neg_tags[:3])})도 일부 확인되었습니다."
        )

    # 최종 추천 이유
    reasons.append(
        f"검색 점수(RRF {rrf_score:.4f})에 "
        f"1차 가중치({first_bonus:.4f}), "
        f"2차 가중치({second_bonus:.4f}), "
        f"감정태그 보정({sentiment_bonus:.4f})을 반영해 "
        f"최종 추천되었습니다."
    )

    return f"{title} ({store}) 추천 이유:\n" + "\n".join(reasons)


def generate_followup_question(filters, prefs):
    questions = []

    # 인원
    if "max_players" not in filters:
        questions.append(
            "몇 명이서 플레이하실 예정인가요?"
        )

    # 예산
    if "price" not in filters:
        questions.append(
            "1인당 예산은 어느 정도로 생각하시나요?"
        )

    # 공포도
    if "horror" not in prefs:
        questions.append(
            "공포도는 낮은 쪽이 좋으신가요, 무서운 테마도 괜찮으신가요?"
        )

    # 난이도
    if "difficulty" not in prefs:
        questions.append(
            "난이도는 쉬운 입문용이 좋으신가요, 어려운 문제 위주가 좋으신가요?"
        )

    # 중요 요소
    if not any(
        prefs.get(k)
        for k in ["story", "puzzle", "interior", "production"]
    ):
        questions.append(
            "스토리, 퍼즐, 인테리어, 연출 중 어떤 요소를 가장 중요하게 보시나요?"
        )

    # 방탈출 경험 여부
    questions.append(
        "방탈출 경험이 많으신 편인가요, 아니면 처음이신가요?"
    )

    # 활동량 선호
    questions.append(
        "활동량이 많은 테마를 선호하시나요, 아니면 이동이 적은 테마가 좋으신가요?"
    )

    # 장르 선호
    questions.append(
        "추리, 공포, 감성, 코믹, 스릴러 중 선호하는 장르가 있으신가요?"
    )

    # 데이트 / 친구 / 단체
    questions.append(
        "데이트용으로 찾으시나요, 친구들과 함께 즐길 테마를 찾으시나요?"
    )

    # 실패 허용 여부
    questions.append(
        "탈출 실패를 감수하고라도 어려운 테마를 선호하시나요?"
    )

    # 장치 vs 문제
    questions.append(
        "화려한 장치와 연출이 중요한가요, 아니면 문제 퀄리티가 더 중요한가요?"
    )

    # 인기 vs 숨은 명작
    questions.append(
        "평점이 높은 인기 테마를 우선 보시나요, 아니면 숨은 명작도 괜찮으신가요?"
    )

    if not questions:
        return (
            "추가로 선호하는 테마 분위기나 "
            "피하고 싶은 요소가 있으신가요?"
        )

    return (
        "더 정확한 추천을 위해:\n"
        + "\n".join(questions[:4])
    )


# =========================
# 테스트용 데이터
# =========================

score_info = {
    "rrf_score": 0.0164,
    "first_bonus": 0.2196,
    "second_bonus": 0.1162,
    "sentiment_bonus": 0.0800,
    "pos_tags": ["꽃길", "추천", "몰입"],
    "neg_tags": []
}

review_item = {
    "title": "경성",
    "store_name": "셜록홈즈 원주점",
    "document": """
    진짜 꽃길이었습니다.
    스토리도 좋고 몰입감이 좋았습니다.
    완전 추천합니다.
    """
}

stats_item = {
    "location": "원주시",
    "satisfaction": 3.66,
    "story": 3.8,
    "puzzle": 3.4,
    "interior": 3.2,
    "production": 3.5,
    "horror": 0.36,
    "difficulty": 3.59
}

filters = {
    "location": "원주시"
}

prefs = {
    "story": True,
    "satisfaction": True,
    "horror": "low"
}


# =========================
# 실행
# =========================

reason = generate_recommend_reason(
    review_item=review_item,
    stats_item=stats_item,
    score_info=score_info
)

followup = generate_followup_question(
    filters=filters,
    prefs=prefs
)

print("\n[추천 이유]")
print(reason)

print("\n[역질문]")
print(followup)