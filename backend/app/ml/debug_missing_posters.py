from backend.app.ml.fetch_movie_posters import (
    build_session,
    get_search_titles,
    search_tmdb,
    display_title,
    extract_year,
)

from backend.app.database.connection import SessionLocal
from backend.app.database.models import Movie
from sqlalchemy import select


MOVIE_IDS = [75, 510, 1235, 1359, 1410, 1420, 1564]


def main():
    session = build_session()
    db = SessionLocal()

    try:
        movies = db.scalars(
            select(Movie)
            .where(Movie.movie_id.in_(MOVIE_IDS))
            .order_by(Movie.movie_id)
        ).all()

        for movie in movies:
            print("\n" + "=" * 70)
            print(f"ID: {movie.movie_id}")
            print(f"TITLE: {movie.title}")
            print(f"YEAR: {movie.release_date}")

            for query in get_search_titles(movie.title):
                for media_type in ("movie", "tv"):
                    results = search_tmdb(
                        session, query, media_type
                    )

                    print(
                        f"\nQUERY: {query} | TYPE: {media_type}"
                    )

                    for result in results[:10]:
                        date = (
                            result.get("release_date")
                            or result.get("first_air_date")
                        )

                        print(
                            f"  ID: {result.get('id')} | "
                            f"TITLE: {display_title(result)} | "
                            f"YEAR: {extract_year(date)} | "
                            f"POSTER: {bool(result.get('poster_path'))}"
                        )

    finally:
        db.close()
        session.close()


if __name__ == "__main__":
    main()