import {
  AlertCircle,
  Clapperboard,
  Film,
  LoaderCircle,
  Play,
  Search,
  Sparkles,
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
import Logo from "./components/Logo";
import MovieCard from "./components/MovieCard";
import MovieDetail from "./components/MovieDetail";
import Profile from "./components/Profile";

function getReleaseYear(releaseDate) {
  if (!releaseDate) return "MOVIE";

  const match = String(releaseDate).match(/\b(19|20)\d{2}\b/);

  return match ? match[0] : "MOVIE";
}

function App() {
  const [query, setQuery] = useState("");
  const [searchResults, setSearchResults] = useState([]);
  const [recommendations, setRecommendations] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [searched, setSearched] = useState(false);
  const [user, setUser] = useState(null);
  const [authChecking, setAuthChecking] = useState(true);
  const [activeMovieId, setActiveMovieId] = useState(null);
  const [showProfile, setShowProfile] = useState(false);

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

  async function loadRecommendations() {
    setLoading(true);
    setError("");
    try {
      const data = await movieApi.recommendations(12);
      setRecommendations(data.results || []);
    } catch (err) {
      setError(err.message || "Could not load recommendations.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (user) loadRecommendations();
  }, [user]);

  function handleLogout() {
    removeAccessToken();

    setUser(null);
    setRecommendations([]);
    setSearchResults([]);
    setActiveMovieId(null);
    setSearched(false);
    setShowProfile(false);
    setQuery("");
    setError("");
  }

  function openMovie(movieOrId) {
    const id = typeof movieOrId === "object" ? movieOrId.movie_id : movieOrId;
    setActiveMovieId(id);
  }

  function closeMovie() {
    setActiveMovieId(null);
    if (!searched && !showProfile) loadRecommendations(); // CHANGED
  }

  async function searchMovies(event) {
    event.preventDefault();
    if (!query.trim()) return;

    setActiveMovieId(null);
    setLoading(true);
    setError("");
    setRecommendations([]);
    setShowProfile(false);
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

  function goHome() {
    setActiveMovieId(null);
    setSearched(false);
    setQuery("");
    loadRecommendations();
    setShowProfile(false);
  }

  function openProfile() {
    setActiveMovieId(null);
    setShowProfile(true);
  }

  const visibleMovies = searched ? searchResults : recommendations;
  const sectionTitle = searched
    ? `Search results for "${query}"`
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
        <a href="#home" className="brand" onClick={goHome}>
          <Logo />
        </a>

        <nav>
          <a href="#home" onClick={openProfile}>
            My Library
          </a>
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
        {activeMovieId ? (
          <MovieDetail
            movieId={activeMovieId}
            onBack={closeMovie}
            onSelectMovie={openMovie}
          />
        ) : showProfile ? (
          <Profile user={user} onOpenMovie={openMovie} />
        ) : (
          <>
            {
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
                    Discover your next favorite film with recommendations
                    powered by machine learning.
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
            }

            {
              <section className="movie-section" id="movies">
                <div className="section-heading">
                  <div>
                    <span className="section-kicker">
                      {searched ? "SEARCH" : "PERSONALIZED FOR YOU"}
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
                        onSelect={openMovie}
                      />
                    ))}
                  </div>
                )}

                {!loading && !error && visibleMovies.length === 0 && (
                  <div className="empty-state">
                    <Film size={34} />
                    <h3>
                      {searched ? "No movies found" : "No movies to show yet"}
                    </h3>
                    <p>
                      {searched
                        ? "Try another title, such as Toy Story, Star Wars, or Batman."
                        : "Search for a movie to start discovering."}
                    </p>
                  </div>
                )}
              </section>
            }
          </>
        )}

        <footer className="footer">
          <a href="#home" className="footer-brand">
            <Logo />
          </a>

          <p>Built with React, FastAPI, and machine learning.</p>

          <span>MovieLens 100K · Educational portfolio project</span>

          <span className="tmdb-attribution">
            This product uses the TMDB API but is not endorsed or certified by
            TMDB.
          </span>
        </footer>
      </main>
    </div>
  );
}

export default App;
