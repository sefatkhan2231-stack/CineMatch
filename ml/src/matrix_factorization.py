from pathlib import Path

import pandas as pd
from surprise import Dataset, Reader, SVD

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

print(f"Users: {ratings['user_id'].nunique():,}")
print(f"Movies: {ratings['movie_id'].nunique():,}")
print(f"Ratings: {len(ratings):,}")

reader = Reader(
    line_format='user item rating timestamp',
    sep='\t',
    rating_scale=(1, 5),
)

data = Dataset.load_from_file(
    str(ratings_file),
    reader=reader,
)

trainset = data.build_full_trainset()

model = SVD(
    n_factors=50,
    n_epochs=20,
    lr_all=0.005,
    reg_all=0.02,
    random_state=42,
)

model.fit(trainset)

print("\nSVD matrix factorization model trained!")

user_id = '196'
movie_id = '50'

prediction = model.predict(user_id, movie_id)

print(f"\nExample prediction:")
print(f"User ID: {user_id}")
print(f"Movie ID: {movie_id}")
print(f"Predicted rating: {prediction.est:.4f}/5")