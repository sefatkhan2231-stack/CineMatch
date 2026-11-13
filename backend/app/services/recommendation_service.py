
from pathlib import Path

import joblib
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[3]
ARTIFACT_DIR = PROJECT_ROOT / "ml" / "artifacts"

SVD_WEIGHT = 0.25
POPULARITY_WEIGHT = 0.75
MIN_RATINGS = 10


class RecommendationService:
    def __init__(self):
        self.model = joblib.load(ARTIFACT_DIR / "svd_model.joblib")
        self.movies = pd.read_pickle(ARTIFACT_DIR / "movies.pkl")
        self.ratings = pd.read_pickle(ARTIFACT_DIR / "ratings.pkl")
        self.movie_stats = pd.read_pickle(
            ARTIFACT_DIR / "movie_stats.pkl"
        )

        self.movies["movie_id"] = self.movies["movie_id"].astype(str)
        self.ratings["user_id"] = self.ratings["user_id"].astype(str)
        self.ratings["movie_id"] = self.ratings["movie_id"].astype(str)
        self.movie_stats["movie_id"] = (
            self.movie_stats["movie_id"].astype(str)
        )

        self.movies["genres"] = self.movies.apply(
            self._extract_genres,
            axis=1,
        )

        self.movie_lookup = self.movies.set_index("movie_id").to_dict(
            orient="index"
        )

        self.rating_counts = self.ratings.groupby("movie_id").size()

        # Precompute the genres for each movie.
        self.genre_sets = {
            row.movie_id: set(row.genres.split())
            for row in self.movies.itertuples()
        }

        # Keep only movies with enough ratings for recommendations.
        self.eligible_movie_ids = set(
            self.movie_stats.loc[
                self.movie_stats["rating_count"] >= MIN_RATINGS,
                "movie_id",
            ]
        )

        self.popularity_lookup = self.movie_stats.set_index(
            "movie_id"
        )["popularity_score"].to_dict()

        print("Recommendation service loaded.")

    @staticmethod
    def _extract_genres(movie):
        genre_columns = [
            "unknown", "action", "adventure", "animation", "children",
            "comedy", "crime", "documentary", "drama", "fantasy",
            "film_noir", "horror", "musical", "mystery", "romance",
            "sci_fi", "thriller", "war", "western",
        ]
        return " ".join(
            genre
            for genre in genre_columns
            if movie[genre] == 1
        )

    @staticmethod
    def _normalize(values):
        values = pd.Series(values, dtype=float)
        low = values.min()
        high = values.max()

        if high == low:
            return [0.0] * len(values)

        return ((values - low) / (high - low)).tolist()

    def search_movies(self, query, limit=10):
        query = query.strip().casefold()

        if not query:
            return []

        matches = self.movies[
            self.movies["title"].str.casefold().str.contains(
                query,
                regex=False,
                na=False,
            )
        ].head(limit)

        return [
            self._movie_response(row.movie_id)
            for row in matches.itertuples()
        ]

    def _movie_response(self, movie_id):
        movie = self.movie_lookup.get(str(movie_id))

        if not movie:
            return None

        genres = [
            genre for genre in movie["genres"].split()
        ]

        return {
            "movie_id": str(movie_id),
            "title": movie["title"],
            "genres": genres,
            "poster_url": movie.get("poster_url"),
            "release_date": (
                None
                if pd.isna(movie["release_date"])
                else str(movie["release_date"])
            ),
        }

    def recommend_for_user(self, user_id, limit=10):
        user_id = str(user_id)

        known_users = set(self.ratings["user_id"])
        if user_id not in known_users:
            raise ValueError(f"Unknown user_id: {user_id}")

        seen = set(
            self.ratings.loc[
                self.ratings["user_id"] == user_id,
                "movie_id",
            ]
        )

        candidates = sorted(
            self.eligible_movie_ids - seen
        )

        if not candidates:
            return []

        svd_scores = [
            self.model.predict(user_id, movie_id).est
            for movie_id in candidates
        ]
        popularity_scores = [
            self.popularity_lookup[movie_id]
            for movie_id in candidates
        ]

        svd_normalized = self._normalize(svd_scores)
        popularity_normalized = self._normalize(popularity_scores)

        ranked = []
        for movie_id, svd_score, pop_score in zip(
            candidates,
            svd_normalized,
            popularity_normalized,
        ):
            hybrid_score = (
                SVD_WEIGHT * svd_score
                + POPULARITY_WEIGHT * pop_score
            )

            ranked.append({
                "movie_id": movie_id,
                "hybrid_score": round(hybrid_score, 6),
                "predicted_rating": round(
                    self.model.predict(user_id, movie_id).est,
                    3,
                ),
            })

        ranked.sort(
            key=lambda item: item["hybrid_score"],
            reverse=True,
        )

        results = []
        for item in ranked[:limit]:
            movie = self._movie_response(item["movie_id"])
            if movie:
                results.append({**movie, **item})

        return results

    def similar_movies(self, movie_id, limit=10):
        movie_id = str(movie_id)

        if movie_id not in self.genre_sets:
            raise ValueError(f"Unknown movie_id: {movie_id}")

        target_genres = self.genre_sets[movie_id]
        if not target_genres:
            return []

        scores = []
        for candidate_id, candidate_genres in self.genre_sets.items():
            if candidate_id == movie_id or not candidate_genres:
                continue

            intersection = len(target_genres & candidate_genres)
            union = len(target_genres | candidate_genres)
            similarity = intersection / union if union else 0.0

            if similarity > 0:
                scores.append({
                    "movie_id": int(candidate_id),
                    "similarity": round(similarity, 4),
                })

        scores.sort(
            key=lambda item: item["similarity"],
            reverse=True,
        )

        return scores[:limit]


service = RecommendationService()
