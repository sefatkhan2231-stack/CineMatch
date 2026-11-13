import { Film, Sparkles, Star } from "lucide-react";
import { useState } from "react";

export function getReleaseYear(releaseDate) {
  if (!releaseDate) return "MOVIE";
  const match = String(releaseDate).match(/\b(19|20)\d{2}\b/);
  return match ? match[0] : "MOVIE";
}

export default function MovieCard({ movie, onSelect }) {
  const [posterFailed, setPosterFailed] = useState(false);

  return (
    <button
      className="movie-card"
      onClick={() => onSelect(movie)}
      title={`View ${movie.title}`}
    >
      <div className="movie-poster">
        {movie.poster_url && !posterFailed ? (
          <img
            src={movie.poster_url}
            alt={`${movie.title} poster`}
            loading="lazy"
            onError={() => setPosterFailed(true)}
          />
        ) : (
          <>
            <Film size={38} strokeWidth={1.3} />
            <span className="poster-label">CINEMATCH</span>
          </>
        )}
        <span className="movie-year">{getReleaseYear(movie.release_date)}</span>
      </div>

      <div className="movie-info">
        <h3>{movie.title}</h3>
        <p>{(movie.genres || []).slice(0, 3).join(" · ") || "Discover"}</p>

        {movie.recommendation_score != null && (
          <span className="rating">
            <Sparkles size={13} />
            {Number(movie.recommendation_score).toFixed(2)} match score
          </span>
        )}
        {movie.predicted_rating != null && (
          <span className="rating">
            <Star size={13} fill="currentColor" />
            {Number(movie.predicted_rating).toFixed(1)} predicted
          </span>
        )}
      </div>
    </button>
  );
}
