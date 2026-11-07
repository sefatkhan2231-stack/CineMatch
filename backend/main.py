from pathlib import Path

from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
import joblib
from sqlalchemy.orm import Session

from backend.app.services.recommendation_service import service
from backend.app.database.connection import get_db
from backend.app.services.movie_service import (
    search_movies_db,
    get_movie_db,
)
from backend.app.services.personalized_recommendation_service import (
    get_personalized_recommendations,
    build_popularity_lookup,
)
from backend.app.schemas.rating import RatingCreate
from backend.app.services.rating_service import (
    submit_rating,
    get_user_ratings,
    delete_rating,
)

from backend.app.services.watchlist_service import (
    add_to_watchlist,
    get_watchlist,
    remove_from_watchlist,
)

from backend.app.schemas.auth import UserRegister, UserLogin
from backend.app.services.auth_service import register_user, login_user

from backend.app.core.dependencies import get_current_user
from backend.app.database.models import User

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_DIR = PROJECT_ROOT / "ml" / "artifacts"

movie_stats = joblib.load(ARTIFACT_DIR / "movie_stats.pkl")
popularity_lookup = build_popularity_lookup(movie_stats)

app = FastAPI(
    title="CineMatch API",
    description=(
        "Movie discovery and personalized recommendations "
        "powered by user ratings, genre preferences, and popularity."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get('/')
def root():
    return {
        'message': 'Welcome to CineMatch API',
        'docs': '/docs',
        'health': '/health',
    }

@app.get('/health')
def health():
    return {'status': 'healthy'}

@app.get('/movies/search')
def search_movies(
    q: str = Query(..., min_length=1, description='Movie title'),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    results = search_movies_db(db, q, limit=limit)
    return {'count': len(results), 'results': results}

@app.get('/recommendations/me')
def get_recommendations(
    current_user: User = Depends(get_current_user),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    try:
        results = get_personalized_recommendations(
            db=db,
            user_id=current_user.id,
            popularity_lookup=popularity_lookup,
            limit=limit,
        )
        return {
            'User_id': current_user.id,
            'count': len(results),
            'results': results,
        }
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc

@app.get('/movies/{movie_id}')
def get_movie(
    movie_id: int,
    db: Session = Depends(get_db),
):
    movie = get_movie_db(db, movie_id)

    if movie is None:
        raise HTTPException(
            status_code=404,
            detail='Movie not found',
        )

    return movie

@app.get('/movies/{movie_id}/similar')
def get_similar_movies(
    movie_id: str,
    limit: int = Query(10, ge=1, le=50)
):
    try:
        results = service.similar_movies(movie_id, limit=limit)
        return {
            'movie_id': movie_id,
            'count': len(results),
            'results': results,
        }
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc

@app.post('/ratings')
def create_rating(
    payload: RatingCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        return submit_rating(
            db,
            current_user.id,
            payload.movie_id,
            payload.rating,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

@app.get('/ratings/me')
def read_user_ratings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        results = get_user_ratings(db, current_user.id)
        return {
            "user_id": current_user.id,
            "count": len(results),
            "results": results,
        }
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc))


@app.delete('/ratings/me/{movie_id}')
def remove_rating(
    movie_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        return delete_rating(db, current_user.id, movie_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

@app.post('/watchlist/{movie_id}')
def create_watchlist_entry(
    movie_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        return add_to_watchlist(db, current_user.id, movie_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

@app.get('/watchlist/me')
def read_watchlist(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        results = get_watchlist(db, current_user.id)

        return {
            'user_id': current_user.id,
            'count': len(results),
            'results': results,
        }
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

@app.delete('/watchlist/{movie_id}')
def delete_watchlist_entry(
    movie_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        return remove_from_watchlist(db, current_user.id, movie_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

@app.post('/auth/register', status_code=201)
def register(
    payload: UserRegister,
    db: Session = Depends(get_db),
):
    try:
        return register_user(
            db,
            username=payload.username,
            email=str(payload.email),
            password=payload.password,
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))

@app.post('/auth/login')
def login(
    payload: UserLogin,
    db: Session = Depends(get_db)
):
    try:
        return login_user(
            db,
            email=str(payload.email),
            password=payload.password,
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))

@app.get('/auth/me')
def read_current_user(
    current_user: User = Depends(get_current_user),
):
    return {
        'id': current_user.id,
        'username': current_user.username,
        'email': current_user.email,
    }