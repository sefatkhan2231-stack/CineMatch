from collections import defaultdict
from pathlib import Path
import math

import pandas as pd
from surprise import Dataset, Reader, SVD
from sklearn.model_selection import train_test_split
from evaluate_rank import evaluate_rank

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

reader = Reader(
    line_format='user item rating timestamp',
    sep='\t',
    rating_scale=(1, 5),
)

data = Dataset.load_from_file(
    str(ratings_file),
    reader=reader,
)

raw_ratings = data.raw_ratings

dev_raw, test_raw = train_test_split(raw_ratings, test_size=0.20, random_state=42)
train_raw, val_raw = train_test_split(dev_raw, test_size=0.20, random_state=43)

trainset_full = data.construct_trainset(train_raw + val_raw)
testset = data.construct_testset(test_raw)

print(f"Final training ratings: {trainset_full.n_ratings:,}")
print(f"Reserved test ratings: {len(testset):,}")

train_seen = defaultdict(set)
train_movie_ids = set()

for inner_uid, inner_iid, _ in trainset_full.all_ratings():
    user_id = trainset_full.to_raw_uid(inner_uid)
    movie_id = trainset_full.to_raw_iid(inner_iid)
    train_seen[user_id].add(movie_id)
    train_movie_ids.add(movie_id)

train_movie_ids = sorted(train_movie_ids)

model = SVD(
    n_factors=50,
    n_epochs=40,
    lr_all=0.005,
    reg_all=0.01,
    random_state=42,
)

model.fit(trainset_full)

relevant_test = defaultdict(set)

for user_id, movie_id, rating in testset:
    if rating >= 4:
        relevant_test[user_id].add(movie_id)

k = 10

precisions, recalls, ndcgs = [], [], []


for user_id, relevant_movies in relevant_test.items():
    if not relevant_movies:
        continue

    candidates = [
        movie_id
        for movie_id in train_movie_ids
        if movie_id not in train_seen[user_id]
    ]

    scored = [
        (movie_id, model.predict(user_id, movie_id).est)
        for movie_id in candidates
    ]

    recommended = sorted(
        scored, key=lambda item: item[1], reverse=True
    )[:k]

    recommended_ids = [movie_id for movie_id, _ in recommended]
    hits = sum(
        movie_id in relevant_movies for movie_id in recommended_ids
    )

    precisions.append(hits / k)
    recalls.append(hits / len(relevant_movies))

    dcg = sum(
        1 / math.log2(rank + 1)
        for rank, movie_id in enumerate(recommended_ids, start=1)
        if movie_id in relevant_movies
    )

    ideal_hits = min(len(relevant_movies), k)
    idcg = sum(
        1 / math.log2(rank + 1)
        for rank in range(1, ideal_hits + 1)
    )

    ndcgs.append(dcg / idcg if idcg else 0.0)

results = evaluate_rank(
    testset=testset,
    train_seen=train_seen,
    train_movie_ids=train_movie_ids,
    score_movies=lambda user_id, movie_id: (
        model.predict(user_id, movie_id).est
    ),
    k=10,
)

print("\nFinal SVD test results (K=10)")
print(f"Users evaluated: {results['users_evaluated']:,}")
print(f"Precision@10: {results['precision@10']:.4f}")
print(f"Recall@10:    {results['recall@10']:.4f}")
print(f"NDCG@10:      {results['ndcg@10']:.4f}")