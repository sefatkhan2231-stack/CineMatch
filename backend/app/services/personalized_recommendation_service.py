from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from backend.app.database.models import Rating, User, Movie

def get_user_rating_history(
        db: Session,
        user_id: int,
)-> list[dict]:

    user = db.get(User, user_id)

    if user is None:
        raise ValueError('User not found')

    statement = (
        select(Rating)
        .options(joinedload(Rating.movie))
        .where(Rating.user_id == user_id)
        .order_by(Rating.created_at.desc())
    )

    ratings = db.scalars(statement).all()

    return [
        {
            'movie_id': rating.movie_id,
            'title': rating.movie.title,
            'genres': rating.movie.genres or [],
            'rating': float(rating.rating),
        }
        for rating in ratings
    ]

def calculate_genre_preferences(
        rating_history: list[dict],
)-> dict[str, float]:

    genre_scores = {}

    for item in rating_history:
        rating = item['rating']
        genres = item['genres']

        for genre in genres:
            if genre not in genre_scores:
                genre_scores[genre] = []

            genre_scores[genre].append(rating - 3.0)

    return {
        genre: round(sum(scores) / len(scores), 4)
        for genre, scores in genre_scores.items()
    }

def calculate_movie_genre_score(
        movie_genres: list[str],
        genre_preferences: dict[str, float],
)-> float:

    matching_scores = [
        genre_preferences[genre]
        for genre in movie_genres
        if genre in genre_preferences
    ]

    if not matching_scores:
        return 0.5

    average_preference = sum(matching_scores) / len(matching_scores)

    score = (average_preference + 2.0) / 4.0

    return round(score, 4)

import pandas as pd

MIN_RATINGS = 10


def build_popularity_lookup(movie_stats: pd.DataFrame) -> dict[str, float]:

    eligible_movies = movie_stats[
        movie_stats["rating_count"] >= MIN_RATINGS
    ].copy()

    if eligible_movies.empty:
        return {}

    min_score = eligible_movies["popularity_score"].min()
    max_score = eligible_movies["popularity_score"].max()

    score_range = max_score - min_score

    if score_range == 0:
        eligible_movies["normalized_popularity"] = 0.5
    else:
        eligible_movies["normalized_popularity"] = (
            eligible_movies["popularity_score"] - min_score
        ) / score_range

    return {
        str(row.movie_id): round(float(row.normalized_popularity), 4)
        for row in eligible_movies.itertuples()
    }

def calculate_hybrid_score(
        genre_score: float,
        popularity_score: float,
)-> float:

    genre_weight = 0.60
    popularity_weight = 0.40

    return round(
        (genre_weight * genre_score)
        + (popularity_weight * popularity_score),
        4,
    )

def get_personalized_recommendations(
    db: Session,
    user_id: int,
    popularity_lookup: dict[str, float],
    limit: int = 12,
) -> list[dict]:

    if limit < 1:
        raise ValueError("Limit must be greater than zero.")

    # 1. Retrieve the user's rating history.
    rating_history = get_user_rating_history(db, user_id)

    # 2. Identify movies the user has already rated.
    rated_movie_ids = {
        str(item["movie_id"])
        for item in rating_history
    }

    # 3. Calculate genre preferences if rating history exists.
    genre_preferences = (
        calculate_genre_preferences(rating_history)
        if rating_history
        else {}
    )

    # 4. Retrieve movies from PostgreSQL.
    movies = db.scalars(select(Movie)).all()

    recommendations = []

    for movie in movies:
        movie_id = str(movie.movie_id)

        # Skip movies without eligible popularity data.
        if movie_id not in popularity_lookup:
            continue

        # Skip movies already rated by this user.
        if movie_id in rated_movie_ids:
            continue

        popularity_score = popularity_lookup[movie_id]

        # 5. Choose the scoring strategy.
        if rating_history:
            genre_score = calculate_movie_genre_score(
                movie.genres or [],
                genre_preferences,
            )

            final_score = calculate_hybrid_score(
                genre_score,
                popularity_score,
            )

            recommendation_type = "personalized"

        else:
            # Cold-start user: rely on popularity.
            genre_score = None
            final_score = popularity_score
            recommendation_type = "popular"

        # 6. Prepare the recommendation.
        recommendations.append({
            "movie_id": movie.movie_id,
            "title": movie.title,
            "genres": movie.genres or [],
            "release_date": movie.release_date,
            "poster_url": movie.poster_url,
            "genre_score": genre_score,
            "popularity_score": popularity_score,
            "recommendation_score": final_score,
            "recommendation_type": recommendation_type,
        })

    # 7. Rank by recommendation score.
    recommendations.sort(
        key=lambda item: (
            item["recommendation_score"],
            item["popularity_score"],
        ),
        reverse=True,
    )

    return recommendations[:limit]