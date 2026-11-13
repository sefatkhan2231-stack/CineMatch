from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models import Movie

def formate_movie(movie: Movie) -> dict:
    return {
        "movie_id": str(movie.movie_id),
        "title": movie.title,
        "genres": movie.genres or [],
        "release_date": movie.release_date,
        "poster_url": movie.poster_url,
    }

def search_movies_db(
        db: Session,
        query: str,
        limit: int = 10,
) -> list[dict]:

    query = query.strip()

    if not query:
        return []

    statement = (
        select(Movie)
        .where(Movie.title.ilike(f"%{query}%", escape="\\"))
        .order_by(Movie.title)
        .limit(limit)
    )

    movies = db.scalars(statement).all()

    return [formate_movie(movie) for movie in movies]

def get_movie_db(
        db: Session,
        movie_id: int,
) -> dict | None:

    movie = db.get(Movie, movie_id)

    if movie is None:
        return None

    return formate_movie(movie)