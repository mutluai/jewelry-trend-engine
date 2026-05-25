# Opportunity Scoring System

## Score Components (0-100 each)

| Component | Default Weight | Description |
|-----------|---------------|-------------|
| trend_velocity | 25% | How fast is interest growing? |
| cross_source | 20% | How many sources show this trend? |
| competition_density | 15% | Inverted: fewer competitors = higher score |
| novelty | 15% | How new/unseen is this in our tracking? |
| brand_fit | 15% | How well does it match our brand profile? |
| review_signal | 10% | Review count and rating signal |

**Total score = weighted sum of all components (0-100)**

## Adjusting Weights

Via dashboard: Settings → Puanlama Ağırlıkları

Via API:
```bash
PATCH /api/v1/settings/scoring-weights
{
  "trend_velocity": 0.30,
  "cross_source": 0.20,
  "competition_density": 0.10,
  "novelty": 0.20,
  "brand_fit": 0.15,
  "review_signal": 0.05
}
```

Weights are automatically normalized (don't need to sum to exactly 1.0).

## Score Interpretation

| Score | Interpretation | Action |
|-------|---------------|--------|
| 80-100 | Exceptional opportunity | Design new / restock immediately |
| 60-79 | Strong opportunity | Test small batch |
| 40-59 | Moderate signal | Monitor closely |
| 20-39 | Weak signal | Note and revisit |
| 0-19 | Not recommended | Skip |

## Running Scoring Manually

```bash
python jobs/run_scoring.py --limit 100
# With AI attribute extraction:
python jobs/run_scoring.py --limit 100 --ai
```
