
from pathlib import Path

import pandas as pd
from surprise import Dataset, KNNWithMeans, Reader

# --------------------------------------------------
# 1. Locate and load the data
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATA_DIR = (
    PROJECT_ROOT
    / "ml"
    / "data"
    / "raw"
    / "ml-100k"
    / "ml-100k"
)

ratings_file = DATA_DIR / "u.data"
movies_file = DATA_DIR / "u.item"

ratings = pd.read_csv(
    ratings_file,
    sep="\t",
    names=["user_id", "movie_id", "rating", "timestamp"],
)

movies = pd.read_csv(
    movies_file,
    sep="|",
    header=None,
    usecols=[0, 1],
    names=["movie_id", "title"],
    encoding="latin-1",
)

# --------------------------------------------------
# 2. Build the Surprise training dataset
# --------------------------------------------------

reader = Reader(
    line_format="user item rating timestamp",
    sep="\t",
    rating_scale=(1, 5),
)

data = Dataset.load_from_file(
    str(ratings_file),
    reader=reader,
)

trainset = data.build_full_trainset()

print(f"Users: {trainset.n_users:,}")
print(f"Movies: {trainset.n_items:,}")
print(f"Ratings: {trainset.n_ratings:,}")

# --------------------------------------------------
# 3. Train user-based collaborative filtering
# --------------------------------------------------

similarity_options = {
    "name": "cosine",
    "user_based": True,
    "min_support": 2,
}

model = KNNWithMeans(
    k=40,
    min_k=1,
    sim_options=similarity_options,
    verbose=False,
)

model.fit(trainset)

print("\nCollaborative filtering model trained!")

# --------------------------------------------------
# 4. Recommend unseen movies for a user
# --------------------------------------------------


def recommend_movies(user_id, top_n=10):
    user_id = str(user_id)

    try:
        trainset.to_inner_uid(user_id)
    except ValueError:
        print(f"User {user_id} was not found.")
        return

    seen_movies = set(
        ratings.loc[
            ratings["user_id"].astype(str) == user_id,
            "movie_id",
        ].astype(str)
    )

    movie_counts = ratings.groupby("movie_id").size()

    candidates = movies[
        ~movies["movie_id"].astype(str).isin(seen_movies)
    ].copy()

    candidates["rating_count"] = (
        candidates["movie_id"]
        .map(movie_counts)
        .fillna(0)
        .astype(int)
    )

    candidates = candidates[
        candidates["rating_count"] >= 10
    ].copy()

    print(f"Eligible unseen movies: {len(candidates)}")
    print(
        "Movies below 10 ratings remaining:",
        int((candidates["rating_count"] < 10).sum()),
    )

    predictions = []

    for row in candidates.itertuples(index=False):
        prediction = model.predict(user_id, str(row.movie_id))

        predictions.append({
            "movie_id": row.movie_id,
            "title": row.title,
            "predicted_rating": prediction.est,
            "actual_k": prediction.details.get("actual_k", 0),
            "rating_count": row.rating_count,
        })

    results = pd.DataFrame(predictions)

    results = results.sort_values(
        by="predicted_rating",
        ascending=False,
    ).head(top_n)

    print(f"\nRecommendations for user {user_id}")
    print("-" * 85)

    if results.empty:
        print("No recommendations available.")
        return

    print(
        results.to_string(
            index=False,
            formatters={
                "predicted_rating": "{:.4f}".format,
            },
        )
    )

    print("\nPrediction summary:")
    print(
        "Mean predicted rating:",
        f"{results['predicted_rating'].mean():.3f}",
    )
    print(
        "Minimum movie rating count:",
        results["rating_count"].min(),
    )



# --------------------------------------------------
# 5. Test the model
# --------------------------------------------------

if __name__ == "__main__":
    recommend_movies(user_id=196, top_n=10)
