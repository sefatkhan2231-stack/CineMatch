import {
  ArrowLeft,
  Bookmark,
  BookmarkCheck,
  Film,
  LoaderCircle,
  Star,
  Trash2,
} from "lucide-react";
import { useEffect, useState } from "react";
import { movieApi, ratingApi, watchlistApi } from "../services/api";
import MovieCard, { getReleaseYear } from "./MovieCard";

export default function MovieDetail({ movieId, onBack, onSelectMovie }) {
  const [movie, setMovie] = useState(null);
  const [similar, setSimilar] = useState([]);
  const [myRating, setMyRating] = useState(null);
  const [inWatchlist, setInWatchlist] = useState(false);
  const [hoverStar, setHoverStar] = useState(0);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [posterFailed, setPosterFailed] = useState(false);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setLoading(true);
      setError("");
      setPosterFailed(false);

      try {
        const [movieData, ratings, watchlist] = await Promise.all([
          movieApi.get(movieId),
          ratingApi.getMyRatings(),
          watchlistApi.getMyWatchlist(),
        ]);
        if (cancelled) return;

        setMovie(movieData);

        const mine = (ratings.results || []).find(
          (r) => String(r.movie_id) === String(movieId),
        );
        setMyRating(mine ? Number(mine.rating) : null);

        setInWatchlist(
          (watchlist.results || []).some(
            (w) => String(w.movie_id) === String(movieId),
          ),
        );

        // Similar movies are optional: don't break the page if this fails.
        movieApi
          .similar(movieId, 6)
          .then((d) => !cancelled && setSimilar(d.results || []))
          .catch(() => !cancelled && setSimilar([]));
      } catch (err) {
        if (!cancelled) setError(err.message || "Could not load this movie.");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    load();
    window.scrollTo({ top: 0 });

    return () => {
      cancelled = true;
    };
  }, [movieId]);

  async function handleRate(value) {
    setBusy(true);
    setError("");
    try {
      await ratingApi.submit(Number(movieId), value);
      setMyRating(value);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  async function handleRemoveRating() {
    setBusy(true);
    setError("");
    try {
      await ratingApi.delete(Number(movieId));
      setMyRating(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  async function handleWatchlist() {
    setBusy(true);
    setError("");
    try {
      if (inWatchlist) {
        await watchlistApi.remove(Number(movieId));
        setInWatchlist(false);
      } else {
        await watchlistApi.add(Number(movieId));
        setInWatchlist(true);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  if (loading) {
    return (
      <section className="movie-section">
        <div className="status-message">
          <LoaderCircle className="spinner" size={28} />
          <p>Loading movie...</p>
        </div>
      </section>
    );
  }

  if (!movie) {
    return (
      <section className="movie-section">
        <button className="back-button" onClick={onBack}>
          <ArrowLeft size={18} /> Back
        </button>
        <div className="status-message error-message">
          <p>{error || "Movie not found."}</p>
        </div>
      </section>
    );
  }

  const shownRating = hoverStar || myRating || 0;

  return (
    <section className="movie-section detail-page">
      <button className="back-button" onClick={onBack}>
        <ArrowLeft size={18} /> Back
      </button>

      <div className="detail-layout">
        <div className="detail-poster">
          {movie.poster_url && !posterFailed ? (
            <img
              src={movie.poster_url}
              alt={`${movie.title} poster`}
              onError={() => setPosterFailed(true)}
            />
          ) : (
            <>
              <Film size={60} strokeWidth={1.3} />
              <span className="poster-label">CINEMATCH</span>
            </>
          )}
        </div>

        <div className="detail-info">
          <span className="section-kicker">
            {getReleaseYear(movie.release_date)}
          </span>
          <h2>{movie.title}</h2>

          <div className="detail-genres">
            {(movie.genres || []).map((g) => (
              <span key={g} className="genre-chip">
                {g}
              </span>
            ))}
          </div>

          <div className="rate-block">
            <p className="rate-label">
              {myRating ? `Your rating: ${myRating}/5` : "Rate this movie"}
            </p>

            <div className="star-row" onMouseLeave={() => setHoverStar(0)}>
              {[1, 2, 3, 4, 5].map((value) => (
                <button
                  key={value}
                  type="button"
                  className="star-button"
                  disabled={busy}
                  aria-label={`Rate ${value} star${value > 1 ? "s" : ""}`}
                  onMouseEnter={() => setHoverStar(value)}
                  onClick={() => handleRate(value)}
                >
                  <Star
                    size={30}
                    fill={value <= shownRating ? "currentColor" : "none"}
                  />
                </button>
              ))}

              {myRating && (
                <button
                  type="button"
                  className="text-button"
                  disabled={busy}
                  onClick={handleRemoveRating}
                >
                  <Trash2 size={15} /> Remove rating
                </button>
              )}
            </div>
          </div>

          <button
            type="button"
            className={`watchlist-button ${inWatchlist ? "active" : ""}`}
            disabled={busy}
            onClick={handleWatchlist}
          >
            {inWatchlist ? (
              <>
                <BookmarkCheck size={18} /> In your watchlist
              </>
            ) : (
              <>
                <Bookmark size={18} /> Add to watchlist
              </>
            )}
          </button>

          {error && <p className="detail-error">{error}</p>}
        </div>
      </div>

      {similar.length > 0 && (
        <div className="detail-similar">
          <h3>Similar movies</h3>
          <div className="movie-grid">
            {similar.map((m) => (
              <MovieCard
                key={m.movie_id}
                movie={m}
                onSelect={(picked) => onSelectMovie(picked.movie_id)}
              />
            ))}
          </div>
        </div>
      )}
    </section>
  );
}
