import json
import re
from pathlib import Path

# =========================
# 자동 파일 탐색
# =========================

BASE_DIR = Path(r"C:\lecture\Nolit")


def find_meta_file(keyword):
    files = list(BASE_DIR.glob("*"))

    for file in files:
        name = file.name.lower()

        if (
            keyword.lower() in name
            and "meta" in name
            and not name.endswith(".index")
        ):
            return file

    print(f"[메타 파일 못 찾음] keyword = {keyword}")
    return None


BOARDGAME_META_PATH = find_meta_file("faiss_bgg_stats")
ESCAPE_META_PATH = find_meta_file("faiss_bbabang_stats")
MURDER_META_PATH = find_meta_file("faiss_murdermysterylog")

print("BOARDGAME_META_PATH:", BOARDGAME_META_PATH)
print("ESCAPE_META_PATH:", ESCAPE_META_PATH)
print("MURDER_META_PATH:", MURDER_META_PATH)


# =========================
# 평가 쿼리
# =========================

EVAL_QUERIES = {
    "보드게임 하나 추천해줘": {
        "category": "boardgame",
        "conditions": {
            "boardgame": 2,
            "popular": 2,
            "fun": 1,
        },
    },

    "재밌는 방탈출 하나 추천해줘": {
        "category": "escape",
        "conditions": {
            "escape": 2,
            "fun": 2,
            "story": 1,
            "device": 1,
        },
    },

    "머더미스터리 하나 추천해줘": {
        "category": "murder",
        "conditions": {
            "murder": 2,
            "mystery": 2,
            "story": 1,
            "immersion": 1,
        },
    },

    "나 요새 그냥 파티게임 하나 해보고 싶어": {
        "category": "boardgame",
        "conditions": {
            "party": 3,
            "many_players": 2,
            "easy": 1,
            "fun": 1,
        },
    },

    "인원 7명 정도 되는데 뭐가 좋을까?": {
        "category": "boardgame",
        "conditions": {
            "player_7": 3,
            "many_players": 2,
            "party": 2,
            "easy": 1,
        },
    },
}


# =========================
# 조건 키워드
# =========================

CONDITION_KEYWORDS = {
    "boardgame": [
        "보드게임", "보드", "게임",
        "board game", "boardgame", "tabletop"
    ],

    "escape": [
        "방탈출", "테마", "탈출",
        "escape room", "escape", "theme"
    ],

    "murder": [
        "머더", "머더미스터리", "미스터리", "추리",
        "murder", "mystery", "detective", "deduction"
    ],

    "party": [
        "파티", "단체", "여럿", "웃긴", "친구", "모임",
        "party", "social", "group", "multiplayer",
        "casual", "family", "friends", "humor"
    ],

    "easy": [
        "쉬운", "쉽", "입문", "초보", "간단",
        "easy", "simple", "beginner",
        "gateway", "light", "casual"
    ],

    "popular": [
        "인기", "추천", "유명", "베스트",
        "popular", "recommended",
        "top rated", "best", "famous", "classic"
    ],

    "many_players": [
        "단체", "여럿", "다인원", "6명", "7명", "8명",
        "6 players", "7 players", "8 players",
        "large group", "multiplayer",
        "group play", "many players"
    ],

    "player_7": [
        "7명", "7인", "최대 7", "최대7",
        "7 players", "supports 7",
        "up to 7", "7 player"
    ],

    "fun": [
        "재밌", "존잼", "꿀잼", "웃긴", "만족",
        "fun", "exciting", "enjoyable",
        "entertaining", "hilarious"
    ],

    "story": [
        "스토리", "서사", "몰입", "연출",
        "story", "narrative",
        "theme", "immersive", "atmosphere"
    ],

    "device": [
        "장치", "인테리어", "연출",
        "device", "mechanism",
        "production", "special effects"
    ],

    "mystery": [
        "추리", "범인", "사건", "미스터리",
        "mystery", "deduction",
        "detective", "crime", "culprit"
    ],

    "immersion": [
        "몰입", "분위기", "역할", "캐릭터",
        "immersion", "immersive",
        "roleplay", "character", "atmosphere"
    ],
}


# =========================
# 파일 로드
# =========================

def load_json(path):
    if path is None:
        return []

    if not path.exists():
        print(f"[파일 없음] {path}")
        return []

    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    except Exception as e:
        print(f"[로드 실패] {path}")
        print(e)
        return []


def get_title(item):
    for key in [
        "title", "name", "game_name", "theme_name",
        "primary_name", "kor_title", "eng_title"
    ]:
        if key in item and item[key]:
            return str(item[key])

    return str(item)


def get_number(item, keys, default=None):
    for key in keys:
        if key in item and item[key] not in [None, ""]:
            try:
                return float(item[key])
            except Exception:
                pass

    return default


def count_keywords(text, keywords):
    return sum(
        1 for keyword in keywords
        if keyword.lower() in text
    )


def extract_player_count(query):
    patterns = [
        r"(\d+)\s*명",
        r"(\d+)\s*인",
        r"인원\s*(\d+)",
    ]

    for pattern in patterns:
        match = re.search(pattern, query)
        if match:
            return int(match.group(1))

    return None


# =========================
# 기본 키워드 점수
# =========================

def simple_keyword_score(query, item):
    text = json.dumps(item, ensure_ascii=False).lower()
    score = 0

    if "보드게임" in query:
        score += 3

    if "방탈출" in query:
        score += count_keywords(
            text,
            CONDITION_KEYWORDS["escape"]
        ) * 3

    if "머더" in query or "머더미스터리" in query:
        score += count_keywords(
            text,
            CONDITION_KEYWORDS["murder"]
        ) * 3

    if "파티" in query:
        score += count_keywords(
            text,
            CONDITION_KEYWORDS["party"]
        ) * 4

    if "재밌" in query or "추천" in query:
        score += count_keywords(
            text,
            CONDITION_KEYWORDS["fun"]
        ) * 2

    return score


# =========================
# 1차 가중치
# 조건 의도 기반 가중치
# =========================

def first_weight_score(query, item, category):
    score = 0
    text = json.dumps(item, ensure_ascii=False).lower()

    min_players = get_number(
        item,
        ["min_players", "minplayers", "min_player", "minimum_players"]
    )

    max_players = get_number(
        item,
        ["max_players", "maxplayers", "max_player", "maximum_players"]
    )

    rating = get_number(
        item,
        [
            "avg_rating",
            "average_rating",
            "rating",
            "satisfaction",
            "bayesaverage",
            "bayes_average"
        ]
    )

    weight = get_number(
        item,
        [
            "weight",
            "average_weight",
            "complexity",
            "avg_weight"
        ]
    )

    difficulty = get_number(
        item,
        ["difficulty"]
    )

    horror = get_number(
        item,
        ["horror"]
    )

    query_player = extract_player_count(query)

    # =========================
    # 공통 하드필터성 인원 보정
    # =========================

    if query_player:
        if min_players and max_players:
            if min_players <= query_player <= max_players:
                score += 20
            else:
                score -= 100

        elif max_players:
            if query_player <= max_players:
                score += 12
            else:
                score -= 100

    # =========================
    # 보드게임
    # =========================

    if category == "boardgame":
        if "파티" in query:
            score += count_keywords(
                text,
                CONDITION_KEYWORDS["party"]
            ) * 8

        if "전략" in query:
            if "strategy" in text or "전략" in text:
                score += 10

        if "협력" in query:
            if "cooperative" in text or "협력" in text:
                score += 10

        if "타일" in query:
            if "tile" in text or "타일" in text:
                score += 10

        if rating:
            score += rating * 2

        if weight:
            if any(k in query for k in [
                "쉬운", "입문", "초보", "간단"
            ]):
                score += max(0, 5 - weight) * 4

            if any(k in query for k in [
                "전략", "어려운", "헤비", "깊은"
            ]):
                score += weight * 4

        recommended_players = str(
            item.get("recommended_players", "")
        )

        best_players = str(
            item.get("best_players", "")
        )

        if query_player:
            if str(query_player) in recommended_players:
                score += 10

            if str(query_player) in best_players:
                score += 12

        source = str(item.get("source", "")).lower()

        if source == "boardlife":
            score *= 1.5

    # =========================
    # 방탈출
    # =========================

    elif category == "escape":
        if horror is not None:
            if any(k in query for k in [
                "안 무서운",
                "공포 없음",
                "무섭지 않은"
            ]):
                score += max(0, 5 - horror) * 5

            if any(k in query for k in [
                "무서운",
                "공포",
                "호러"
            ]):
                score += horror * 5

        if difficulty is not None:
            if any(k in query for k in [
                "쉬운",
                "입문",
                "초보"
            ]):
                score += max(0, 5 - difficulty) * 4

            if any(k in query for k in [
                "어려운",
                "고난도"
            ]):
                score += difficulty * 4

        satisfaction = get_number(item, ["satisfaction"])
        puzzle = get_number(item, ["puzzle"])
        story = get_number(item, ["story"])
        interior = get_number(item, ["interior"])
        production = get_number(item, ["production"])

        if satisfaction is not None:
            score += satisfaction * 4

        if "퍼즐" in query and puzzle is not None:
            score += puzzle * 5

        if "스토리" in query and story is not None:
            score += story * 5

        if "인테리어" in query and interior is not None:
            score += min(interior, 5) * 5

        if "연출" in query and production is not None:
            score += min(production, 5) * 5

    # =========================
    # 머더미스터리
    # =========================

    elif category == "murder":
        if difficulty is not None:
            if any(k in query for k in [
                "입문",
                "쉬운",
                "초보"
            ]):
                if difficulty <= 2:
                    score += 20
                else:
                    score -= 10

            if any(k in query for k in [
                "어려운",
                "고난도",
                "복잡"
            ]):
                if difficulty >= 3:
                    score += 20
                else:
                    score -= 5

        if rating:
            score += rating * 5

        if "보드게임형" in query:
            scene_category = str(item.get("scene_category", ""))

            if "보드게임형" in scene_category:
                score += 15
            else:
                score -= 100

    return score


# =========================
# 2차 가중치
# 랭크 / 평점 / 리뷰 수 기반 품질 보정
# =========================

def second_weight_score(query, item, category):
    score = 0

    rating = get_number(item, [
        "avg_rating",
        "average_rating",
        "rating",
        "bayesaverage",
        "bayes_average",
        "satisfaction"
    ])

    category_rank = get_number(item, [
        "category_rank",
        "overall_rank",
        "rank"
    ])

    review_count = get_number(item, [
        "review_count",
        "num_reviews",
        "users_rated",
        "rating_count",
        "voters"
    ])

    # =========================
    # 평점 2차 보정
    # =========================

    if rating is not None:
        if category == "boardgame":
            # BGG 기준 1~10점
            if rating >= 8:
                score += 20
            elif rating >= 7.5:
                score += 15
            elif rating >= 7:
                score += 10
            elif rating >= 6.5:
                score += 5

        elif category in ["escape", "murder"]:
            # 빠방 / 머더미스터리 기준 0~5점
            if rating >= 4.8:
                score += 20
            elif rating >= 4.5:
                score += 15
            elif rating >= 4.0:
                score += 10
            elif rating >= 3.5:
                score += 5

    # =========================
    # 랭크 2차 보정
    # 낮은 숫자일수록 좋은 순위
    # =========================

    if category_rank is not None:
        if category_rank <= 10:
            score += 25
        elif category_rank <= 50:
            score += 20
        elif category_rank <= 100:
            score += 15
        elif category_rank <= 300:
            score += 10
        elif category_rank <= 1000:
            score += 5

    # =========================
    # 리뷰 수 / 평가 수 신뢰도 보정
    # =========================

    if review_count is not None:
        if review_count >= 10000:
            score += 15
        elif review_count >= 3000:
            score += 12
        elif review_count >= 1000:
            score += 10
        elif review_count >= 300:
            score += 6
        elif review_count >= 100:
            score += 3

    return score


# =========================
# 조건 기반 점수
# =========================

def condition_score(item, conditions):
    text = json.dumps(item, ensure_ascii=False).lower()

    total_possible = sum(conditions.values())
    earned = 0
    detail = {}

    min_players = get_number(item, [
        "min_players", "minplayers", "min_player", "minimum_players"
    ])

    max_players = get_number(item, [
        "max_players", "maxplayers", "max_player", "maximum_players"
    ])

    weight_value = get_number(item, [
        "weight", "average_weight", "complexity", "avg_weight"
    ])

    rating = get_number(item, [
        "rating", "average_rating", "avg_rating",
        "bayesaverage", "bayes_average"
    ])

    for condition, weight in conditions.items():
        keywords = CONDITION_KEYWORDS.get(
            condition,
            []
        )

        matched = [
            keyword for keyword in keywords
            if keyword.lower() in text
        ]

        if condition == "boardgame":
            matched.append("category=boardgame")

        if condition == "popular":
            if rating and rating >= 7:
                matched.append(f"rating {rating}")

        if condition == "player_7":
            if min_players and max_players and min_players <= 7 <= max_players:
                matched.append(
                    f"player range {int(min_players)}-{int(max_players)}"
                )
            elif max_players and max_players >= 7:
                matched.append(f"max_players {int(max_players)}")

        if condition == "many_players":
            if max_players and max_players >= 6:
                matched.append(f"max_players {int(max_players)}")

        if condition == "easy":
            if weight_value and weight_value <= 2.5:
                matched.append(f"weight {weight_value}")

        if matched:
            earned += weight
            detail[condition] = {
                "score": weight,
                "matched": matched,
            }

        else:
            detail[condition] = {
                "score": 0,
                "matched": [],
            }

    if total_possible == 0:
        return 0, detail

    return earned / total_possible, detail


# =========================
# RRF
# =========================

def rrf_score(rank, k=60):
    return 1 / (k + rank)


def keyword_retrieve(
    query,
    data,
    category,
    top_k=50
):
    scored = []

    for item in data:
        base_score = simple_keyword_score(
            query,
            item
        )

        first_score = first_weight_score(
            query,
            item,
            category
        )

        second_score = second_weight_score(
            query,
            item,
            category
        )

        final_score = (
            base_score
            + first_score
            + second_score
        )

        # 하드필터 탈락 제거
        if final_score <= -50:
            continue

        scored.append({
            "title": get_title(item),
            "score": final_score,
            "base_score": base_score,
            "first_weight_score": first_score,
            "second_weight_score": second_score,
            "item": item,
        })

    scored.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    return scored[:top_k]


def condition_retrieve(
    data,
    conditions,
    top_k=50
):
    scored = []

    for item in data:
        score, detail = condition_score(
            item,
            conditions
        )

        scored.append({
            "title": get_title(item),
            "score": score,
            "detail": detail,
            "item": item,
        })

    scored.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    return scored[:top_k]


def rrf_fusion(
    result_lists,
    k=60,
    top_k=5
):
    fused = {}

    for result_list in result_lists:
        for rank, result in enumerate(
            result_list,
            start=1
        ):
            title = result["title"]

            if title not in fused:
                fused[title] = {
                    "title": title,
                    "rrf_score": 0,
                    "item": result["item"],
                    "debug": [],
                }

            fused[title]["rrf_score"] += rrf_score(
                rank,
                k
            )

            fused[title]["debug"].append({
                "rank": rank,
                "score": result.get("score", 0),
                "base_score": result.get("base_score"),
                "first_weight_score": result.get("first_weight_score"),
                "second_weight_score": result.get("second_weight_score"),
            })

    final_results = list(
        fused.values()
    )

    final_results.sort(
        key=lambda x: x["rrf_score"],
        reverse=True
    )

    return final_results[:top_k]


def recommend(
    query,
    category,
    conditions,
    top_k=5
):
    if category == "boardgame":
        data = boardgame_meta

    elif category == "escape":
        data = escape_meta

    elif category == "murder":
        data = murder_meta

    else:
        data = (
            boardgame_meta
            + escape_meta
            + murder_meta
        )

    # 기본 키워드 + 1차 가중치 + 2차 가중치
    keyword_results = keyword_retrieve(
        query=query,
        data=data,
        category=category,
        top_k=50
    )

    # 조건 충족도 기반 랭킹
    condition_results = condition_retrieve(
        data=data,
        conditions=conditions,
        top_k=50
    )

    # RRF 융합
    results = rrf_fusion(
        [
            keyword_results,
            condition_results
        ],
        k=60,
        top_k=top_k
    )

    return results


def grade_score(score):
    if score >= 0.8:
        return "매우 적합"
    elif score >= 0.6:
        return "적합"
    elif score >= 0.4:
        return "보통"
    elif score >= 0.2:
        return "낮음"
    else:
        return "부적합"


# =========================
# 실행
# =========================

boardgame_meta = load_json(
    BOARDGAME_META_PATH
)

escape_meta = load_json(
    ESCAPE_META_PATH
)

murder_meta = load_json(
    MURDER_META_PATH
)

print("\n==============================")
print("2차 가중치 적용 → RRF 추천 평가")
print("==============================\n")

print("boardgame_meta:", len(boardgame_meta))
print("escape_meta:", len(escape_meta))
print("murder_meta:", len(murder_meta))
print()

all_query_scores = []

for query, info in EVAL_QUERIES.items():
    category = info["category"]
    conditions = info["conditions"]

    results = recommend(
        query=query,
        category=category,
        conditions=conditions,
        top_k=5
    )

    print(f"[쿼리] {query}")
    print(f"[카테고리] {category}")
    print("[추천 결과]")

    query_scores = []

    for idx, result in enumerate(
        results,
        start=1
    ):
        score, detail = condition_score(
            result["item"],
            conditions
        )

        query_scores.append(score)

        base_score = simple_keyword_score(
            query=query,
            item=result["item"]
        )

        first_score = first_weight_score(
            query=query,
            item=result["item"],
            category=category
        )

        second_score = second_weight_score(
            query=query,
            item=result["item"],
            category=category
        )

        final_score = (
            base_score
            + first_score
            + second_score
        )

        print(f"{idx}. {result['title']}")
        print(f"   기본 키워드 점수: {base_score:.2f}")
        print(f"   1차 가중치 점수: {first_score:.2f}")
        print(f"   2차 가중치 점수: {second_score:.2f}")
        print(f"   2차 적용 후 점수: {final_score:.2f}")
        print(f"   최종 RRF 점수: {result['rrf_score']:.6f}")
        print(f"   조건 충족 점수: {score:.4f}")
        print(f"   등급: {grade_score(score)}")

        print("   [RRF 반영 랭크 정보]")
        for debug in result.get("debug", []):
            print(
                f"   - rank: {debug['rank']}, "
                f"score: {debug['score']:.2f}, "
                f"base: {debug.get('base_score')}, "
                f"1차: {debug.get('first_weight_score')}, "
                f"2차: {debug.get('second_weight_score')}"
            )

        print("   [조건 상세]")
        for cond, value in detail.items():
            print(
                f"   - {cond}: "
                f"{value['score']}점 / "
                f"매칭 키워드: "
                f"{value['matched']}"
            )

        print()

    avg_score = (
        sum(query_scores)
        / len(query_scores)
        if query_scores else 0
    )

    all_query_scores.append(
        avg_score
    )

    print(
        f"Condition Match Score@5: "
        f"{avg_score:.4f}"
    )
    print(
        f"등급: "
        f"{grade_score(avg_score)}"
    )
    print("-" * 50)

total_avg = (
    sum(all_query_scores)
    / len(all_query_scores)
    if all_query_scores else 0
)

print("\n==============================")
print("전체 평균 점수")
print("==============================")
print(
    f"Average Condition Match Score@5: "
    f"{total_avg:.4f}"
)
print(
    f"전체 등급: "
    f"{grade_score(total_avg)}"
)