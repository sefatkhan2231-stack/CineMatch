from pathlib import Path
from collections import defaultdict

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from surprise import Dataset, Reader
from sklearn.model_selection import train_test_split

from evaluate_rank import evaluate_rank

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = (
    PROJECT_ROOT
    / 'ml'
    / 'data'
    / 'raw'
    / 'ml-100k'
    / 'ml-100k'
)

# --------------------------------------------------
# 1. Load movie metadata
# --------------------------------------------------

movie_columns = [
    "movie_id", "title", "release_date", "video_release_date",
    "imdb_url", "unknown", "action", "adventure", "animation",
    "children", "comedy", "crime", "documentary", "drama",
    "fantasy", "film_noir", "horror", "musical", "mystery",
    "romance", "sci_fi", "thriller", "war", "western",
]

movies = pd.read_csv(
    DATA_DIR / 'u.item',
    sep='|',
    names=movie_columns,
    encoding='latin-1',
)

genre_columns = movie_columns[6:]

movies['genres'] = movies[genre_columns].apply(
    lambda row: " ".join(
        genre for genre in genre_columns if row[genre] == 1
    ),
    axis=1,
)

# --------------------------------------------------
# 2. Build genre vectors
# --------------------------------------------------

vectorizer = TfidfVectorizer(
    tokenizer=str.split,
    preprocessor=None,
    token_pattern=None,
    lowercase=True,
)

tfidf_matrix = vectorizer.fit_transform(movies['genres'])
similarity_matrix = cosine_similarity(tfidf_matrix)

movie_id_to_index = {
    str(movie_id): index
    for index, movie_id in enumerate(movies['movie_id'])
}

# --------------------------------------------------
# 3. Recreate the final train/test split
# --------------------------------------------------

ratings_file = DATA_DIR / 'u.data'

reader = Reader(
    line_format='user item rating timestamp',
    sep='\t',
    rating_scale=(1, 5),
)

data = Dataset.load_from_file(
    str(ratings_file),
    reader=reader,
)

dev_raw, test_raw = train_test_split(
    data.raw_ratings,
    test_size=0.20,
    random_state=42,
)

train_raw, val_raw = train_test_split(
    dev_raw,
    test_size=0.20,
    random_state=43,
)

trainset_full = data.construct_trainset(train_raw + val_raw)
testset = data.construct_testset(test_raw)

train_rows = [
    (
        trainset_full.to_raw_uid(uid),
        trainset_full.to_raw_iid(iid),
        rating,
    )
    for uid, iid, rating in trainset_full.all_ratings()
]

train_seen = defaultdict(set)
user_ratings = defaultdict(set)
train_movie_ids = set()

for user_id, movie_id, rating in train_rows:
    train_seen[user_id].add(movie_id)
    train_movie_ids.add(movie_id)
    user_ratings[user_id].add((movie_id, rating))

train_movie_ids = sorted(
    movie_id
    for movie_id in train_movie_ids
    if movie_id in movie_id_to_index
)

# --------------------------------------------------
# 4. Create user profiles from training ratings
# --------------------------------------------------

def score_movie(user_id, candidate_movie_id):

    profile_items = [
        (movie_id, rating)
        for movie_id, rating in user_ratings[user_id]
        if rating >= 4 and movie_id in movie_id_to_index
    ]

    candidate_index = movie_id_to_index.get(candidate_movie_id)

    if candidate_index is None or not profile_items:
        return 0.0

    indices = [
        movie_id_to_index[movie_id]
        for movie_id, _ in profile_items
    ]

    weights = np.array(
        [rating - 3 for _, rating in profile_items],
        dtype=float,
    )

    similarities = similarity_matrix[indices, candidate_index]

    return float(np.average(similarities, weights=weights))

# --------------------------------------------------
# 5. Evaluate ranking performance
# --------------------------------------------------

results = evaluate_rank(
    testset=testset,
    train_seen=train_seen,
    train_movie_ids=train_movie_ids,
    score_movies=score_movie,
    k=10
)

print(f"Training ratings: {trainset_full.n_ratings:,}")
print(f"Reserved test ratings: {len(testset):,}")
print("\nContent-based test results (K=10)")
print(f"Users evaluated: {results['users_evaluated']:,}")
print(f"Precision@10: {results['precision@10']:.4f}")
print(f"Recall@10:    {results['recall@10']:.4f}")
print(f"NDCG@10:      {results['ndcg@10']:.4f}")