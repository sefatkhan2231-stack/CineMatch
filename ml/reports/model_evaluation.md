# CineMatch — Model Evaluation Report

## 1. Overview

CineMatch is a movie recommendation system developed to explore and compare different recommendation approaches. The project evaluates content-based filtering, collaborative filtering using Singular Value Decomposition (SVD), popularity-based recommendation, and a hybrid approach combining SVD with movie popularity.

The objective is to identify an effective recommendation strategy using offline evaluation and ranking metrics.

## 2. Dataset

**Dataset:** MovieLens 100K

| Property                   |                  Value |
| -------------------------- | ---------------------: |
| Total ratings              |                100,000 |
| Unique users               |                    943 |
| Movies in dataset metadata |                  1,682 |
| Average rating             | Approximately 3.53 / 5 |
| Rating scale               |                    1–5 |

The dataset contains user IDs, movie IDs, ratings, and timestamps, along with movie metadata and genre information.

## 3. Evaluation Methodology

### Train, validation, and test split

The project uses a reproducible split with fixed random seeds.

| Split                      |          Ratings | Purpose                                     |
| -------------------------- | ---------------: | ------------------------------------------- |
| Training                   | 64,000 initially | Model training and hyperparameter selection |
| Validation                 |           16,000 | Selecting SVD parameters and hybrid weights |
| Final development training |           80,000 | Retraining the selected models              |
| Final test                 |           20,000 | Final offline evaluation                    |

The validation experiment uses a 64,000-rating training subset and 16,000 validation ratings. After selecting the configuration, the models are retrained using all 80,000 development ratings and evaluated on the reserved 20,000-rating test set.

The final test set is intended to remain separate from model selection.

### Relevance definition

For ranking evaluation, a held-out rating of **4 or higher** is considered relevant.

For each eligible user, the system ranks candidate movies that appear in the training ratings but that the user has not rated in the training data.

The evaluation uses the top 10 recommendations, denoted by K = 10.

### Evaluation metrics

- **Precision@10:** The proportion of the 10 recommended movies that are relevant.
- **Recall@10:** The proportion of relevant held-out movies retrieved in the top 10.
- **NDCG@10:** A ranking-quality metric that gives greater importance to relevant movies appearing near the top of the recommendation list.

Higher values indicate better ranking performance.

## 4. Models Evaluated

### 4.1 Content-Based Filtering

The content-based recommender represents movies using their genre information and applies TF-IDF vectorization and cosine similarity.

A user profile is constructed from movies the user rated positively, and candidate movies are ranked by their similarity to that profile.

This approach can recommend movies with similar genres without relying directly on other users' preferences.

**Limitation:** Genre-only representations provide limited information about a movie. Movies sharing the same genres can have similar or identical representations, making it difficult to capture more nuanced preferences.

### 4.2 Popularity-Based Recommendation

The popularity baseline calculates a smoothed average rating for each movie:

\[
\text{Score}(m)=
\frac{n_m\bar r_m+C\mu}{n_m+C}
\]

Where:

- \(n_m\) is the number of training ratings for movie \(m\).
- \(\bar r_m\) is the movie's average training rating.
- \(\mu\) is the global average rating.
- \(C\) is the smoothing constant, set to 20.

Smoothing reduces the influence of movies with very few ratings, making the ranking less sensitive to small samples.

The resulting scores are used to rank unseen candidate movies for each user.

**Limitation:** Popularity does not fully personalize recommendations to individual users' interests.

### 4.3 Collaborative Filtering with SVD

The SVD recommender learns latent user and movie representations from the user–movie rating matrix. It uses these representations to estimate ratings for movies a user has not rated.

Selected hyperparameters:

| Parameter         | Value |
| ----------------- | ----: |
| Number of factors |    50 |
| Training epochs   |    40 |
| Learning rate     | 0.005 |
| Regularization    |  0.01 |
| Random seed       |    42 |

The configuration was selected through validation rather than by optimizing the final test metrics.

**Limitation:** SVD depends on historical rating patterns and can struggle with new users or movies that have little or no rating history.

### 4.4 Hybrid Recommendation

The hybrid combines SVD scores with popularity scores. For each user's candidate movies, both sets of scores are min-max normalized before blending:

\[
S*{\text{hybrid}}(u,m)=
0.25S*{\text{SVD,norm}}(u,m)
+0.75S\_{\text{pop,norm}}(m)
\]

The selected weights are:

- SVD: 25%
- Popularity: 75%

The weights were selected using the validation set. The hybrid was subsequently evaluated on the final test set.

This approach combines personalized collaborative-filtering signals with a more stable popularity baseline.

## 5. Final Test Results

The following results were obtained on the reserved 20,000-rating test set, with 920 users evaluated.

| Model         | Precision@10 |  Recall@10 |    NDCG@10 |
| ------------- | -----------: | ---------: | ---------: |
| Content-Based |       0.0208 |     0.0221 |     0.0277 |
| SVD           |       0.0724 |     0.0539 |     0.0865 |
| Popularity    |       0.0859 | **0.0619** |     0.0990 |
| Hybrid        |   **0.0870** |     0.0616 | **0.1035** |

### Interpretation

**Content-based filtering**

The genre-only content-based model achieved the lowest scores among the evaluated approaches. This suggests that genre information alone does not capture enough of the preference patterns represented in this dataset.

**SVD collaborative filtering**

SVD performed substantially better than content-based filtering, indicating that latent user–movie rating patterns provide useful ranking signals.

**Popularity baseline**

Popularity achieved strong results across all three metrics. This demonstrates that a relatively simple baseline can be difficult to beat in top-N recommendation tasks.

**Hybrid recommendation**

The hybrid achieved the highest Precision@10 and NDCG@10 among the evaluated models. Its Recall@10 was slightly lower than that of the popularity baseline.

Compared with popularity, the hybrid's relative improvements were approximately:

- Precision@10: **1.28%**
- NDCG@10: **4.55%**
- Recall@10: approximately **0.48% lower**

These improvements are promising but modest. They do not establish that the hybrid will perform better on every dataset or evaluation split.

## 6. Key Findings

1. A simple popularity baseline is a strong benchmark for this dataset.
2. SVD captures useful collaborative preference patterns and outperforms the genre-only content-based model.
3. Combining popularity and SVD produces the strongest observed Precision@10 and NDCG@10 results in this experiment.
4. The hybrid does not improve every metric, so the best model depends partly on the evaluation objective.
5. Correct grouping by movie ID is essential when calculating movie-level popularity statistics.
6. Ranking evaluation is necessary because rating-prediction metrics such as RMSE and MAE do not directly measure the quality of the top recommendations.

## 7. Limitations

- The evaluation uses one fixed random train/validation/test split.
- The observed hybrid improvements are modest and have not been tested for statistical significance.
- Genre-only content representations are limited and may produce many similar recommendations.
- The dataset is relatively small compared with real-world commercial recommendation platforms.
- The candidate catalog excludes movies without training ratings, so the evaluation does not measure recommendations for entirely unrated movies.
- The current evaluation focuses on ranking relevance and does not directly measure diversity, novelty, coverage, or user satisfaction.
- Offline test performance does not guarantee that users will prefer the recommendations in a live application.

## 8. Future Improvements

Potential next steps include:

- Improve content-based features using richer movie metadata, descriptions, and keywords.
- Explore a hybrid that incorporates content-based scores in addition to SVD and popularity.
- Evaluate diversity, catalog coverage, novelty, and intra-list similarity.
- Compare results across multiple random splits or a time-based evaluation.
- Investigate confidence intervals or statistical tests to assess whether the observed gains are reliable.
- Build a FastAPI backend that serves recommendations to the CineMatch frontend.
- Add recommendation explanations, such as shared genres or similar movies.
- Evaluate the deployed system using latency, error handling, and user feedback.

## 9. Conclusion

The experiments show that recommendation quality depends on both the modeling approach and the evaluation metric. On the MovieLens 100K dataset, the hybrid combining 25% SVD and 75% popularity achieved the highest observed Precision@10 and NDCG@10, while popularity alone achieved slightly higher Recall@10.

The hybrid is therefore a promising candidate for the CineMatch application, although further validation is needed before claiming a consistent improvement over the baseline.

The project demonstrates an end-to-end model evaluation workflow, including data splitting, hyperparameter selection, ranking metrics, baseline comparisons, and analysis of model limitations.
