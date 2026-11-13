import argparse
import csv
import json
import os
import re
import time
import unicodedata
from difflib import SequenceMatcher
from pathlib import Path

import requests
from dotenv import load_dotenv
from requests.adapters import HTTPAdapter
from sqlalchemy import select
from urllib3.util.retry import Retry

from app.database.connection import SessionLocal
from app.database.models import Movie


# --------------------------------------------------
# Configuration
# --------------------------------------------------

load_dotenv()

TMDB_BASE_URL = "https://api.themoviedb.org/3"
IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w500"

ACCEPT_SCORE = 0.85      # minimum score to auto-accept
MIN_GAP = 0.05           # best must beat runner-up by this much
YEAR_PENALTY = 0.03      # score lost per year of difference
MAX_YEAR_PENALTY_YEARS = 10
NO_YEAR_PENALTY = 0.05   # when either side has no year

REQUEST_DELAY = 0.25
COMMIT_EVERY = 50

OVERRIDES_FILE = Path("poster_overrides.json")
REVIEW_FILE = Path("poster_review.csv")

ARTICLES = (
    "the", "a", "an",
    "le", "la", "les",
    "il", "lo", "gli",
    "el", "los", "las",
    "das", "der", "die",
)

IMDB_ID_OVERRIDES = {
}


# --------------------------------------------------
# HTTP session (with retries)
# --------------------------------------------------

def build_session() -> requests.Session:
    token = os.getenv("TMDB_API_READ_ACCESS_TOKEN")

    if not token:
        raise ValueError("TMDB API token missing from .env")

    session = requests.Session()

    retry_strategy = Retry(
        total=5,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
        respect_retry_after_header=True,
    )

    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    session.headers.update({
        "Authorization": f"Bearer {token}",
        "accept": "application/json",
    })

    return session


# --------------------------------------------------
# Title helpers
# --------------------------------------------------

def normalize_title(title: str) -> str:
    title = re.sub(r"\s*\(\d{4}\)\s*$", "", title or "")

    title = unicodedata.normalize("NFKD", title)
    title = "".join(c for c in title if not unicodedata.combining(c))

    title = title.lower()
    return re.sub(r"[^a-z0-9]", "", title)


def reorder_article(title: str) -> str:
    """'Sixth Man, The' -> 'The Sixth Man'."""
    match = re.match(r"^(.+),\s*([A-Za-z]+)$", title.strip())

    if match and match.group(2).lower() in ARTICLES:
        return f"{match.group(2)} {match.group(1)}"

    return title.strip()


def extract_year(value) -> int | None:
    if not value:
        return None

    match = re.search(r"\b(?:19|20)\d{2}\b", str(value))
    return int(match.group()) if match else None


def get_search_titles(title: str) -> list[str]:
    """
    Build search variations from a messy title such as
    'Boot, Das (Das Boot) (1981)'.
    """
    clean = re.sub(r"\s*\(\d{4}\)\s*$", "", title).strip()

    alternatives = re.findall(r"\(([^()]*)\)", clean)
    primary = re.sub(r"\s*\([^()]*\)", "", clean).strip()

    candidates = [primary] + alternatives

    search_titles = []
    seen = set()

    for candidate in candidates:
        candidate = candidate.strip()

        if not candidate:
            continue

        for variation in (candidate, reorder_article(candidate)):
            key = normalize_title(variation)

            if key and key not in seen:
                seen.add(key)
                search_titles.append(variation)

    return search_titles


def display_title(result: dict) -> str:
    return result.get("title") or result.get("name") or "?"


# --------------------------------------------------
# TMDB API
# --------------------------------------------------

def tmdb_get(session, path: str, params: dict | None = None) -> dict:
    response = session.get(
        f"{TMDB_BASE_URL}{path}",
        params=params or {},
        timeout=20,
    )
    response.raise_for_status()
    return response.json()


def search_tmdb(session, title: str, media_type: str) -> list[dict]:
    data = tmdb_get(
        session,
        f"/search/{media_type}",
        {
            "query": title,
            "include_adult": False,
            "language": "en-US",
        },
    )
    return data.get("results", [])


def find_by_imdb(session, imdb_id: str) -> dict | None:
    data = tmdb_get(
        session,
        f"/find/{imdb_id}",
        {"external_source": "imdb_id"},
    )

    for key, media_type in (("movie_results", "movie"), ("tv_results", "tv")):
        for item in data.get(key, []):
            if item.get("poster_path"):
                item["_media_type"] = media_type
                return item

    return None


def get_by_tmdb_id(session, tmdb_id: int, media_type: str) -> dict | None:
    data = tmdb_get(session, f"/{media_type}/{tmdb_id}")

    if data.get("poster_path"):
        data["_media_type"] = media_type
        return data

    return None


# --------------------------------------------------
# Matching
# --------------------------------------------------

def title_similarity(a: str, b: str) -> float:
    """
    Fuzzy similarity with a containment rule, so prefixes like
    "Stephen King's The Langoliers" still match "The Langoliers".
    The 10-character minimum stops short titles ("Harlem") from
    matching longer ones ("Harlem Nights").
    """
    score = SequenceMatcher(None, a, b).ratio()
    short, long_ = sorted((a, b), key=len)

    if len(short) >= 10 and short in long_:
        score = max(score, 0.90)

    return score


def rank_candidates(
    results: list[dict],
    movie_title: str,
    movie_year: int | None,
) -> list[tuple[float, dict]]:
    """Score candidates: title similarity minus a soft year penalty."""
    targets = [normalize_title(t) for t in get_search_titles(movie_title)]
    targets = [t for t in targets if t]

    if not targets:
        return []

    ranked = []

    for result in results:
        if not result.get("poster_path"):
            continue

        names = [
            normalize_title(result.get(key, ""))
            for key in ("title", "original_title", "name", "original_name")
        ]
        names = [n for n in names if n]

        if not names:
            continue

        score = max(
            title_similarity(target, name)
            for target in targets
            for name in names
        )

        result_year = extract_year(
            result.get("release_date") or result.get("first_air_date")
        )

        if movie_year and result_year:
            gap = min(abs(movie_year - result_year), MAX_YEAR_PENALTY_YEARS)
            score -= gap * YEAR_PENALTY
        else:
            score -= NO_YEAR_PENALTY

        ranked.append((score, result))

    ranked.sort(key=lambda item: item[0], reverse=True)
    return ranked


def decide(ranked: list[tuple[float, dict]]) -> tuple[dict | None, str]:
    """Accept only a confident, unambiguous best candidate."""
    if not ranked:
        return None, "no_candidates"

    best_score, best = ranked[0]

    if best_score < ACCEPT_SCORE:
        return None, "low_score"

    if len(ranked) > 1 and best_score - ranked[1][0] < MIN_GAP:
        return None, "ambiguous"

    return best, "ok"


def collect_results(
    session,
    search_titles: list[str],
    media_type: str,
    verbose: bool,
) -> list[dict]:
    """Search every title variation for one media type, de-duplicated."""
    collected = []
    seen_ids = set()

    # TMDB search can miss titles with apostrophes, so also try without them.
    queries = []

    for title in search_titles:
        queries.append(title)
        plain = title.replace("'", "").replace("\u2019", "")

        if plain != title:
            queries.append(plain)

    for search_title in queries:
        results = search_tmdb(session, search_title, media_type)

        if verbose:
            print(
                f"    QUERY {search_title!r} | {media_type} "
                f"| results: {len(results)}"
            )

        for result in results:
            result_id = result.get("id")

            if result_id in seen_ids:
                continue

            seen_ids.add(result_id)
            result["_media_type"] = media_type
            collected.append(result)

        time.sleep(REQUEST_DELAY)

    return collected


def resolve_movie(
    session,
    movie,
    year: int | None,
    overrides: dict,
    verbose: bool,
) -> tuple[dict | None, str, list[tuple[float, dict]]]:
    """
    Returns (match, reason, ranked_candidates).
    Order: manual override -> IMDb ID -> movie search -> TV search.
    """
    # 1. Manual override file (rare leftovers)
    override = overrides.get(str(movie.movie_id))

    if override:
        match = get_by_tmdb_id(
            session,
            override["tmdb_id"],
            override.get("media_type", "movie"),
        )
        time.sleep(REQUEST_DELAY)

        if match:
            return match, "override", []

        return None, "override_no_poster", []

    # 2. Exact lookup by IMDb ID
    imdb_id = (
        IMDB_ID_OVERRIDES.get(movie.movie_id)
        or getattr(movie, "imdb_id", None)
    )

    if imdb_id:
        match = find_by_imdb(session, str(imdb_id))
        time.sleep(REQUEST_DELAY)

        if match:
            return match, "imdb", []

    # 3. Title search: movies first, TV only if nothing accepted
    search_titles = get_search_titles(movie.title)
    last_ranked: list[tuple[float, dict]] = []
    last_reason = "no_candidates"

    for media_type in ("movie", "tv"):
        results = collect_results(session, search_titles, media_type, verbose)
        ranked = rank_candidates(results, movie.title, year)
        match, reason = decide(ranked)

        if match:
            return match, reason, ranked

        # keep the best-looking failure for the review file
        if not last_ranked or (ranked and ranked[0][0] > last_ranked[0][0]):
            last_ranked = ranked
            last_reason = reason

    return None, last_reason, last_ranked


# --------------------------------------------------
# Overrides / review file
# --------------------------------------------------

def load_overrides() -> dict:
    if not OVERRIDES_FILE.exists():
        return {}

    with OVERRIDES_FILE.open(encoding="utf-8") as f:
        return json.load(f)


def write_review_file(rows: list[dict]) -> None:
    if not rows:
        return

    fieldnames = [
        "movie_id", "title", "year", "reason",
        "best_guess", "best_guess_year", "best_score", "tmdb_id", "media_type",
    ]

    with REVIEW_FILE.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Review file written: {REVIEW_FILE} ({len(rows)} rows)")


def build_review_row(movie, year, reason, ranked) -> dict:
    row = {
        "movie_id": movie.movie_id,
        "title": movie.title,
        "year": year or "",
        "reason": reason,
        "best_guess": "",
        "best_guess_year": "",
        "best_score": "",
        "tmdb_id": "",
        "media_type": "",
    }

    if ranked:
        score, best = ranked[0]
        row.update({
            "best_guess": display_title(best),
            "best_guess_year": extract_year(
                best.get("release_date") or best.get("first_air_date")
            ) or "",
            "best_score": round(score, 3),
            "tmdb_id": best.get("id", ""),
            "media_type": best.get("_media_type", ""),
        })

    return row


# --------------------------------------------------
# Main poster-fetching process
# --------------------------------------------------

def fetch_posters(limit: int | None, apply_changes: bool, verbose: bool):
    session = build_session()
    overrides = load_overrides()
    db = SessionLocal()

    try:
        statement = (
            select(Movie)
            .where(Movie.poster_url.is_(None))
            .order_by(Movie.movie_id)
        )

        if limit:
            statement = statement.limit(limit)

        movies = db.scalars(statement).all()

        print(f"\nMovies to process: {len(movies)}")
        print(f"Mode: {'APPLY CHANGES' if apply_changes else 'DRY RUN'}")
        print("-" * 55)

        matched = 0
        unmatched = 0
        errors = 0
        updated = 0
        review_rows: list[dict] = []

        for index, movie in enumerate(movies, start=1):
            prefix = f"[{index}/{len(movies)}]"

            try:
                year = extract_year(movie.title) or extract_year(
                    movie.release_date
                )

                match, reason, ranked = resolve_movie(
                    session, movie, year, overrides, verbose
                )

                if match:
                    poster_url = f"{IMAGE_BASE_URL}{match['poster_path']}"
                    matched += 1

                    print(
                        f"{prefix} MATCH ({reason}): "
                        f"{movie.title} -> {display_title(match)}"
                    )
                    print(f"    Poster: {poster_url}")

                    if apply_changes:
                        movie.poster_url = poster_url
                        updated += 1

                        if updated % COMMIT_EVERY == 0:
                            db.commit()
                            print("    Database batch committed.")

                else:
                    unmatched += 1
                    print(f"{prefix} NO MATCH ({reason}): {movie.title}")
                    review_rows.append(
                        build_review_row(movie, year, reason, ranked)
                    )

                time.sleep(REQUEST_DELAY)

            except requests.RequestException as exc:
                errors += 1
                print(f"{prefix} API ERROR: {movie.title}: {exc}")

            except Exception as exc:
                errors += 1
                print(f"{prefix} ERROR: {movie.title}: {exc}")

        if apply_changes:
            db.commit()

        write_review_file(review_rows)

        print("\n" + "=" * 55)
        print("POSTER FETCH SUMMARY")
        print("=" * 55)
        print(f"Processed: {len(movies)}")
        print(f"Matched:   {matched}")
        print(f"Unmatched: {unmatched}")
        print(f"Errors:    {errors}")
        print(f"Updated:   {updated}")

        if not apply_changes:
            print("\nDRY RUN: No database changes were made.")
            print("Use --apply to save the matched posters.")

    finally:
        db.close()
        session.close()


# --------------------------------------------------
# Command-line interface
# --------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Fetch movie posters from TMDB."
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Maximum number of movies to process (0 = all).",
    )

    parser.add_argument(
        "--apply",
        action="store_true",
        help="Save poster URLs to PostgreSQL.",
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print every TMDB query.",
    )

    args = parser.parse_args()

    fetch_posters(
        limit=args.limit or None,
        apply_changes=args.apply,
        verbose=args.verbose,
    )