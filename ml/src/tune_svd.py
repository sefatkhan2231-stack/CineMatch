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

rating_file = DATA_DIR / 'u.data'

reader = Reader(
    line_format='user item rating timestamp',
    sep='\t',
    rating_scale=(1, 5),
)

ratings = pd.read_csv(
    rating_file,
    sep='\t'
)

data = Dataset.load_from_file(
    str(rating_file),
    reader=reader,
)

trainset, testset = train_test_split(
    data,
    test_size=0.20,
    random_state=42,
)

print(f"Training ratings: {trainset.n_ratings:,}")
print(f"Test ratings: {len(testset):,}")

train_seen = defaultdict(set)

for inner_uid, inner_iid, _ in trainset.all_ratings():
    user_id = trainset.to_raw_uid(inner_uid)
    movie_id = trainset.to_raw_iid(inner_iid)
    train_seen[user_id].add(movie_id)

train_movie_ids = sorted(
    trainset.to_raw_iid(inner_iid)
    for inner_iid in trainset.all_items()
)

relevant_test = defaultdict(set)

for user_id, movie_id, rating in testset:
    if rating >= 4:
        relevant_test[user_id].add(movie_id)

K = 10

def evaluate_ranking(model):
    precisions, recalls, ndcgs = [], [], []

    for user_id, relevant_movies in relevant_test.items():
        if not relevant_movies:
            continue

        candidates = [
            movie_id for movie_id in train_movie_ids
            if movie_id not in  train_seen[user_id]
        ]

        scored = [
            (movie_id, model.predict(user_id, movie_id).est)
            for movie_id in candidates
        ]

        recommended = sorted(
            scored, key=lambda item: item[1], reverse=True
        )[:K]

        recommended_ids = [movie_id for movie_id, _ in recommended]
        hits = sum(
            movie_id in relevant_movies for movie_id in recommended_ids
        )

        precisions.append(hits / K)
        recalls.append(hits / len(relevant_movies))

        dcg = sum(
            1 / math.log2(rank + 1)
            for rank, movie_id in enumerate(recommended_ids, start=1)
            if movie_id in relevant_movies
        )

        ideals_hits = min(len(relevant_movies), K)
        idcg = sum(
            1 / math.log2(rank + 1)
            for rank in range(1, ideals_hits + 1)
        )

        ndcgs.append(dcg / idcg if idcg else 0.0)

    return (
        sum(precisions) / len(precisions),
        sum(recalls) / len(recalls),
        sum(ndcgs) / len(ndcgs),
        len(precisions),
    )

configs = [
    {"n_factors": 20, "n_epochs": 20, "reg_all": 0.02},
    {"n_factors": 50, "n_epochs": 20, "reg_all": 0.02},
    {"n_factors": 100, "n_epochs": 20, "reg_all": 0.02},
    {"n_factors": 50, "n_epochs": 40, "reg_all": 0.02},
    {"n_factors": 50, "n_epochs": 20, "reg_all": 0.05},
]

results = []

for config in configs:
    print(f"\nTraining SVD with {config}")

    model = SVD(
        n_factors = config['n_factors'],
        n_epochs = config['n_epochs'],
        lr_all=0.005,
        reg_all=config['reg_all'],
        random_state=42,
    )

    model.fit(trainset)

    precision, recall, ndcg, users = evaluate_ranking(model)

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

print("\nSVD ranking tuning results (sorted by NDCG@10)")
print(results_df.to_string(index=False, float_format=lambda x: f"{x:.4f}"))