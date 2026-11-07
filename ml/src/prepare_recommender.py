
from pathlib import Path

import joblib
import pandas as pd
from surprise import Dataset, Reader, SVD


# --------------------------------------------------
# 1. Paths
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATA_DIR = (
    PROJECT_ROOT
    / "ml"
    / "data"
    / "raw"
    / "ml-100k"
    / "ml-100k"
)

ARTIFACT_DIR = PROJECT_ROOT / "ml" / "artifacts"
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)

RATINGS_FILE = DATA_DIR / "u.data"
MOVIES_FILE = DATA_DIR / "u.item"


# --------------------------------------------------
# 2. Load data
# --------------------------------------------------

ratings = pd.read_csv(
    RATINGS_FILE,
    sep="\t",
    names=["user_id", "movie_id", "rating", "timestamp"],
)

movie_columns = [
    "movie_id", "title", "release_date", "video_release_date",
    "imdb_url", "unknown", "action", "adventure", "animation",
    "children", "comedy", "crime", "documentary", "drama",
    "fantasy", "film_noir", "horror", "musical", "mystery",
    "romance", "sci_fi", "thriller", "war", "western",
]

movies = pd.read_csv(
    MOVIES_FILE,
    sep="|",
    header=None,
    names=movie_columns,
    encoding="latin-1",
)

movies["movie_id"] = movies["movie_id"].astype(str)
ratings["user_id"] = ratings["user_id"].astype(str)
ratings["movie_id"] = ratings["movie_id"].astype(str)

print(f"Ratings loaded: {len(ratings):,}")
print(f"Movies loaded: {len(movies):,}")


# --------------------------------------------------
# 3. Train SVD
# --------------------------------------------------

reader = Reader(
    line_format="user item rating timestamp",
    sep="\t",
    rating_scale=(1, 5),
)

data = Dataset.load_from_file(
    str(RATINGS_FILE),
    reader=reader,
)

trainset = data.build_full_trainset()

model = SVD(
    n_factors=50,
    n_epochs=40,
    lr_all=0.005,
    reg_all=0.01,
    random_state=42,
)

print("Training SVD model...")
model.fit(trainset)
print("SVD training complete.")


# --------------------------------------------------
# 4. Calculate smoothed popularity scores
# --------------------------------------------------

movie_stats = ratings.groupby("movie_id")["rating"].agg(
    rating_count="count",
    mean_rating="mean",
)

global_mean = ratings["rating"].mean()
m = 20

movie_stats["popularity_score"] = (
    movie_stats["rating_count"] * movie_stats["mean_rating"]
    + m * global_mean
) / (movie_stats["rating_count"] + m)

movie_stats = movie_stats.reset_index()


# --------------------------------------------------
# 5. Save artifacts
# --------------------------------------------------

joblib.dump(model, ARTIFACT_DIR / "svd_model.joblib")
movies.to_pickle(ARTIFACT_DIR / "movies.pkl")
ratings.to_pickle(ARTIFACT_DIR / "ratings.pkl")
movie_stats.to_pickle(ARTIFACT_DIR / "movie_stats.pkl")

print("\nArtifacts saved to:", ARTIFACT_DIR)
for path in sorted(ARTIFACT_DIR.iterdir()):
    if path.is_file():
        print(f"  {path.name}: {path.stat().st_size:,} bytes")
