import {
  AlertCircle,
  Clapperboard,
  Film,
  LoaderCircle,
  Play,
  Search,
  Sparkles,
  Star,
} from "lucide-react";
import { useEffect, useState } from "react";
import "./App.css";

import {
  authApi,
  getAccessToken,
  movieApi,
  removeAccessToken,
} from "./services/api";

import Auth from "./components/Auth";

const API_BASE_URL = "http://127.0.0.1:8000";

function getReleaseYear(releaseDate) {
  if (!releaseDate) return "MOVIE";

  const match = String(releaseDate).match(/\b(19|20)\d{2}\b/);

  return match ? match[0] : "MOVIE";
}

function MovieCard({ movie, onSelect }) {
  const [posterFailed, setPosterFailed] = useState(false);

  return (
    <button
      className="movie-card"
      onClick={() => onSelect(movie)}
      title={`Find movies similar to ${movie.title}`}
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

function App() {
  const [query, setQuery] = useState("");
  const [searchResults, setSearchResults] = useState([]);
  const [recommendations, setRecommendations] = useState([]);
  const [similarMovies, setSimilarMovies] = useState([]);
  const [selectedMovie, setSelectedMovie] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [searched, setSearched] = useState(false);
  const [user, setUser] = useState(null);
  const [authChecking, setAuthChecking] = useState(true);

  useEffect(() => {
    async function checkSession() {
      const token = getAccessToken();

      if (!token) {
        setAuthChecking(false);
        return;
      }

      try {
        const currentUser = await authApi.me();
        setUser(currentUser);
      } catch (err) {
        removeAccessToken();
        setUser(null);
        console.error("Session validation failed:", err.message);
      } finally {
        setAuthChecking(false);
      }
    }

    checkSession();
  }, []);

  useEffect(() => {
    if (!user) return;

    async function loadRecommendations() {
      setLoading(true);
      setError("");
      setSearched(false);
      setSelectedMovie(null);

      try {
        const data = await movieApi.recommendations(12);
        setRecommendations(data.results || []);
      } catch (err) {
        setError(err.message || "Could not load recommendations.");
      } finally {
        setLoading(false);
      }
    }

    loadRecommendations();
  }, [user]);

  function handleLogout() {
    removeAccessToken();

    setUser(null);
    setRecommendations([]);
    setSearchResults([]);
    setSimilarMovies([]);
    setSelectedMovie(null);
    setSearched(false);
    setQuery("");
    setError("");
  }

  async function searchMovies(event) {
    event.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setError("");
    setRecommendations([]);
    setSimilarMovies([]);
    setSelectedMovie(null);
    setSearched(true);

    try {
      const data = await movieApi.search(query, 12);
      setSearchResults(data.results || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function findSimilar(movie) {
    setLoading(true);
    setError("");
    setSelectedMovie(movie);
    setSearchResults([]);
    setRecommendations([]);
    setSimilarMovies([]);
    setSearched(false);

    try {
      const data = await movieApi.similar(movie.movie_id, 12);
      setSimilarMovies(data.results || []);
    } catch (err) {
      setError(err.message || "Could not load similar movies.");
    } finally {
      setLoading(false);
    }
  }

  const visibleMovies = searched
    ? searchResults
    : selectedMovie
      ? similarMovies
      : recommendations;

  const sectionTitle = searched
    ? `Search results for "${query}"`
    : selectedMovie
      ? `Movies similar to ${selectedMovie.title}`
      : "Recommended for you";

  if (authChecking) {
    return (
      <div className="auth-page">
        <div className="status-message">
          <LoaderCircle className="spinner" size={28} />
          <p>Checking your session...</p>
        </div>
      </div>
    );
  }

  if (!user) {
    return <Auth onLogin={setUser} />;
  }

  return (
    <div className="app-shell">
      <header className="navbar">
        <a href="#home" className="brand">
          <span className="brand-icon">
            <Clapperboard size={23} />
          </span>
          <span>
            CINE<span className="brand-accent">MATCH</span>
          </span>
        </a>

        <nav>
          <a href="#home">Discover</a>
          <a href="#movies">Movies</a>
        </nav>

        <form className="search-form" onSubmit={searchMovies}>
          <Search size={18} />
          <input
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Search movies..."
            aria-label="Search movies"
          />
          <button type="submit" aria-label="Submit search">
            Search
          </button>
        </form>

        <div className="nav-user">
          <span>Hi, {user.username}</span>

          <button type="button" onClick={handleLogout}>
            Log out
          </button>
        </div>
      </header>

      <main id="home">
        <section className="hero">
          <div className="hero-content">
            <div className="eyebrow">
              <Sparkles size={15} />
              YOUR PERSONAL MOVIE UNIVERSE
            </div>

            <h1>
              Every movie has
              <br />
              <span>a match.</span>
            </h1>

            <p>
              Discover your next favorite film with recommendations powered by
              machine learning.
            </p>

            <a className="hero-button" href="#movies">
              <Play size={17} fill="currentColor" />
              Explore movies
            </a>
          </div>

          <div className="hero-art" aria-hidden="true">
            <div className="orbit orbit-one" />
            <div className="orbit orbit-two" />
            <div className="hero-film">
              <Clapperboard size={100} />
            </div>
            <span className="floating-star star-one">✦</span>
            <span className="floating-star star-two">✧</span>
            <span className="floating-star star-three">✦</span>
          </div>

          <div className="hero-bottom">
            <span>DISCOVER DIFFERENTLY</span>
            <span>100K RATINGS · 1,682 MOVIES</span>
          </div>
        </section>

        <section className="movie-section" id="movies">
          <div className="section-heading">
            <div>
              <span className="section-kicker">
                {searched
                  ? "SEARCH"
                  : selectedMovie
                    ? "DISCOVER MORE"
                    : "PERSONALIZED FOR YOU"}
              </span>
              <h2>{sectionTitle}</h2>
            </div>
            <span className="result-count">
              {visibleMovies.length}{" "}
              {visibleMovies.length === 1 ? "movie" : "movies"}
            </span>
          </div>

          {loading && (
            <div className="status-message">
              <LoaderCircle className="spinner" size={28} />
              <p>Finding your next favorite...</p>
            </div>
          )}

          {!loading && error && (
            <div className="status-message error-message">
              <AlertCircle size={25} />
              <p>{error}</p>
            </div>
          )}

          {!loading && !error && visibleMovies.length > 0 && (
            <div className="movie-grid">
              {visibleMovies.map((movie) => (
                <MovieCard
                  key={movie.movie_id}
                  movie={movie}
                  onSelect={findSimilar}
                />
              ))}
            </div>
          )}

          {!loading && !error && visibleMovies.length === 0 && (
            <div className="empty-state">
              <Film size={34} />
              <h3>{searched ? "No movies found" : "No movies to show yet"}</h3>
              <p>
                {searched
                  ? "Try another title, such as Toy Story, Star Wars, or Batman."
                  : "Search for a movie to start discovering."}
              </p>
            </div>
          )}
        </section>

        <footer className="footer">
          <a href="#home" className="footer-brand">
            CINEMATCH
          </a>
          <p>Built with React, FastAPI, and machine learning.</p>
          <span>MovieLens 100K · Educational portfolio project</span>
        </footer>
      </main>
    </div>
  );
}

export default App;
