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

trainset = data.construct_trainset(train_raw)
testset = data.construct_testset(test_raw)
validation_set = data.construct_testset(val_raw)

print(f"Training ratings: {trainset.n_ratings:,}")
print(f"Validation ratings: {len(validation_set):,}")
print(f"Final test ratings reserved: {len(testset):,}")

# --------------------------------------------------
# 2. Train SVD using training ratings only
# --------------------------------------------------

svd = SVD(
    n_factors=50,
    n_epochs=40,
    lr_all=0.005,
    reg_all=0.01,
    random_state=42,
)

svd.fit(trainset)

# --------------------------------------------------
# 3. Prepare popularity scores from training ratings
# --------------------------------------------------

train_seen = defaultdict(set)
train_movie_ids = set()

train_rows = [
    (
        trainset.to_raw_uid(uid),
        trainset.to_raw_iid(iid),
        rating,
    )
    for uid, iid, rating in trainset.all_ratings()
]

train_df = pd.DataFrame(
    train_rows, columns=['user_id', 'movie_id', 'rating']
)

global_mean = train_df['rating'].mean()

movies_stats = train_df.groupby('movie_id')['rating'].agg(
    ['count', 'mean']
)

m = 20
movies_stats['popularity_score'] = (
    movies_stats['count'] * movies_stats['mean']
    + m * global_mean 
    ) / (movies_stats['count'] + m)


for user_id, movie_id, _ in train_rows:
    train_seen[user_id].add(movie_id)

train_movie_ids = sorted(movies_stats.index.to_list())

# --------------------------------------------------
# 4. Build validation relevance
# --------------------------------------------------

relevant_validation = defaultdict(set)

for user_id, movie_id, rating in validation_set:
    if rating >= 4:
        relevant_validation[user_id].add(movie_id)

# --------------------------------------------------
# 5. Cache model scores for validation candidates
# --------------------------------------------------

def minmax_normalize(values):
    values = np.asarray(values, dtype=float)

    minmum = values.min()
    maximum = values.max()

    if maximum == minmum:
        return np.zeros_like(values)

    return (values - minmum) / (maximum - minmum)

user_candidates = {}
user_scores = {}

for user_id in relevant_validation:
    candidates = [
        movie_id
        for movie_id in train_movie_ids
        if movie_id not in train_seen[user_id]
    ]

    if not candidates:
        continue

    popularity_raw = np.array([
        movies_stats.loc[movie_id, 'popularity_score']
        for movie_id in candidates
    ])

    svd_raw = np.array([
        svd.predict(user_id, movie_id).est
        for movie_id in candidates
    ])

    user_candidates[user_id] = candidates

    user_scores[user_id] = (
        minmax_normalize(svd_raw),
        minmax_normalize(popularity_raw),
    )

# --------------------------------------------------
# 6. Tune blend weights on validation data
# --------------------------------------------------

weights = [0.0, 0.25, 0.5, 0.75, 1.0]
results = []

for alpha in weights:

    def score_movies(user_id, movie_id, alpha=alpha):
        candidates = user_candidates[user_id]
        index = candidates.index(movie_id)

        svd_scores, popularity_scores = user_scores[user_id]

        return (
            alpha * svd_scores[index]
            + (1 - alpha) * popularity_scores[index]
        )

    metrics = evaluate_rank(
        testset=validation_set,
        train_seen=train_seen,
        train_movie_ids=train_movie_ids,
        score_movies=score_movies,
        k=10,
    )

    results.append({
        "svd_weight": alpha,
        "popularity_weight": 1 - alpha,
        "precision@10": metrics["precision@10"],
        "recall@10": metrics["recall@10"],
        "ndcg@10": metrics["ndcg@10"],
    })

results_df = pd.DataFrame(results).sort_values(
    "ndcg@10",
    ascending=False,
)

print("\nHybrid validation results (sorted by NDCG@10)")
print(results_df.to_string(index=False, float_format=lambda x: f"{x:.4f}"))

best = results_df.iloc[0]

print("\nBest validation configuration")
print(f"SVD weight: {best['svd_weight']:.2f}")
print(f"Popularity weight: {best['popularity_weight']:.2f}")
print(f"Validation NDCG@10: {best['ndcg@10']:.4f}")