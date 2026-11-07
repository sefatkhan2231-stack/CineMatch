
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.database.models import Rating, User, Movie
from backend.app.services.movie_service import formate_movie


def submit_rating(
    db: Session,
    user_id: int,
    movie_id: int,
    rating_value: float,
) -> dict:

    user = db.get(User, user_id)
    if user is None:
        raise ValueError("User not found")

    movie = db.get(Movie, movie_id)
    if movie is None:
        raise ValueError("Movie not found")

    existing_rating = db.scalar(
        select(Rating).where(
            Rating.user_id == user_id,
            Rating.movie_id == movie_id,
        )
    )

    if existing_rating:
        existing_rating.rating = rating_value
        message = "Rating updated successfully"
    else:
        existing_rating = Rating(
            user_id=user_id,
            movie_id=movie_id,
            rating=rating_value,
        )
        db.add(existing_rating)
        message = "Rating submitted successfully"

    db.commit()
    db.refresh(existing_rating)

    return {
        "message": message,
        "user_id": existing_rating.user_id,
        "movie_id": existing_rating.movie_id,
        "rating": existing_rating.rating,
    }


def get_user_ratings(db: Session, user_id: int) -> list[dict]:

    user = db.get(User, user_id)
    if user is None:
        raise ValueError("User not found")

    statement = (
        select(Rating)
        .where(Rating.user_id == user_id)
        .order_by(Rating.created_at.desc())
    )

    ratings = db.scalars(statement).all()

    results = []

    for rating in ratings:
        movie = formate_movie(rating.movie)

        results.append({
            **movie,
            "rating": rating.rating,
            "created_at": rating.created_at,
            "updated_at": rating.updated_at,
        })

    return results


def delete_rating(
    db: Session,
    user_id: int,
    movie_id: int,
) -> dict:

    statement = select(Rating).where(
        Rating.user_id == user_id,
        Rating.movie_id == movie_id,
    )

    rating = db.scalar(statement)

    if rating is None:
        raise ValueError("Rating not found")

    db.delete(rating)
    db.commit()

    return {"message": "Rating deleted successfully"}
