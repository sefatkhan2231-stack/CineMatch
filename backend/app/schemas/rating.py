from pydantic import BaseModel, Field


class RatingCreate(BaseModel):
    movie_id: int = Field(gt=0)
    rating: float = Field(ge=1, le=5)