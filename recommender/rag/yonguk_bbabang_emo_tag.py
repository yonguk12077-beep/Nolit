# =========================
# 감정 태그 (Sentiment Tag)
# =========================

# 긍정 태그 → 가산점
POSITIVE_TAGS = {
    "꽃길": 0.04,
    "풀꽃길": 0.05,
    "재밌": 0.03,
    "존잼": 0.04,
    "꿀잼": 0.04,
    "만족": 0.03,
    "추천": 0.03,
    "강추": 0.04,
    "입문용": 0.02,
    "인테리어 좋": 0.03,
    "스토리 좋": 0.03,
    "연출 좋": 0.03,
    "장치 좋": 0.02,
    "몰입": 0.03,
}

# 부정 태그 → 감점
NEGATIVE_TAGS = {
    "아쉽": -0.03,
    "별로": -0.04,
    "비추": -0.05,
    "실망": -0.04,
    "불친절": -0.04,
    "노후": -0.03,
    "장치 오류": -0.04,
    "오류": -0.03,
    "고장": -0.03,
    "불쾌": -0.04,
    "최악": -0.06,
}


def sentiment_tag_bonus(review_item):
    """
    리뷰 텍스트(document)에서
    긍정/부정 감정 태그를 추출하여
    보너스 점수를 계산

    return:
        bonus (float)
        matched_positive (list)
        matched_negative (list)
    """

    text = str(review_item.get("document", ""))

    bonus = 0.0
    matched_positive = []
    matched_negative = []

    # 긍정 태그 탐색
    for tag, weight in POSITIVE_TAGS.items():
        if tag in text:
            bonus += weight
            matched_positive.append(tag)

    # 부정 태그 탐색
    for tag, weight in NEGATIVE_TAGS.items():
        if tag in text:
            bonus += weight
            matched_negative.append(tag)

    # 점수가 너무 커지는 것 방지
    # 최대 +0.15 / 최소 -0.15 제한
    bonus = max(min(bonus, 0.15), -0.15)

    return bonus, matched_positive, matched_negative


# =========================
# 테스트 예시
# =========================

review_item = {
    "title": "경성",
    "store_name": "셜록홈즈 원주점",
    "document": """
    진짜 꽃길이었습니다.
    스토리도 너무 좋고 몰입감 최고.
    연출 좋고 인테리어도 만족스러웠어요.
    완전 추천합니다.
    """
}

bonus, pos_tags, neg_tags = sentiment_tag_bonus(review_item)

print("===== 감정 태그 분석 결과 =====")
print("테마명:", review_item["title"])
print("매장명:", review_item["store_name"])
print("긍정 태그:", pos_tags)
print("부정 태그:", neg_tags)
print("감정 태그 점수:", bonus)