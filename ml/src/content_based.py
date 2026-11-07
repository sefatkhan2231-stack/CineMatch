from pathlib import Path

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# --------------------------------------------------
# 1. Load the MovieLens data
# --------------------------------------------------

PROJECT_DATA = Path(__file__).resolve().parents[2]

DATA_DIR = (
    PROJECT_DATA
    / 'ml'
    / 'data'
    / 'raw'
    / 'ml-100k'
    / 'ml-100k'
)

movie_columns = [
    "movie_id",
    "title",
    "release_date",
    "video_release_date",
    "imdb_url",
    "unknown",
    "action",
    "adventure",
    "animation",
    "children",
    "comedy",
    "crime",
    "documentary",
    "drama",
    "fantasy",
    "film_noir",
    "horror",
    "musical",
    "mystery",
    "romance",
    "sci_fi",
    "thriller",
    "war",
    "western",
]

movies = pd.read_csv(
    DATA_DIR / 'u.item',
    sep='|',
    names=movie_columns,
    encoding='latin-1',
)

genre_columns = movie_columns[6:]

# --------------------------------------------------
# 2. Convert genre indicators into readable text
# --------------------------------------------------

def extract_genres(movie):
    return " ".join(
        genre
        for genre in genre_columns
        if movie[genre] == 1
    )

movies['genres'] = movies.apply(extract_genres, axis=1)

# movies['content'] = (
#     movies['title'].fillna("").str.replace(r'\s+', ' ', regex=True)
#     + ' '
#     + movies['genres']
# )

# --------------------------------------------------
# 3. Convert text into TF-IDF vectors
# --------------------------------------------------

# vectorizer = TfidfVectorizer(
#     stop_words='english',
#     token_pattern=r"(?u)\b\w+\b",
# )
vectorizer = TfidfVectorizer(
    tokenizer=str.split,
    preprocessor=None,
    token_pattern=None,
    lowercase=True,
)

tfidf_matrix = vectorizer.fit_transform(movies['genres'])

similarity_matrix = cosine_similarity(tfidf_matrix)

print(f"Movies loaded: {len(movies):,}")
print(f"TF-IDF matrix shape: {tfidf_matrix.shape}")
print(f"Similarity matrix shape: {similarity_matrix.shape}")

# --------------------------------------------------
# 4. Recommend similar movies
# --------------------------------------------------

def recommend_movies(movie_title, top_n=10):
    matches = movies[
        movies['title'].str.casefold()
        == movie_title.strip().casefold()
    ]

    if matches.empty:
        print(f"\nMovie not found: {movie_title}")
        print("Try copying a title from the MovieLens dataset.")
        return

    movie_index = matches.index[0]

    scores = similarity_matrix[movie_index]

    ranked_indices = scores.argsort()[::-1]

    ranked_indices = [
        idx for idx in ranked_indices
        if idx != movie_index
    ][:top_n]

    print(f"\nRecommendations for: {movies.loc[movie_index, 'title']}")
    print(f"Genres: {movies.loc[movie_index, 'genres']}")
    print("-" * 65)

    for rank, idx in enumerate(ranked_indices, start=1):
        recommended = movies.iloc[idx]

        print(
            f"{rank:2}. {recommended['title']:<40} "
            f"Similarity: {scores[idx]:.3f}"
        )

# --------------------------------------------------
# 5. Test the model
# --------------------------------------------------

if __name__ == "__main__":
    recommend_movies("Star Wars (1977)", top_n=10)
    recommend_movies("Toy Story (1995)", top_n=10)