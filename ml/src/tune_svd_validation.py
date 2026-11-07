from pathlib import Path
from collections import defaultdict
import math

import pandas as pd
from surprise import Dataset, Reader, SVD
from sklearn.model_selection import train_test_split

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
    ratings_file,
    reader=reader,
)

raw_ratings = data.raw_ratings

dev_raw, test_raw = train_test_split(raw_ratings, test_size=0.20, random_state=42)
train_raw, val_raw = train_test_split(dev_raw, test_size=0.20, random_state=43)

trainset = data.construct_trainset(train_raw)
validation_set = data.construct_testset(val_raw)
testset = data.construct_testset(test_raw)

print(f"Training ratings: {trainset.n_ratings:,}")
print(f"Validation ratings: {len(validation_set):,}")
print(f"Final test ratings reserved: {len(testset):,}")

train_seen = defaultdict(set)
train_movie_ids = set()

for inner_uid, inner_iid, _ in trainset.all_ratings():
    user_id = trainset.to_raw_uid(inner_uid)
    movie_id = trainset.to_raw_iid(inner_iid)
    train_seen[user_id].add(movie_id)
    train_movie_ids.add(movie_id)

train_movie_ids = sorted(train_movie_ids)

def ranking_metrics(model, evaluation_ratings, k=10):
    relevant = defaultdict(set)

    for user_id, movie_id, rating in evaluation_ratings:
        if rating >= 4:
            relevant[user_id].add(movie_id)

    precisions, recalls, ndcgs = [], [], []

    for user_id, relevant_movies in relevant.items():
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
        ndcgs.append(dcg/ idcg if idcg else 0.0)

    if not precisions:
        return 0.0, 0.0, 0.0, 0

    return (
        sum(precisions) / len(precisions),
        sum(recalls) / len(recalls),
        sum(ndcgs) / len(ndcgs),
        len(precisions),
    )

configs = [
    {"n_factors": 50, "n_epochs": 40, "reg_all": 0.01},
    {"n_factors": 50, "n_epochs": 40, "reg_all": 0.02},
    {"n_factors": 50, "n_epochs": 60, "reg_all": 0.01},
    {"n_factors": 50, "n_epochs": 60, "reg_all": 0.02},
    {"n_factors": 100, "n_epochs": 40, "reg_all": 0.01},
    {"n_factors": 100, "n_epochs": 40, "reg_all": 0.02},
    {"n_factors": 100, "n_epochs": 60, "reg_all": 0.01},
    {"n_factors": 100, "n_epochs": 60, "reg_all": 0.02},
]

results = []

for config in configs:
    print(f"\nTraining SVD: {config}")

    model = SVD(
        n_factors=config['n_factors'],
        n_epochs=config['n_epochs'],
        lr_all=0.005,
        reg_all=config['reg_all'],
        random_state=42,
    )

    model.fit(trainset)

    precision, recall, ndcg, users = ranking_metrics(
        model, validation_set
    )

    results.append({
        **config,
        "Precision@10": precision,
        "Recall@10": recall,
        "NDCG@10": ndcg,
        "Users": users,
    })

results_df = pd.DataFrame(results).sort_values(
    'NDCG@10', ascending=False
)

print("\nValidation results (sorted by NDCG@10)")
print(results_df.to_string(
    index=False, float_format=lambda x: f"{x:.4f}"
))