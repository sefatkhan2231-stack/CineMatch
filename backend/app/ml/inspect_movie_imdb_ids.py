
from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[3]

ITEM_FILE = (
    PROJECT_ROOT
    / "ml"
    / "data"
    / "raw"
    / "ml-100k"
    / "ml-100k"
    / "u.item"
)

MOVIE_IDS = [75, 510, 1235, 1359, 1410, 1420, 1564]

df = pd.read_csv(
    ITEM_FILE,
    sep="|",
    encoding="latin-1",
    header=None,
    usecols=[0, 1, 4],
    names=["movie_id", "title", "imdb_url"],
)

df = df[df["movie_id"].isin(MOVIE_IDS)].copy()

df["imdb_id"] = df["imdb_url"].str.extract(
    r"(tt\d+)"
)

print(df.to_string(index=False))
