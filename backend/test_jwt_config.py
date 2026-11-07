from app.core.config import (
    JWT_SECRET_KEY,
    JWT_ALGORITHM,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)

print("Secret configured:", bool(JWT_SECRET_KEY))
print("Algorithm:", JWT_ALGORITHM)
print("Token expiration:", ACCESS_TOKEN_EXPIRE_MINUTES, "minutes")