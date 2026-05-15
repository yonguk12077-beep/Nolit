from __future__ import annotations
import re


# ==========================================================
# 감정 태그 키워드 통합본
# ==========================================================

TAG_KEYWORDS = {
    # -------------------------
    # 공포 관련
    # -------------------------
    "공포있음": [
        "무서", "무섭", "공포", "호러", "깜짝",
        "점프스케어", "귀신", "유령", "악몽",
        "살인", "시체", "어두", "긴장",
    ],

    "공포없음": [
        "안 무서", "안무서", "무섭지 않",
        "공포 없", "공포없", "호러 없",
        "힐링", "따뜻", "평화", "감성",
    ],

    # -------------------------
    # 난이도 관련
    # -------------------------
    "고난이도": [
        "어렵", "어려", "고난이도",
        "복잡", "막혔", "헤맸",
        "하드", "숙련자", "상급",
    ],

    "입문용": [
        "쉬움", "쉬운", "쉽게",
        "간단", "입문", "초보",
        "입문용", "가볍", "부담없",
        "부담 없이",
    ],

    # -------------------------
    # 분위기 관련
    # -------------------------
    "분위기좋음": [
        "재밌", "재미있", "몰입",
        "추천", "최고", "만족",
        "분위기 좋", "웃음",
    ],

    "분위기별로": [
        "지루", "노잼", "별로",
        "실망", "비추천", "최악",
    ],

    # -------------------------
    # 관계 / 상황
    # -------------------------
    "데이트추천": [
        "데이트", "커플", "연인",
        "둘이서", "2인", "이인",
    ],

    "친목용": [
        "친구", "모임", "회식",
        "단체", "친목", "파티",
    ],

    "처음만나는사이추천": [
        "처음 만나", "첫만남",
        "소개팅", "아이스브레이크",
        "어색",
    ],

    # -------------------------
    # 플레이 성향
    # -------------------------
    "협력": [
        "협력", "같이", "팀플",
    ],

    "대화유도": [
        "대화", "토론", "소통",
        "밀담", "떠들",
    ],

    "가볍게즐길수있음": [
        "가볍", "편하게",
        "부담없", "간단",
    ],

    # -------------------------
    # 리뷰 기반 긍정 태그
    # -------------------------
    "재밌음": [
        "재밌", "재미있"
    ],

    "꿀잼": [
        "꿀잼", "존잼"
    ],

    "만족도높음": [
        "만족", "만족스러"
    ],

    "강추": [
        "강추", "추천"
    ],

    "스토리좋음": [
        "스토리 좋", "스토리도 좋"
    ],

    "연출좋음": [
        "연출 좋", "연출도 좋"
    ],

    "장치좋음": [
        "장치 좋", "장치도 좋"
    ],

    "몰입감좋음": [
        "몰입", "몰입감"
    ],

    "인테리어좋음": [
        "인테리어 좋", "인테리어도 좋"
    ],

    # -------------------------
    # 리뷰 기반 부정 태그
    # -------------------------
    "아쉬움": [
        "아쉽", "아쉬웠"
    ],

    "별로": [
        "별로"
    ],

    "비추천": [
        "비추", "비추천"
    ],

    "실망": [
        "실망"
    ],

    "불친절": [
        "불친절"
    ],

    "노후됨": [
        "노후", "낡았", "오래됨"
    ],

    "장치오류": [
        "장치 오류", "오류"
    ],

    "고장": [
        "고장"
    ],

    "불쾌함": [
        "불쾌"
    ],

    "최악": [
        "최악"
    ],
}


# ==========================================================
# 점수표
# ==========================================================

POSITIVE_TAG_SCORE = {
    "입문용": 3,
    "분위기좋음": 3,
    "친목용": 3,
    "데이트추천": 2,
    "처음만나는사이추천": 3,
    "공포없음": 2,
    "협력": 2,
    "대화유도": 2,
    "가볍게즐길수있음": 2,
    "재밌음": 3,
    "꿀잼": 3,
    "만족도높음": 3,
    "강추": 3,
    "스토리좋음": 3,
    "연출좋음": 3,
    "장치좋음": 2,
    "몰입감좋음": 3,
    "인테리어좋음": 2,
}


NEGATIVE_TAG_SCORE = {
    "고난이도": -2,
    "분위기별로": -3,
    "공포있음": -3,
    "공포높음": -5,
    "아쉬움": -2,
    "별로": -3,
    "비추천": -4,
    "실망": -3,
    "불친절": -4,
    "노후됨": -2,
    "장치오류": -4,
    "고장": -3,
    "불쾌함": -4,
    "최악": -5,
}


# ==========================================================
# 텍스트 추출
# ==========================================================

def extract_text(item: dict) -> str:
    parts = []

    for key in [
        "title",
        "name",
        "description",
        "reviews",
        "review_text",
        "document",
    ]:
        value = item.get(key)

        if isinstance(value, list):
            parts.extend(map(str, value))
        elif value:
            parts.append(str(value))

    return " ".join(parts)


def count_matches(text: str, keywords: list[str]) -> int:
    text = text.lower()
    count = 0

    for keyword in keywords:
        count += len(re.findall(
            re.escape(keyword.lower()),
            text
        ))

    return count


# ==========================================================
# 감정 태깅
# ==========================================================

def tag_item(item: dict) -> list[str]:
    text = extract_text(item)
    tags = []

    for tag, keywords in TAG_KEYWORDS.items():
        if count_matches(text, keywords) >= 1:
            tags.append(tag)

    # 공포 강도 자동 보정
    horror_count = count_matches(
        text,
        TAG_KEYWORDS["공포있음"]
    )

    if horror_count >= 4:
        tags.append("공포높음")

    # 쉬운 게임이면 자동 추가
    if "입문용" in tags and "가볍게즐길수있음" not in tags:
        tags.append("가볍게즐길수있음")

    return list(dict.fromkeys(tags))


# ==========================================================
# 공포 필터
# ==========================================================

def is_horror_blocked(
    item: dict,
    horror_tolerance: int
) -> bool:
    """
    0 = 공포 절대 불가
    1 = 약한 공포 가능
    2 = 공포 허용
    """

    tags = set(item.get("emotion_tags", []))

    if horror_tolerance >= 2:
        return False

    if horror_tolerance == 0:
        return (
            "공포있음" in tags
            or "공포높음" in tags
        )

    if horror_tolerance == 1:
        return "공포높음" in tags

    return False


# ==========================================================
# 감정 태그 필터 + 점수 재계산
# ==========================================================

def filter_and_score(
    items: list[dict],
    emotion_tags: list[str],
    horror_tolerance: int = 2,
    emotion_weight: float = 5.0,
) -> list[dict]:

    result = []

    for item in items:
        item_copy = item.copy()

        item_copy["emotion_tags"] = tag_item(item_copy)

        # 공포 하드 필터
        if is_horror_blocked(
            item_copy,
            horror_tolerance
        ):
            continue

        # 긍정 점수
        positive_score = 0
        for tag in emotion_tags:
            if tag in item_copy["emotion_tags"]:
                positive_score += POSITIVE_TAG_SCORE.get(tag, 1)

        # 부정 점수
        negative_score = 0
        for tag in item_copy["emotion_tags"]:
            negative_score += NEGATIVE_TAG_SCORE.get(tag, 0)

        base_score = (
            item_copy.get("total_score")
            or item_copy.get("final_score")
            or item_copy.get("avg_rating")
            or item_copy.get("rating")
            or 0
        )

        final_score = (
            base_score
            + ((positive_score + negative_score) * emotion_weight)
        )

        item_copy["emotion_match_score"] = positive_score
        item_copy["negative_score"] = negative_score
        item_copy["final_score"] = round(final_score, 2)

        result.append(item_copy)

    result.sort(
        key=lambda x: x["final_score"],
        reverse=True
    )

    return result

# ==========================================================
# 테스트 예시: 실제 체험 리뷰 느낌
# 기본 점수 100 기준, 점수 증감 표시
# ==========================================================

if __name__ == "__main__":
    test_items = [
        {
            "title": "이스케이프룸: 시간의 방",
            "source": "escape",
            "document": """
            스토리도 좋고 연출도 좋아서 몰입감이 좋았습니다.
            장치도 깔끔하게 작동했고 인테리어도 좋아서 만족스러웠어요.
            전체적으로 재밌고 추천할 만한 방탈출이었습니다.
            """,
            "total_score": 100,
        },
        {
            "title": "구두룡 저택의 살인",
            "source": "murdermystery",
            "document": """
            기대하고 갔는데 전체적으로 아쉬웠습니다.
            진행이 어렵고 복잡해서 초반부터 몰입이 잘 안 됐어요.
            스토리도 별로였고 끝나고 나니 실망스러워서 비추천합니다.
            """,
            "total_score": 100,
        },
        {
            "title": "코드네임",
            "source": "boardgame",
            "document": """
            친구들이랑 했는데 룰이 쉬운 입문용 게임이라 부담 없이 즐겼습니다.
            대화가 자연스럽게 많아지고 분위기도 좋아서 친목용으로 좋았어요.
            짧게 즐기기에도 괜찮고 만족스러운 보드게임이었습니다.
            """,
            "total_score": 100,
        },
    ]

    emotion_tags = [
        "재밌음",
        "만족도높음",
        "강추",
        "스토리좋음",
        "연출좋음",
        "장치좋음",
        "몰입감좋음",
        "인테리어좋음",
        "입문용",
        "친목용",
        "대화유도",
        "가볍게즐길수있음",
        "분위기좋음",
    ]

    result = filter_and_score(
        items=test_items,
        emotion_tags=emotion_tags,
        horror_tolerance=2,
        emotion_weight=5.0,
    )

    print("\n감정 태그 기반 점수 변화 테스트\n")

    for item in result:
        base_score = item["total_score"]
        final_score = item["final_score"]
        diff = final_score - base_score

        sign = "+" if diff >= 0 else ""

        print(f"제목: {item['title']} ({item['source']})")
        print(f"리뷰 감정 태그: {item['emotion_tags']}")
        print(f"기본 점수: {base_score}")
        print(f"긍정 태그 점수: {item['emotion_match_score']}")
        print(f"부정 태그 점수: {item['negative_score']}")
        print(f"점수 변화: {sign}{diff}")
        print(f"최종 점수: {final_score}")
        print()