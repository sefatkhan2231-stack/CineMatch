
from backend.app.database.connection import SessionLocal
from backend.app.services.personalized_recommendation_service import (
    get_user_rating_history,
    calculate_genre_preferences,
    calculate_movie_genre_score,
    build_popularity_lookup,
    calculate_hybrid_score,
    get_personalized_recommendations,
)

db = SessionLocal()

try:
    user_id = 3

    ratings = get_user_rating_history(db, user_id)

    print(f"Total ratings: {len(ratings)}")

    for rating in ratings:
        print(rating)

    preferences = calculate_genre_preferences(ratings)

    print("\nGenre preferences:")

    for genre, score in preferences.items():
        print(f"{genre}: {score}")

    print("\nMovie genre scores:")

    test_movies = [
        {
            "title": "Drama movie",
            "genres": ["drama"],
        },
        {
            "title": "Animation comedy movie",
            "genres": ["animation", "comedy"],
        },
        {
            "title": "Drama comedy movie",
            "genres": ["drama", "comedy"],
        },
    ]

    for movie in test_movies:
        score = calculate_movie_genre_score(
            movie["genres"],
            preferences,
        )
        print(f'{movie["title"]}: {score}')
        

finally:
    db.close()


import joblib
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_DIR = PROJECT_ROOT / "ml" / "artifacts"

movie_stats = joblib.load(ARTIFACT_DIR / "movie_stats.pkl")

print("\nPopularity artifact:")
print("Shape:", movie_stats.shape)
print("Columns:", movie_stats.columns.tolist())
print("\nFirst 5 rows:")
print(movie_stats.head())

print("\nNumeric column ranges:")
print(movie_stats.select_dtypes(include="number").describe())

popularity_lookup = build_popularity_lookup(movie_stats)

print("\nNormalized popularity:")
print("Eligible movies:", len(popularity_lookup))

print("Lowest score:", min(popularity_lookup.values()))
print("Highest score:", max(popularity_lookup.values()))

print("\nSample popularity scores:")
for movie_id, score in list(popularity_lookup.items())[:5]:
    print(f"Movie ID {movie_id}: {score}")

print("\nHybrid recommendation scores:")

test_cases = [
    ("Drama movie", 1.0, 0.7332),
    ("Animation comedy movie", 0.0, 0.7332),
    ("Drama comedy movie", 0.5, 0.7332),
]

for title, genre_score, popularity_score in test_cases:
    final_score = calculate_hybrid_score(
        genre_score,
        popularity_score,
    )
    print(f"{title}: {final_score}")

recommendations = get_personalized_recommendations(
    db=db,
    user_id=user_id,
    popularity_lookup=popularity_lookup,
    limit=10,
)

print("\nPersonalized recommendations:")

for index, movie in enumerate(recommendations, start=1):
    print(
        f'{index}. {movie["title"]} | '
        f'Genre: {movie["genre_score"]} | '
        f'Popularity: {movie["popularity_score"]} | '
        f'Final: {movie["recommendation_score"]}'
    )

print("\nRecommendation validation:")

recommended_ids = {
    str(movie["movie_id"])
    for movie in recommendations
}

print("Recommendation count:", len(recommendations))

print(
    "Rated movies excluded:",
    not recommended_ids.intersection({"1", "6"})
)

print(
    "All recommendations personalized:",
    all(
        movie["recommendation_type"] == "personalized"
        for movie in recommendations
    )
)

scores = [
    movie["recommendation_score"]
    for movie in recommendations
]

print(
    "Correctly sorted:",
    scores == sorted(scores, reverse=True)
)