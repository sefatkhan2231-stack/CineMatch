from collections import defaultdict
from pathlib import Path
import math

import pandas as pd
from surprise import Dataset, Reader
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

train_rows = [
    (
        trainset_full.to_raw_uid(uid),
        trainset_full.to_raw_iid(iid),
        rating,
    )
    for uid, iid, rating in trainset_full.all_ratings()
]

train_df = pd.DataFrame(
    train_rows, columns=['user_id', 'movie_id', 'rating']
)

global_mean = train_df['rating'].mean()

movie_stats = train_df.groupby('movie_id')['rating'].agg(
    ['count', 'mean']
)

m = 20
movie_stats['popularity_score'] = (
    movie_stats['count'] * movie_stats['mean']
    + m * global_mean
) / (movie_stats['count'] + m)

train_seen = defaultdict(set)
for user_id, movie_id, _ in train_rows:
    train_seen[user_id].add(movie_id)

train_movie_ids = sorted(movie_stats.index.to_list())

relevant_test = defaultdict(set)
for user_id, movie_id, rating in testset:
    if rating >= 4:
        relevant_test[user_id].add(movie_id)

K = 10
precisions, recalls, ndcgs = [], [], []

for user_id, relevant_movies in relevant_test.items():
    if not relevant_movies:
        continue

    candidates = [
        movie_id for movie_id in train_movie_ids
        if movie_id not in train_seen[user_id]
    ]

    ranked = sorted(
        candidates,
        key=lambda movie_id: movie_stats.loc[
            movie_id, 'popularity_score'
        ],
        reverse=True,
    )

    recommended = ranked[:K]

    hits = sum(movie_id in relevant_movies for movie_id in recommended)
    precisions.append(hits / K)
    recalls.append(hits / len(relevant_movies))

    dcg = sum(
        1 / math.log2(rank + 1)
        for rank, movie_id in enumerate(recommended, start=1)
        if movie_id in relevant_movies
    )

    ideal_hits = min(len(relevant_movies), K)
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
        movie_stats.loc[movie_id, 'popularity_score']
    ),
    k=10,
)

print("\nFinal popularity test results (K=10)")
print(f"Users evaluated: {results['users_evaluated']:,}")
print(f"Precision@10: {results['precision@10']:.4f}")
print(f"Recall@10:    {results['recall@10']:.4f}")
print(f"NDCG@10:      {results['ndcg@10']:.4f}")