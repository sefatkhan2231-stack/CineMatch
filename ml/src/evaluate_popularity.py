from collections import defaultdict
from pathlib import Path
import math

import pandas as pd
from surprise import Dataset, Reader
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
    names=["user_id", "movie_id", "rating", "timestamp"],
)

reader = Reader(
    line_format='user item rating timestamp',
    sep='\t',
    rating_scale=(1, 5),
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

print(f"Training ratings: {trainset.n_ratings:,}")
print(f"Test ratings: {len(testset):,}")

train_rows = [
    (trainset.to_raw_uid(uid), trainset.to_raw_iid(iid), rating)
    for uid, iid, rating in trainset.all_ratings()
]

train_df = pd.DataFrame(
    train_rows,
    columns=['user_id', 'movie_id', 'rating'],
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

relevant_test = defaultdict(set)

for user_id, movie_id, rating in testset:
    if rating >= 4:
        relevant_test[user_id].add(movie_id)

all_movie_ids = sorted(movie_stats.index.tolist())

K = 10
precisions = []
recalls = []
ndcgs = []

for user_id, relevant_movies in relevant_test.items():
    candidates = [
        movie_id
        for movie_id in all_movie_ids
        if movie_id not in train_seen[user_id]
        and movie_id in movie_stats.index 
    ]

    if not candidates or not relevant_movies:
        continue

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

print(f"\nPopularity ranking evaluation (K={K})")
print(f"Users evaluated: {len(precisions):,}")
print(f"Precision@{K}: {sum(precisions) / len(precisions):.4f}")
print(f"Recall@{K}:    {sum(recalls) / len(recalls):.4f}")
print(f"NDCG@{K}:      {sum(ndcgs) / len(ndcgs):.4f}")