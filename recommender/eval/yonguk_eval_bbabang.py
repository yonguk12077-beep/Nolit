import os
import re
import json
import faiss
import argparse
import numpy as np
from collections import defaultdict
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer


def get_model_dim(model):
    if hasattr(model, "get_embedding_dimension"):
        return model.get_embedding_dimension()
    return model.get_sentence_embedding_dimension()


def load_metadata(path):
    if not os.path.exists(path):
        raise FileNotFoundError(f"파일을 찾을 수 없습니다: {path}")

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def tokenize(text):
    if text is None:
        return []
    return str(text).lower().split()


def extract_query_conditions(query):
    filters = {}
    prefs = {}

    if "서울" in query:
        filters["area"] = "서울"
    elif "경기" in query:
        filters["area"] = "경기"
    elif "강원" in query:
        filters["area"] = "강원"

    if "원주시" in query or "원주" in query:
        filters["location"] = "원주시"
    elif "강릉시" in query or "강릉" in query:
        filters["location"] = "강릉시"
    elif "강남구" in query:
        filters["location"] = "강남구"
    elif "마포구" in query:
        filters["location"] = "마포구"
    elif "부천" in query:
        filters["location"] = "부천시"
    elif "수원" in query:
        filters["location"] = "수원시"
    elif "인천" in query:
        filters["location"] = "인천"

    m = re.search(r"(\d+)\s*(명|인)", query)
    if m:
        filters["max_players"] = int(m.group(1))

    m = re.search(r"(\d+)\s*만\s*원\s*이하", query)
    if m:
        filters["price"] = int(m.group(1)) * 10000

    m = re.search(r"(\d+)\s*원\s*이하", query)
    if m:
        filters["price"] = int(m.group(1))

    m = re.search(r"(\d+)\s*시간\s*이내", query)
    if m:
        filters["playing_time"] = int(m.group(1)) * 60

    m = re.search(r"(\d+)\s*분\s*이내", query)
    if m:
        filters["playing_time"] = int(m.group(1))

    if any(w in query for w in ["안 무서운", "안무서운", "무섭지 않은", "공포 없는", "쫄보"]):
        prefs["horror"] = "low"
    elif any(w in query for w in ["무서운", "공포", "호러"]):
        prefs["horror"] = "high"

    if any(w in query for w in ["쉬운", "입문", "초보", "방린이"]):
        prefs["difficulty"] = "low"
    elif any(w in query for w in ["어려운", "고난도", "하드", "빡센"]):
        prefs["difficulty"] = "high"

    if any(w in query for w in ["퍼즐", "문제", "문제 잘 만든", "문제 퀄"]):
        prefs["puzzle"] = True

    if any(w in query for w in ["스토리", "서사", "몰입"]):
        prefs["story"] = True

    if any(w in query for w in ["인테리어", "예쁜", "잘 꾸민"]):
        prefs["interior"] = True

    if any(w in query for w in ["연출", "장치", "퀄리티"]):
        prefs["production"] = True

    prefs["satisfaction"] = True

    return filters, prefs


def make_doc_text(item):
    parts = []
    for key in ["title", "store_name", "document", "area", "location"]:
        if item.get(key) is not None:
            parts.append(str(item.get(key)))
    return " ".join(parts)


def build_bm25(metadata):
    corpus = [tokenize(make_doc_text(item)) for item in metadata]
    return BM25Okapi(corpus)


def build_stats_lookup(stats_metadata):
    lookup = {}

    for item in stats_metadata:
        key = (
            str(item.get("title", "")).strip(),
            str(item.get("store_name", "")).strip()
        )
        lookup[key] = item

    return lookup


def get_stats_item(review_item, stats_lookup):
    key = (
        str(review_item.get("title", "")).strip(),
        str(review_item.get("store_name", "")).strip()
    )

    return stats_lookup.get(key, review_item)


def bm25_search(query, bm25, top_n=1000):
    scores = bm25.get_scores(tokenize(query))
    ranked = np.argsort(scores)[::-1][:top_n]
    return ranked.tolist()


def dense_search(query, model, index, top_n=1000):
    q_emb = model.encode([query], convert_to_numpy=True)
    q_emb = np.asarray(q_emb).astype("float32")

    if q_emb.ndim == 1:
        q_emb = q_emb.reshape(1, -1)

    if q_emb.shape[1] != index.d:
        raise ValueError(
            f"FAISS index 차원({index.d})과 모델 차원({q_emb.shape[1]})이 다릅니다."
        )

    distances, indices = index.search(q_emb, top_n)
    return [int(i) for i in indices[0] if i != -1]


def passes_hard_filter(item, filters):
    if not filters:
        return True

    if filters.get("area"):
        if item.get("area") != filters["area"]:
            return False

    if filters.get("location"):
        if item.get("location") != filters["location"]:
            return False

    if filters.get("max_players"):
        max_players = item.get("max_players")
        if max_players is None:
            return False
        if filters["max_players"] > max_players:
            return False

    if filters.get("price"):
        price = item.get("price")
        if price is None:
            return False
        if price > filters["price"]:
            return False

    if filters.get("playing_time"):
        playing_time = item.get("playing_time")
        if playing_time is None:
            return False
        if playing_time > filters["playing_time"]:
            return False

    return True


def filter_ranked_docs(ranked_docs, review_metadata, stats_lookup, filters):
    filtered = []

    for doc_id in ranked_docs:
        if doc_id < 0 or doc_id >= len(review_metadata):
            continue

        review_item = review_metadata[doc_id]
        stats_item = get_stats_item(review_item, stats_lookup)

        if passes_hard_filter(stats_item, filters):
            filtered.append(doc_id)

    return filtered


def rrf_fusion(rank_lists, rrf_k=60):
    scores = defaultdict(float)

    for ranked_docs in rank_lists:
        for rank, doc_id in enumerate(ranked_docs, start=1):
            scores[doc_id] += 1.0 / (rrf_k + rank)

    return scores


def normalize_score(value, max_value=5.0):
    if value is None:
        return None

    try:
        return min(float(value) / max_value, 1.0)
    except:
        return None


def first_weight_bonus(item, prefs):
    score = 0.0

    horror = normalize_score(item.get("horror"), 5.0)
    if horror is not None:
        if prefs.get("horror") == "low":
            score += (1.0 - horror) * 0.20
        elif prefs.get("horror") == "high":
            score += horror * 0.20

    difficulty = normalize_score(item.get("difficulty"), 5.0)
    if difficulty is not None:
        if prefs.get("difficulty") == "low":
            score += (1.0 - difficulty) * 0.15
        elif prefs.get("difficulty") == "high":
            score += difficulty * 0.15

    satisfaction = normalize_score(item.get("satisfaction"), 5.0)
    if satisfaction is not None and prefs.get("satisfaction"):
        score += satisfaction * 0.20

    if prefs.get("puzzle"):
        puzzle = normalize_score(item.get("puzzle"), 5.0)
        if puzzle is not None:
            score += puzzle * 0.10

    if prefs.get("story"):
        story = normalize_score(item.get("story"), 5.0)
        if story is not None:
            score += story * 0.10

    if prefs.get("interior"):
        interior = normalize_score(item.get("interior"), 6.0)
        if interior is not None:
            score += interior * 0.10

    if prefs.get("production"):
        production = normalize_score(item.get("production"), 6.5)
        if production is not None:
            score += production * 0.10

    return score


def second_weight_rating_bonus(item):
    fields = ["satisfaction", "story", "puzzle", "interior", "production"]

    values = []
    for field in fields:
        value = item.get(field)
        if value is not None:
            try:
                values.append(float(value))
            except:
                pass

    if not values:
        return 0.0

    avg = sum(values) / len(values)

    return (avg / 5.0) * 0.10


def second_weight_rank_bonus(rank):
    return (1.0 / rank) * 0.05


def add_weight_bonus(rrf_scores, review_metadata, stats_lookup, prefs, use_rank_bonus=True):
    final_scores = []

    sorted_rrf = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)

    for rank, (doc_id, rrf_score) in enumerate(sorted_rrf, start=1):
        review_item = review_metadata[doc_id]
        stats_item = get_stats_item(review_item, stats_lookup)

        first_bonus = first_weight_bonus(stats_item, prefs)
        second_rating_bonus = second_weight_rating_bonus(stats_item)

        if use_rank_bonus:
            second_rank_bonus = second_weight_rank_bonus(rank)
        else:
            second_rank_bonus = 0.0

        second_bonus = second_rating_bonus + second_rank_bonus
        final_score = rrf_score + first_bonus + second_bonus

        final_scores.append(
            (
                doc_id,
                final_score,
                rrf_score,
                first_bonus,
                second_rating_bonus,
                second_rank_bonus,
                second_bonus
            )
        )

    final_scores.sort(key=lambda x: x[1], reverse=True)
    return final_scores


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("--review_meta", type=str, default="faiss_bbabang_reviews_metadata.json")
    parser.add_argument("--stats_meta", type=str, default="faiss_bbabang_stats_metadata.json")
    parser.add_argument("--index", type=str, default="faiss_bbabang_reviews.index")
    parser.add_argument("--model", type=str, default="jhgan/ko-sroberta-multitask")
    parser.add_argument("--top_n", type=int, default=1000)
    parser.add_argument("--rrf_k", type=int, default=60)
    parser.add_argument("--no_rank_bonus", action="store_true")

    args = parser.parse_args()

    review_metadata = load_metadata(args.review_meta)
    stats_metadata = load_metadata(args.stats_meta)
    stats_lookup = build_stats_lookup(stats_metadata)

    print("Loading FAISS index...")
    index = faiss.read_index(args.index)

    print("Loading model...")
    model = SentenceTransformer(args.model)

    print("FAISS index dimension:", index.d)
    print("Model dimension:", get_model_dim(model))

    if index.d != get_model_dim(model):
        raise ValueError(
            f"FAISS index dimension({index.d})과 model dimension({get_model_dim(model)})이 다릅니다."
        )

    print("Building BM25...")
    bm25 = build_bm25(review_metadata)

    query = "원주에서 스토리 좋고 만족도 높은 방탈출 추천"

    # query = "원주에서 3명이 할 수 있는 스토리 좋고 만족도 높은 방탈출 추천"
    # query = "원주에서 2명이 할 수 있는 안 무서운 입문용 방탈출 추천"
    # query = "강릉에서 커플이 하기 좋은 인테리어 예쁜 방탈출 추천"
    # query = "원주에서 퍼즐 잘 만들고 어려운 고난도 방탈출 추천"

    print("\nUser Query:", query)

    filters, prefs = extract_query_conditions(query)

    print("Filters:", filters)
    print("Preferences:", prefs)

    bm25_results = bm25_search(query, bm25, top_n=args.top_n)
    dense_results = dense_search(query, model, index, top_n=args.top_n)

    bm25_filtered = filter_ranked_docs(
        ranked_docs=bm25_results,
        review_metadata=review_metadata,
        stats_lookup=stats_lookup,
        filters=filters
    )

    dense_filtered = filter_ranked_docs(
        ranked_docs=dense_results,
        review_metadata=review_metadata,
        stats_lookup=stats_lookup,
        filters=filters
    )

    print("BM25 filtered count:", len(bm25_filtered))
    print("Dense filtered count:", len(dense_filtered))

    rrf_scores = rrf_fusion(
        [bm25_filtered, dense_filtered],
        rrf_k=args.rrf_k
    )

    final_results = add_weight_bonus(
        rrf_scores=rrf_scores,
        review_metadata=review_metadata,
        stats_lookup=stats_lookup,
        prefs=prefs,
        use_rank_bonus=not args.no_rank_bonus
    )

    print("\n===== TOP RESULTS =====")

    if not final_results:
        print("조건을 만족하는 결과가 없습니다.")
    else:
        for rank, result in enumerate(final_results[:10], start=1):
            (
                doc_id,
                final_score,
                rrf_score,
                first_bonus,
                second_rating_bonus,
                second_rank_bonus,
                second_bonus
            ) = result

            review_item = review_metadata[doc_id]
            stats_item = get_stats_item(review_item, stats_lookup)

            print(
                f"{rank}. {review_item.get('title')} | {review_item.get('store_name')} | "
                f"area={stats_item.get('area')} | "
                f"location={stats_item.get('location')} | "
                f"max_players={stats_item.get('max_players')} | "
                f"price={stats_item.get('price')} | "
                f"playing_time={stats_item.get('playing_time')} | "
                f"horror={stats_item.get('horror')} | "
                f"difficulty={stats_item.get('difficulty')} | "
                f"satisfaction={stats_item.get('satisfaction')} | "
                f"rrf={rrf_score:.4f} | "
                f"first_bonus={first_bonus:.4f} | "
                f"second_rating_bonus={second_rating_bonus:.4f} | "
                f"second_rank_bonus={second_rank_bonus:.4f} | "
                f"second_bonus={second_bonus:.4f} | "
                f"final={final_score:.4f}"
            )