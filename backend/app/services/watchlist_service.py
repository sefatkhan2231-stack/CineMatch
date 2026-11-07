from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.database.models import User, Movie, Watchlist
from backend.app.services.movie_service import formate_movie

def add_to_watchlist(
        db: Session,
        user_id: int,
        movie_id: int,
)-> dict:

    user = db.get(User, user_id)
    if user is None:
        raise ValueError('User not found')

    movie = db.get(Movie, movie_id)
    if movie is None:
        raise ValueError('Movie not found')

    existing = db.scalar(
        select(Watchlist).where(
            Watchlist.user_id == user_id,
            Watchlist.movie_id == movie_id,
        )
    )

    if existing:
        return {"message": "Movie already in watchlist"}

    entry = Watchlist(
        user_id=user_id,
        movie_id=movie_id,
    )

    db.add(entry)
    db.commit()
    db.refresh(entry)

    return {
        "message": "Movie added to watchlist successfully",
        "user_id": entry.user_id,
        "movie_id": entry.movie_id,
        "added_at": entry.added_at,
    }

def get_watchlist(
        db: Session,
        user_id: int,
)-> list[dict]:

    user = db.get(User, user_id)
    if user is None:
        raise ValueError('User not found')

    statement = (
        select(Watchlist)
        .where(Watchlist.user_id == user_id)
        .order_by(Watchlist.added_at.desc())
    )

    entries = db.scalars(statement).all()

    results = []

    for entry in entries:
        movie = formate_movie(entry.movie)

        results.append({
            **movie,
            'added_at': entry.added_at,
        })

    return results

def remove_from_watchlist(
        db: Session,
        user_id: int,
        movie_id: int,
)-> dict:

    statement = select(Watchlist).where(
        Watchlist.user_id == user_id,
        Watchlist.movie_id == movie_id,
    )

    entry = db.scalar(statement)

    if entry is None:
        raise ValueError("Movie not found in watchlist")

    db.delete(entry)
    db.commit()

    return {"message": "Movie remove from watchlist successfully"}