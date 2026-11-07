from collections import defaultdict
from pathlib import Path
import math

import pandas as pd
from surprise import Dataset, Reader, SVD
from surprise.model_selection import train_test_split

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = (
    PROJECT_ROOT
    / 'ml'
    / 'data'
    / 'raw'
    / 'ml-100k'
    / 'ml-100k'
)

ratings_file = DATA_DIR / 'u.data'

ratings = pd.read_csv(
    ratings_file,
    sep='\t',
    names=['user_id', 'movie_id', 'rating', 'timestamp'],
)

reader = Reader(
    line_format='user item rating timestamp',
    sep='\t',
    rating_scale=(1, 5)
)

data = Dataset.load_from_file(
    str(ratings_file),
    reader=reader,
)

trainset, testset = train_test_split(
    data,
    test_size=0.20,
    random_state=42,
)

model = SVD(
    n_factors=50,
    n_epochs=20,
    lr_all=0.005,
    reg_all=0.02,
    random_state=42,
)

model.fit(trainset)

print("SVD trained.")
print(f"Training ratings: {trainset.n_ratings:,}")
print(f"Test ratings: {len(testset):,}")

train_seen = defaultdict(set)

for inner_uid, inner_iid, rating in trainset.all_ratings():
    user_id = trainset.to_raw_uid(inner_uid)
    movie_id = trainset.to_raw_iid(inner_iid)
    train_seen[user_id].add(movie_id)

relevant_test = defaultdict(set)

for user_id, movie_id, rating in testset:
    if rating >= 4:
        relevant_test[user_id].add(movie_id)

K = 10
precisions = []
recalls = []
ndcgs = []

train_movie_ids = {
    trainset.to_raw_iid(inner_iid)
    for inner_iid in trainset.all_items()
}

all_movie_ids = sorted(train_movie_ids)

for user_id, relevant_movies in relevant_test.items():
    candidates = [
        movie_id
        for movie_id in all_movie_ids
        if movie_id not in train_seen[user_id]
    ]

    if not candidates or not relevant_movies:
        continue

    scored_movies = [
        (movie_id, model.predict(user_id, movie_id).est)
        for movie_id in candidates
    ]

    top_k = sorted(
        scored_movies,
        key=lambda item: item[1],
        reverse=True,
    )[:K]

    recommended_ids = [movie_id for movie_id, _ in top_k]
    hits = sum(movie_id in relevant_movies for movie_id in recommended_ids)

    precision = hits / K
    recall = hits / len(relevant_movies)

    dcg = sum(
        1 / math.log2(rank + 1)
        for rank, movie_id in enumerate(recommended_ids, start=1)
        if movie_id in relevant_movies
    )

    ideal_hits = min(len(relevant_movies), K)
    idcg = sum(
        1 / math.log2(rank + 1)
        for rank in range(1, ideal_hits + 1)
    )

    ndcg = dcg / idcg if idcg else 0.0

    precisions.append(precision)
    recalls.append(recall)
    ndcgs.append(ndcg)

print(f"\nRanking evaluation (K={K})")
print(f"Users evaluated: {len(precisions):,}")
print(f"Precision@{K}: {sum(precisions) / len(precisions):.4f}")
print(f"Recall@{K}:    {sum(recalls) / len(recalls):.4f}")
print(f"NDCG@{K}:      {sum(ndcgs) / len(ndcgs):.4f}")