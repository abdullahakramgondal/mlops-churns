# Module 7, Session 1: Answers (MLflow + DVC)

## 1. Lecture questions (notebook gap)

1. **Which data trained the model?** With a notebook you often cannot say. With DVC, `dvc.lock` stores a hash of every input and output, so the exact data is known.
2. **Which settings produced the best score?** MLflow stores the parameters of every run next to its metrics.
3. **Can someone else get the same result tomorrow?** Yes. Seeds are fixed (`random_state: 42`), versions are pinned in `requirements.txt`, settings live in `params.yaml`, and `dvc repro` rebuilds the pipeline.

## 2. Data inspection (Step 4)

| Check | Result |
|---|---|
| Shape of raw data | (7043, 21) |
| Type of `TotalCharges` | `object` (text) |
| Blank `TotalCharges` values | 11 |
| Churn counts | No = 5174, Yes = 1869 |

After cleaning: 7043 raw rows -> 7032 clean rows. Split: 5625 train rows, 1407 test rows.

## 3. Cleaning steps (TODO S1.1 to S1.4)

- S1.1 `drop_duplicates()` removes exact duplicate rows.
- S1.2 `pd.to_numeric(..., errors="coerce")` turns `TotalCharges` into numbers; blanks become NaN.
- S1.3 `dropna(subset=["TotalCharges"])` drops the rows with missing `TotalCharges`.
- S1.4 `map({"Yes": 1, "No": 0})` converts the target `Churn` to 1/0.

Result: `pytest -q tests/test_prepare.py` gives 3 passed.

## 4. MLflow single run (TODO S1.5 to S1.7)

Run `dvc-pipeline` in experiment `churn-prediction` shows 6 parameters (C, max_depth, min_samples_leaf, model, n_estimators, random_state), 4 metrics (accuracy, precision, recall, f1) and a `model` artifact.
Result with the original settings: accuracy 0.748, precision 0.517, recall 0.781, F1 0.622.

## 5. Ten experiments (TODO S1.8 and S1.9)

| Run | Model | n_estimators | max_depth | Extra | F1 | Recall |
|---|---|---|---|---|---|---|
| exp-01 | random_forest | 50 | 4 | | 0.596 | 0.778 |
| exp-02 | random_forest | 100 | 6 | | 0.607 | 0.791 |
| exp-03 | random_forest | 200 | 8 | | 0.622 | 0.781 |
| **exp-04** | **random_forest** | **300** | **10** | | **0.629** | 0.765 |
| exp-05 | random_forest | 200 | 12 | | 0.619 | 0.749 |
| exp-06 | random_forest | 200 | 8 | min_samples_leaf=1 | 0.619 | 0.765 |
| exp-07 | random_forest | 200 | 8 | min_samples_leaf=20 | 0.621 | 0.794 |
| exp-08 | logistic_regression | - | - | C=0.1 | 0.606 | 0.794 |
| exp-09 | logistic_regression | - | - | C=1.0 | 0.603 | 0.802 |
| exp-10 | logistic_regression | - | - | C=10 | 0.603 | 0.802 |

**Chosen run:** I chose exp-04 because it has the highest F1 (0.629) among all 10 runs. Its settings (`n_estimators: 300`, `max_depth: 10`) were copied into `params.yaml`.

Note: exp-09 and exp-10 are identical because for logistic regression, C=1 and C=10 lead to almost the same model.

**Discussion: is the highest F1 always the best choice?**
No. F1 balances precision and recall, but the business may care more about one of them. If catching as many churners as possible matters most, a run with higher recall (exp-09/10, recall 0.802) may be preferred, at the cost of lower precision (0.483), meaning more false alarms. The best model depends on the cost of a missed churner versus a wrong alert.

## 6. DVC pipeline (TODO S1.10 and S1.11)

- `dvc dag` shows 4 stages: get_data -> prepare -> train -> evaluate.
- `dvc repro` runs all 4 stages and creates `dvc.lock`.
- `dvc metrics show`: accuracy 0.7605, F1 0.6293, precision 0.5346, recall 0.7647.

## 7. Reproducibility proof (Step 10)

- (a) Second `dvc repro`: every stage says "didn't change, skipping".
- (b) Changed `max_depth` from 10 to 6: `dvc params diff` showed 10 -> 6. `dvc repro` re-ran only `train` and `evaluate`. `dvc metrics diff`: F1 0.6293 -> 0.6082 (-0.0211), recall +0.0241. Setting it back to 10 reused the cached result.
- (c) Remote: `dvc remote add -d localstore ../dvc-storage`, `dvc push` (5 files pushed), deleted `data/raw/churn.csv`, `dvc pull` restored it.

## 8. Wrap-up questions

1. **MLflow comparison and chosen run:** see section 5. exp-04 was chosen for the highest F1.
2. **`dvc repro` twice:** the second run skips every stage because no dependency, parameter or output changed (hashes in `dvc.lock` match).
3. **`params.yaml` vs `dvc.yaml`:** `params.yaml` holds the settings (values you tune), while `dvc.yaml` defines the pipeline (stages, commands, dependencies and outputs).

## 9. Troubleshooting notes

- Run commands from the repo root using `python -m src.xxx`.
- `pathspec==0.12.1` is pinned because newer versions break this DVC version.
- If `dvc dag` opens a pager, press `q`.
