const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "https://cinematch-nk0m.onrender.com/";

const TOKEN_KEY = "cinematch_access_token";

// JWT token management
export function saveAccessToken(token) {
  localStorage.setItem(TOKEN_KEY, token);
}

export function getAccessToken() {
  return localStorage.getItem(TOKEN_KEY);
}

export function removeAccessToken() {
  localStorage.removeItem(TOKEN_KEY);
}

// Centralized API request handler
async function apiRequest(path, options = {}) {
  const token = getAccessToken();

  const headers = {
    ...(options.body ? { "Content-Type": "application/json" } : {}),
    ...options.headers,
  };

  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers,
  });

  const data = await response.json().catch(() => null);

  if (!response.ok) {
    if (response.status === 401 && token) {
      removeAccessToken();
    }

    const detail = data?.detail;

    const message = Array.isArray(detail)
      ? detail.map((item) => item.msg).join(", ")
      : detail || "Something went wrong. Please try again.";

    throw new Error(message);
  }

  return data;
}

// Authentication
export const authApi = {
  register: (userData) =>
    apiRequest("/auth/register", {
      method: "POST",
      body: JSON.stringify(userData),
    }),

  login: (credentials) =>
    apiRequest("/auth/login", {
      method: "POST",
      body: JSON.stringify(credentials),
    }),

  me: () => apiRequest("/auth/me"),
};

// Movie operations
export const movieApi = {
  search: (query, limit = 12) =>
    apiRequest(`/movies/search?q=${encodeURIComponent(query)}&limit=${limit}`),

  get: (movieId) => apiRequest(`/movies/${movieId}`),

  similar: (movieId, limit = 12) =>
    apiRequest(`/movies/${movieId}/similar?limit=${limit}`),

  recommendations: (limit = 12) =>
    apiRequest(`/recommendations/me?limit=${limit}`),
};

// Rating operations
export const ratingApi = {
  submit: (movieId, rating) =>
    apiRequest("/ratings", {
      method: "POST",
      body: JSON.stringify({
        movie_id: movieId,
        rating,
      }),
    }),

  getMyRatings: () => apiRequest("/ratings/me"),

  delete: (movieId) =>
    apiRequest(`/ratings/me/${movieId}`, {
      method: "DELETE",
    }),
};

// Watchlist operations
export const watchlistApi = {
  getMyWatchlist: () => apiRequest("/watchlist/me"),

  add: (movieId) =>
    apiRequest(`/watchlist/${movieId}`, {
      method: "POST",
    }),

  remove: (movieId) =>
    apiRequest(`/watchlist/${movieId}`, {
      method: "DELETE",
    }),
};
