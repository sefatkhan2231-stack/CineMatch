from collections import defaultdict
import math

def evaluate_rank(
    testset,
    train_seen,
    train_movie_ids,
    score_movies,
    k=10
):

    relevant_test = defaultdict(set)

    for user_id, movie_id, rating in testset:
        if rating >= 4:
            relevant_test[user_id].add(movie_id)

    precisions, recalls, ndcgs = [], [], []

    for user_id, relevant_movies in relevant_test.items():

        seen_movies = train_seen.get(user_id, set())

        candidates = [
            movie_id
            for movie_id in train_movie_ids
            if movie_id not in seen_movies
        ]

        scored = [
            (movie_id, score_movies(user_id, movie_id))
            for movie_id in candidates
        ]

        scored.sort(key=lambda item: item[1], reverse=True)
        recommended = [movie_id for movie_id, _ in scored[:k]]

        hits = sum(
            movie_id in relevant_movies
            for movie_id in recommended
        )

        precisions.append(hits / k)
        recalls.append(hits / len(relevant_movies))

        dcg = sum(
            1 / math.log2(rank + 1)
            for rank, movie_id in enumerate(recommended, start=1)
            if movie_id in relevant_movies
        )

        ideal_hits = min(len(relevant_movies), k)
        idcg = sum(
            1 / math.log2(rank + 1)
            for rank in range(1, ideal_hits + 1)
        )

        ndcgs.append(dcg / idcg if idcg else 0.0)

    if not precisions:
        raise ValueError(
            "No users with relevant test ratings were available."
        )

    return {
        "users_evaluated": len(precisions),
        f"precision@{k}": sum(precisions) / len(precisions),
        f"recall@{k}": sum(recalls) / len(recalls),
        f"ndcg@{k}": sum(ndcgs) / len(ndcgs),
    }

