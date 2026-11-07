
from sqlalchemy import text

from app.database.connection import engine

try:
    with engine.connect() as connection:
        result = connection.execute(
            text("SELECT current_database(), version()")
        )
        database_name, postgres_version = result.one()

        print("PostgreSQL connection successful!")
        print(f"Database: {database_name}")
        print(f"PostgreSQL: {postgres_version}")

except Exception as exc:
    print("PostgreSQL connection failed.")
    print(f"Error: {exc}")
    raise
