from collections import defaultdict
from pathlib import Path
import math

import numpy as np
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

# --------------------------------------------------
# 1. Load ratings and create train/validation/test split
# --------------------------------------------------

ratings_file = DATA_DIR / 'u.data'

reader = Reader(
    line_format='user item rating timestamp',
    sep='\t',
    rating_scale=(1, 5),
)

data = Dataset.load_from_file(
    str(ratings_file),
    reader=reader
)

raw = data.raw_ratings

dev_raw, test_raw = train_test_split(raw, test_size=0.20, random_state=42)
train_raw, val_raw = train_test_split(dev_raw, test_size=0.20, random_state=43)

trainset_full = data.construct_trainset(train_raw + val_raw)
testset = data.construct_testset(test_raw)

print(f"Training ratings: {trainset_full.n_ratings:,}")
print(f"Final test ratings reserved: {len(testset):,}")

# --------------------------------------------------
# 2. Train SVD on all 80,000 development ratings
# --------------------------------------------------

SVD_WEIGHT = 0.25
POPULARITY_WEIGHT = 0.75
K = 10

svd = SVD(
    n_factors=50,
    n_epochs=40,
    lr_all=0.005,
    reg_all=0.01,
    random_state=42,
)

svd.fit(trainset_full)

# --------------------------------------------------
# 3. Calculate popularity from the same training data
# --------------------------------------------------

train_seen = defaultdict(set)
train_movie_ids = set()

train_rows = [
    (
        trainset_full.to_raw_uid(uid),
        trainset_full.to_raw_iid(iid),
        rating,
    )
    for uid, iid, rating in trainset_full.all_ratings()
]

train_df = pd.DataFrame(
    train_rows,
    columns=["user_id", "movie_id", "rating"],
)

movie_stats = train_df.groupby('movie_id')['rating'].agg(
    ['count', 'mean']
)

global_mean = train_df['rating'].mean()

m = 20

movie_stats['popularity_score'] = (
    movie_stats['count'] * movie_stats['mean']
    + m * global_mean
    ) / (movie_stats['count'] + m)

for user_id, movie_id, _ in train_rows:
    train_seen[user_id].add(movie_id)

train_movie_ids = sorted(movie_stats.index.tolist())

# --------------------------------------------------
# 4. Normalize scores for each user's candidate movies
# --------------------------------------------------

def minmax_normalize(values):
    values = np.asarray(values, dtype=float)

    minimum = values.min()
    maximum = values.max()

    if maximum == minimum:
        return np.zeros_like(values)

    return (values - minimum) / (maximum - minimum)

def make_hybrid_scorer(user_id):
    candidates = [
        movie_id
        for movie_id in train_movie_ids
        if movie_id not in train_seen[user_id]
    ]

    if not candidates:
        return {}

    svd_scores = [
        svd.predict(user_id, movie_id).est
        for movie_id in candidates
    ]

    popularity_scores = [
        movie_stats.loc[movie_id, 'popularity_score']
        for movie_id in candidates
    ]

    svd_norm = minmax_normalize(svd_scores)
    popularity_norm = minmax_normalize(popularity_scores)

    return {
        movie_id: (
            SVD_WEIGHT * svd_score
            + POPULARITY_WEIGHT * popularity_score
        )
        for movie_id, svd_score, popularity_score in zip(
            candidates, svd_norm, popularity_norm
        )
    }

hybrid_scores = {}

for user_id, _, rating in testset:
    if rating >= 4 and user_id not in hybrid_scores:
        hybrid_scores[user_id] = make_hybrid_scorer(user_id)

def score_movie(user_id, movie_id):
    return hybrid_scores.get(user_id, {}).get(movie_id, 0.0)

# --------------------------------------------------
# 5. Evaluate on the reserved test set
# --------------------------------------------------

results = evaluate_rank(
    testset=testset,
    train_seen=train_seen,
    train_movie_ids=train_movie_ids,
    score_movies=score_movie,
    k=K,
)

print("\nFinal hybrid test results (K=10)")
print(f"SVD weight: {SVD_WEIGHT:.2f}")
print(f"Popularity weight: {POPULARITY_WEIGHT:.2f}")
print(f"Users evaluated: {results['users_evaluated']:,}")
print(f"Precision@{K}: {results['precision@10']:.4f}")
print(f"Recall@{K}:    {results['recall@10']:.4f}")
print(f"NDCG@{K}:      {results['ndcg@10']:.4f}")