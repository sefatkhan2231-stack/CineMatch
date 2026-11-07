from app.database.connection import Base, engine

from app.database.models import (
    User,
    Movie,
    Rating,
    Watchlist,
    MovieLensRating,
)

def create_table():
    Base.metadata.create_all(bind=engine)

    print('Dataset tables created successfully!')

    for table_name in Base.metadata.tables:
        print(f" - {table_name}")

if __name__ == "__main__":
    create_table()