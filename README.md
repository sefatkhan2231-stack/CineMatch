# 🎬 CineMatch — Movie Recommendation System

**Discover your next favorite movie with personalized recommendations.**

CineMatch is a full-stack movie recommendation platform that helps users discover movies through personalized recommendations, similar-movie suggestions, and movie search.

Built with **React, FastAPI, PostgreSQL, and Machine Learning**, CineMatch combines collaborative filtering and content-based recommendation techniques to make movie discovery more relevant and engaging.

🌐 **Live Demo:** https://cine-match-henna.vercel.app/

---

## ✨ Features

- **Personalized Recommendations** — Discover movies based on user preferences and rating behavior.
- **Similar Movie Discovery** — Find movies related to a selected movie.
- **Movie Search** — Search and explore movies from the MovieLens dataset.
- **User Authentication** — Register and log in securely using JWT-based authentication.
- **Movie Ratings** — Rate movies and manage your ratings.
- **Watchlist** — Save movies you want to watch later.
- **Movie Posters** — Visual movie discovery with poster artwork.
- **REST API** — Backend services powered by FastAPI.
- **Responsive Interface** — A modern, dark-themed movie discovery experience.

---

## 🖥️ Live Preview

Visit the application:

**[🚀 Open CineMatch](https://cine-match-henna.vercel.app/)**

---

## 🛠️ Tech Stack

| Category | Technologies |
|---|---|
| Frontend | React, Vite, JavaScript |
| Styling | CSS |
| Icons | Lucide React |
| Backend | Python, FastAPI |
| Database | PostgreSQL |
| ORM | SQLAlchemy |
| Authentication | JWT, Argon2 |
| Machine Learning | Scikit-learn, Surprise |
| Recommendation | Collaborative Filtering, Content-Based Filtering |
| Dataset | MovieLens 100K |
| Deployment | Vercel, Render |

---

## 🧠 Recommendation System

The recommendation engine uses machine learning techniques to help users discover movies.

### 1. Collaborative Filtering

Collaborative filtering analyzes user-rating patterns to identify movies that users with similar preferences may enjoy.

The project uses **Singular Value Decomposition (SVD)** through the Surprise library.

SVD learns latent user and movie factors from the rating matrix and predicts how a user might rate a movie they have not watched.

### 2. Content-Based Filtering

Content-based filtering recommends movies based on movie characteristics.

CineMatch uses movie genres to identify similarities between movies and suggest titles with related content.

### 3. Hybrid Recommendations

The recommendation system combines recommendation signals to produce a ranked list of movies.

This helps balance predicted user preferences with movie characteristics and popularity.

### 4. Model Evaluation

The models were evaluated using the MovieLens 100K dataset.

**Collaborative filtering — initial evaluation**

| Model | RMSE | MAE |
|---|---:|---:|
| SVD | 0.9348 | 0.7377 |
| KNNWithMeans | 0.9524 | 0.7518 |
| NMF | 1.6503 | 1.3143 |

**Ranking evaluation**

The recommendation models were also evaluated using:

- Precision@10
- Recall@10
- NDCG@10

A tuned SVD experiment achieved approximately:

| Metric | Score |
|---|---:|
| Precision@10 | 0.0742 |
| Recall@10 | 0.0549 |
| NDCG@10 | 0.0850 |

These results are experimental results from offline evaluation, not guarantees of real-world recommendation quality.

---

## 📊 Dataset

CineMatch uses the **[MovieLens 100K Dataset](https://grouplens.org/datasets/movielens/100k/)** provided by GroupLens Research.

Dataset overview:

| Description | Value |
|---|---:|
| Total Ratings | 100,000 |
| Users | 943 |
| Movies | 1,682 |
| Rating Scale | 1–5 |

The dataset provides user ratings and movie metadata for developing and evaluating recommendation algorithms.

---

## 🏗️ Project Architecture

CineMatch follows a full-stack architecture:

```text
                 ┌──────────────────────┐
                 │     React Frontend   │
                 │       (Vercel)       │
                 └──────────┬───────────┘
                            │
                         REST API
                            │
                 ┌──────────▼───────────┐
                 │     FastAPI Backend  │
                 │       (Render)       │
                 └──────────┬───────────┘
                            │
              ┌─────────────┼─────────────┐
              │             │             │
       ┌──────▼─────┐ ┌─────▼──────┐ ┌────▼───────┐
       │ PostgreSQL │ │ ML Models  │ │   Auth     │
       │  Database  │ │            │ │  JWT       │
       └────────────┘ └────────────┘ └────────────┘
```

### Database

PostgreSQL stores application data, including:

- Users
- Movies
- User ratings
- Watchlists
- MovieLens ratings

SQLAlchemy is used for database interaction.

---

## 🚀 Run Locally

Follow these steps to run CineMatch on your local machine.

### Prerequisites

- Python 3.10+
- Node.js and npm
- PostgreSQL
- Git

### 1. Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git

cd movie-recommendation
```

Replace the repository URL with your actual GitHub repository URL.

### 2. Backend Setup

Create and activate a virtual environment:

**Windows:**

```powershell
python -m venv venv

.\venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Create a `.env` file in the backend's expected configuration location.

Example:

```env
DATABASE_URL=postgresql+psycopg://username:password@localhost:5432/cinematch_db

SECRET_KEY=your_secret_key
```

Use the exact environment variable names expected by your backend configuration. Never commit real database credentials, secret keys, or API tokens to GitHub.

### 4. Database Setup

Create a PostgreSQL database:

```sql
CREATE DATABASE cinematch_db;
```

Configure the database connection and initialize the database tables using the project's database setup process.

Import the MovieLens data if you are setting up the recommendation system from scratch.

### 5. Start the Backend

From the project root:

```bash
python -m uvicorn backend.main:app --reload
```

Backend API:

```text
http://127.0.0.1:8000
```

Interactive API documentation:

```text
http://127.0.0.1:8000/docs
```

### 6. Frontend Setup

Open another terminal:

```bash
cd frontend

npm install

npm run dev
```

The frontend will be available at the local Vite development URL shown in your terminal.

Make sure the frontend API configuration points to your local FastAPI backend.

---

## 🔌 API Overview

CineMatch exposes REST API endpoints for its main application features.

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Backend health check |
| POST | `/auth/register` | Register a new user |
| POST | `/auth/login` | Authenticate a user |
| GET | `/auth/me` | Get authenticated user information |
| GET | `/movies/search` | Search movies |
| GET | `/movies/{movie_id}/similar` | Find similar movies |
| GET | `/recommendations/me` | Get personalized recommendations |
| GET/POST | `/ratings` | Retrieve or submit ratings |
| GET | `/watchlist/me` | Retrieve the user's watchlist |

Protected endpoints require a valid JWT access token.

For the complete API specification, run the backend and visit `/docs`.

---

## ☁️ Deployment

CineMatch is deployed using:

| Component | Platform |
|---|---|
| Frontend | Vercel |
| Backend | Render |
| Database | Render PostgreSQL |

The frontend communicates with the FastAPI backend through HTTP requests.

The production backend uses environment-based database configuration rather than a local database connection.

---

## 🔒 Security

Security considerations implemented in CineMatch include:

- JWT-based authentication.
- Password hashing using Argon2.
- Protected endpoints for authenticated operations.
- Environment variables for sensitive configuration.
- PostgreSQL database integration.

---

## 🎯 Project Goals

This project was developed to explore practical applications of machine learning and full-stack development.

Key learning objectives:

- Understanding collaborative filtering and content-based recommendation.
- Training and evaluating recommendation models.
- Working with real-world rating datasets.
- Building REST APIs with FastAPI.
- Designing relational database structures.
- Integrating React with a Python backend.
- Implementing authentication and user-specific functionality.
- Deploying a full-stack machine learning application.

---

## 🔮 Future Improvements

- Improve recommendation quality through additional model experiments.
- Add more advanced hybrid recommendation techniques.
- Introduce user feedback and recommendation explanations.
- Improve cold-start recommendations for new users.
- Add movie filtering by genre, release year, and rating.
- Expand the movie catalog and metadata.
- Add more comprehensive recommendation evaluation and monitoring.

---

## 👨‍💻 Author

**MD. Sefat Khan**

Full Stack Developer | Aspiring Data Scientist & Machine Learning Engineer

- GitHub: https://github.com/Sefat-Khan

---

## 📄 License

This project is intended for educational and portfolio purposes. Add a repository license file if you want to specify formal reuse and distribution terms.

---

⭐ If you find CineMatch interesting, consider giving the repository a star!
