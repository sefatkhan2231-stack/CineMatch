## Initial Recommendation Ranking Evaluation

**Dataset:** MovieLens 100K  
**Split:** 80% training / 20% test  
**Random seed:** 42  
**Relevance threshold:** Rating ≥ 4  
**Ranking cutoff:** K = 10  
**Users evaluated:** 924

| Model               | Precision@10 | Recall@10 | NDCG@10 |
| ------------------- | -----------: | --------: | ------: |
| SVD                 |       0.0689 |    0.0495 |  0.0782 |
| Popularity baseline |       0.0791 |    0.0584 |  0.0904 |

### Initial findings

The popularity baseline outperformed SVD across all three ranking metrics in this experiment. This demonstrates that a simple baseline can be competitive with a more complex recommendation algorithm.

These results are preliminary and apply to the current evaluation setup. Candidate-set consistency, model hyperparameters, and additional train/test splits should be investigated before drawing broader conclusions.
