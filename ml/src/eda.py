
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "ml" / "data" / "raw" / "ml-100k" / "ml-100k"

RATINGS_FILE = DATA_DIR / "u.data"
MOVIES_FILE = DATA_DIR / "u.item"

ratings = pd.read_csv(
    RATINGS_FILE,
    sep="\t",
    names=["user_id", "movie_id", "rating", "timestamp"],
    encoding="latin-1",
)

movie_columns = [
    "movie_id",
    "title",
    "release_date",
    "video_release_date",
    "imdb_url",
    "unknown",
    "action",
    "adventure",
    "animation",
    "children",
    "comedy",
    "crime",
    "documentary",
    "drama",
    "fantasy",
    "film_noir",
    "horror",
    "musical",
    "mystery",
    "romance",
    "sci_fi",
    "thriller",
    "war",
    "western",
]

movies = pd.read_csv(
    MOVIES_FILE,
    sep="|",
    names=movie_columns,
    encoding="latin-1",
)

print("\n========== DATASET OVERVIEW ==========")
print(f"Ratings rows: {len(ratings):,}")
print(f"Unique users: {ratings['user_id'].nunique():,}")
print(f"Unique rated movies: {ratings['movie_id'].nunique():,}")
print(f"Movies in metadata: {movies['movie_id'].nunique():,}")

print("\n========== RATINGS DATA ==========")
print(ratings.head())
print("\nData types:")
print(ratings.dtypes)
print("\nMissing values:")
print(ratings.isnull().sum())
print(f"\nDuplicate rating records: {ratings.duplicated().sum():,}")

print("\n========== RATING DISTRIBUTION ==========")
print(ratings["rating"].value_counts().sort_index())
print(f"\nAverage rating: {ratings['rating'].mean():.2f}")
print(f"Minimum rating: {ratings['rating'].min()}")
print(f"Maximum rating: {ratings['rating'].max()}")

print("\n========== MOVIE METADATA ==========")
print(movies[["movie_id", "title", "release_date"]].head())
print(f"\nMissing movie titles: {movies['title'].isna().sum():,}")

ratings_with_movies = ratings.merge(
    movies[["movie_id", "title"]],
    on="movie_id",
    how="left",
    validate="many_to_one",
)

print("\n========== MOST-RATED MOVIES ==========")
most_rated = (
    ratings_with_movies.groupby("title")
    .agg(
        rating_count=("rating", "size"),
        average_rating=("rating", "mean"),
    )
    .sort_values("rating_count", ascending=False)
    .head(10)
)

print(most_rated.round(2).to_string())

print("\n========== EDA COMPLETE ==========")
