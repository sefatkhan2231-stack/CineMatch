import { Bookmark, Film, LoaderCircle, Star, Trash2 } from "lucide-react";
import { useEffect, useState } from "react";
import { ratingApi, watchlistApi } from "../services/api";

function formatDate(value) {
  if (!value) return "";
  const d = new Date(value);
  return Number.isNaN(d.getTime()) ? "" : d.toLocaleDateString();
}

function Row({ movie, onOpen, onRemove, removeLabel, extra }) {
  const [posterFailed, setPosterFailed] = useState(false);

  return (
    <li className="lib-row">
      <button className="lib-open" onClick={() => onOpen(movie.movie_id)}>
        <div className="lib-poster">
          {movie.poster_url && !posterFailed ? (
            <img
              src={movie.poster_url}
              alt=""
              loading="lazy"
              onError={() => setPosterFailed(true)}
            />
          ) : (
            <Film size={22} strokeWidth={1.3} />
          )}
        </div>

        <div className="lib-text">
          <h3>{movie.title}</h3>
          <p>{(movie.genres || []).slice(0, 3).join(" · ")}</p>
          {extra}
        </div>
      </button>

      <button
        className="lib-remove"
        onClick={() => onRemove(movie.movie_id)}
        aria-label={removeLabel}
        title={removeLabel}
      >
        <Trash2 size={16} />
      </button>
    </li>
  );
}

export default function Profile({ user, onOpenMovie }) {
  const [ratings, setRatings] = useState([]);
  const [watchlist, setWatchlist] = useState([]);
  const [tab, setTab] = useState("ratings");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setLoading(true);
      setError("");
      try {
        const [r, w] = await Promise.all([
          ratingApi.getMyRatings(),
          watchlistApi.getMyWatchlist(),
        ]);
        if (cancelled) return;
        setRatings(r.results || []);
        setWatchlist(w.results || []);
      } catch (err) {
        if (!cancelled) setError(err.message || "Could not load your library.");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    load();
    window.scrollTo({ top: 0 });
    return () => {
      cancelled = true;
    };
  }, []);

  async function removeRating(movieId) {
    try {
      await ratingApi.delete(Number(movieId));
      setRatings((prev) =>
        prev.filter((m) => String(m.movie_id) !== String(movieId)),
      );
    } catch (err) {
      setError(err.message);
    }
  }

  async function removeFromWatchlist(movieId) {
    try {
      await watchlistApi.remove(Number(movieId));
      setWatchlist((prev) =>
        prev.filter((m) => String(m.movie_id) !== String(movieId)),
      );
    } catch (err) {
      setError(err.message);
    }
  }

  const average =
    ratings.length > 0
      ? (
          ratings.reduce((sum, m) => sum + Number(m.rating), 0) / ratings.length
        ).toFixed(1)
      : "–";

  if (loading) {
    return (
      <section className="movie-section">
        <div className="status-message">
          <LoaderCircle className="spinner" size={28} />
          <p>Loading your library...</p>
        </div>
      </section>
    );
  }

  return (
    <section className="movie-section library-page">
      <div className="library-header">
        <div>
          <span className="section-kicker">MY LIBRARY</span>
          <h2>{user.username}</h2>
          <p className="library-email">{user.email}</p>
        </div>

        <div className="library-stats">
          <div>
            <strong>{ratings.length}</strong>
            <span>Rated</span>
          </div>
          <div>
            <strong>{watchlist.length}</strong>
            <span>Watchlist</span>
          </div>
          <div>
            <strong>{average}</strong>
            <span>Avg. rating</span>
          </div>
        </div>
      </div>

      <div className="library-tabs">
        <button
          className={tab === "ratings" ? "active" : ""}
          onClick={() => setTab("ratings")}
        >
          <Star size={15} /> Rated movies ({ratings.length})
        </button>
        <button
          className={tab === "watchlist" ? "active" : ""}
          onClick={() => setTab("watchlist")}
        >
          <Bookmark size={15} /> Watchlist ({watchlist.length})
        </button>
      </div>

      {error && <p className="detail-error">{error}</p>}

      {tab === "ratings" &&
        (ratings.length === 0 ? (
          <div className="empty-state">
            <Star size={34} />
            <h3>No ratings yet</h3>
            <p>Open any movie and give it a star rating.</p>
          </div>
        ) : (
          <ul className="lib-list">
            {ratings.map((m) => (
              <Row
                key={m.movie_id}
                movie={m}
                onOpen={onOpenMovie}
                onRemove={removeRating}
                removeLabel="Remove rating"
                extra={
                  <span className="lib-meta">
                    <Star size={13} fill="currentColor" /> {Number(m.rating)}/5
                    {m.updated_at || m.created_at
                      ? ` · ${formatDate(m.updated_at || m.created_at)}`
                      : ""}
                  </span>
                }
              />
            ))}
          </ul>
        ))}

      {tab === "watchlist" &&
        (watchlist.length === 0 ? (
          <div className="empty-state">
            <Bookmark size={34} />
            <h3>Your watchlist is empty</h3>
            <p>Open any movie and choose "Add to watchlist".</p>
          </div>
        ) : (
          <ul className="lib-list">
            {watchlist.map((m) => (
              <Row
                key={m.movie_id}
                movie={m}
                onOpen={onOpenMovie}
                onRemove={removeFromWatchlist}
                removeLabel="Remove from watchlist"
                extra={
                  m.added_at ? (
                    <span className="lib-meta">
                      Added {formatDate(m.added_at)}
                    </span>
                  ) : null
                }
              />
            ))}
          </ul>
        ))}
    </section>
  );
}
