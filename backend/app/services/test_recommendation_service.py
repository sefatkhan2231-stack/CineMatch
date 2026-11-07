
from recommendation_service import service

print("\n--- Movie search ---")
print(service.search_movies("Last Action Hero", limit=3))

print("\n--- Recommendations for user 196 ---")
print(service.recommend_for_user("434", limit=5))

print("\n--- Similar movies ---")
print(service.similar_movies("94", limit=5))
