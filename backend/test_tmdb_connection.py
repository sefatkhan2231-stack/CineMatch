
import os
import requests
from dotenv import load_dotenv

load_dotenv()

token = os.getenv("TMDB_API_READ_ACCESS_TOKEN")

if not token:
    raise ValueError("TMDB API token not found in .env")

response = requests.get(
    "https://api.themoviedb.org/3/configuration",
    headers={
        "Authorization": f"Bearer {token}",
        "accept": "application/json",
    },
    timeout=15,
)

response.raise_for_status()

data = response.json()

print("TMDB connection successful!")
print("Image base URL:", data["images"]["secure_base_url"])
print("Available poster sizes:", data["images"]["poster_sizes"])
