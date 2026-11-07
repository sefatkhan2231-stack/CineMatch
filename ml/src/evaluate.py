from pathlib import Path

from surprise import Dataset, KNNWithMeans, SVD, accuracy, Reader, NMF
from surprise.model_selection import train_test_split

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = (
    PROJECT_ROOT
    / 'ml'
    / 'data'
    / 'raw'
    / 'ml-100k'
    / 'ml-100k'
)

ratings_file = DATA_DIR / 'u.data'

reader = Reader(
    line_format='user item rating timestamp',
    sep='\t',
    rating_scale=(1, 5),
)

data = Dataset.load_from_file(
    ratings_file,
    reader=reader,
)

trainset, testset = train_test_split(
    data,
    test_size=0.20,
    random_state=42,
)

print(f"Training ratings: {trainset.n_ratings:,}")
print(f"Test ratings: {len(testset):,}")

models = {
    "KNNWithMeans": KNNWithMeans(
        k=40,
        min_k=2,
        sim_options={
            "name": "cosine",
            "user_based": True,
            "min_support": 2,
        },
        verbose=False,
    ),
    "SVD": SVD(
        n_factors=50,
        n_epochs=20,
        lr_all=0.005,
        reg_all=0.02,
        random_state=42,
    ),
    "NMF": NMF(
        n_factors=50,
        n_epochs=20,
        random_state=42,
    ),
}

results = []

for name, model in models.items():
    print(f"\nTraining {name}...")
    model.fit(trainset)

    predictions = model.test(testset)

    rmse = accuracy.rmse(predictions, verbose=False)
    mae = accuracy.mae(predictions, verbose=False)

    results.append({
        'Model': name,
        'RMSE': rmse,
        'MAE': mae,
    })

print("\n" + "=" * 45)
print("MODEL COMPARISON")
print("=" * 45)

for result in sorted(results, key=lambda item: item["RMSE"]):
    print(
        f"{result['Model']:<15} "
        f"RMSE: {result['RMSE']:.4f} | "
        f"MAE: {result['MAE']:.4f}"
    )

print("\nLower RMSE and MAE indicate better rating predictions.")