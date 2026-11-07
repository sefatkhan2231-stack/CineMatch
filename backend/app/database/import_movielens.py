
from pathlib import Path

import pandas as pd
from sqlalchemy import text

from backend.app.database.connection import SessionLocal
from backend.app.database.models import Movie, MovieLensRating


# --------------------------------------------------
# 1. Paths and configuration
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[3]

DATA_DIR = (
    PROJECT_ROOT
    / "ml"
    / "data"
    / "raw"
    / "ml-100k"
    / "ml-100k"
)

RATINGS_FILE = DATA_DIR / "u.data"
MOVIES_FILE = DATA_DIR / "u.item"

GENRE_COLUMNS = [
    "unknown", "action", "adventure", "animation",
    "children", "comedy", "crime", "documentary",
    "drama", "fantasy", "film_noir", "horror",
    "musical", "mystery", "romance", "sci_fi",
    "thriller", "war", "western",
]

MOVIE_COLUMNS = [
    "movie_id", "title", "release_date", "video_release_date",
    "imdb_url", *GENRE_COLUMNS,
]


# --------------------------------------------------
# 2. Load MovieLens files
# --------------------------------------------------

def load_dataset():
    if not RATINGS_FILE.exists():
        raise FileNotFoundError(f"Missing ratings file: {RATINGS_FILE}")

    if not MOVIES_FILE.exists():
        raise FileNotFoundError(f"Missing movies file: {MOVIES_FILE}")

    movies_df = pd.read_csv(
        MOVIES_FILE,
        sep="|",
        header=None,
        names=MOVIE_COLUMNS,
        encoding="latin-1",
    )

    ratings_df = pd.read_csv(
        RATINGS_FILE,
        sep="\t",
        names=["user_id", "movie_id", "rating", "timestamp"],
    )

    return movies_df, ratings_df


# --------------------------------------------------
# 3. Convert movie data
# --------------------------------------------------

def prepare_movies(movies_df):
    records = []

    for _, row in movies_df.iterrows():
        genres = [
            genre
            for genre in GENRE_COLUMNS
            if row[genre] == 1
        ]

        release_date = None

        if pd.notna(row["release_date"]):
            release_date = pd.to_datetime(
                row["release_date"],
                errors="coerce",
            )

            if pd.isna(release_date):
                release_date = None
            else:
                release_date = release_date.date()

        records.append({
            "movie_id": str(row["movie_id"]),
            "title": row["title"],
            "release_date": release_date,
            "genres": genres,
            "poster_url": None,
        })

    return records


# --------------------------------------------------
# 4. Convert rating data
# --------------------------------------------------

def prepare_ratings(ratings_df):
    records = []

    for _, row in ratings_df.iterrows():
        records.append({
            "movielens_user_id": int(row["user_id"]),
            "movie_id": str(row["movie_id"]),
            "rating": int(row["rating"]),
            "timestamp": int(row["timestamp"]),
        })

    return records


# --------------------------------------------------
# 5. Import into PostgreSQL
# --------------------------------------------------

def import_data():
    movies_df, ratings_df = load_dataset()

    movie_records = prepare_movies(movies_df)
    rating_records = prepare_ratings(ratings_df)

    print(f"Movies prepared: {len(movie_records):,}")
    print(f"Ratings prepared: {len(rating_records):,}")

    db = SessionLocal()

    try:
        # Insert movies first because ratings reference movies.
        db.execute(
            text("""
                INSERT INTO movies
                    (movie_id, title, release_date, genres, poster_url)
                VALUES
                    (:movie_id, :title, :release_date,
                     CAST(:genres AS JSONB), :poster_url)
                ON CONFLICT (movie_id) DO UPDATE SET
                    title = EXCLUDED.title,
                    release_date = EXCLUDED.release_date,
                    genres = EXCLUDED.genres
            """),
            [
                {
                    **record,
                    "genres": __import__("json").dumps(record["genres"]),
                }
                for record in movie_records
            ],
        )

        print("Movie catalog imported.")

        # Import original MovieLens ratings separately.
        db.execute(
            text("""
                INSERT INTO movielens_ratings
                    (movielens_user_id, movie_id, rating, timestamp)
                VALUES
                    (:movielens_user_id, :movie_id, :rating, :timestamp)
                ON CONFLICT (movielens_user_id, movie_id) DO NOTHING
            """),
            rating_records,
        )

        db.commit()

        print("MovieLens ratings imported.")
        print("Import completed successfully!")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    import_data()
