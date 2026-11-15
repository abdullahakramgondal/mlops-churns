# Module 7, Session 2: Answers (FastAPI + Docker)

## 1. Lecture questions

- **Why wrap a model in an API?** A model file is only usable by someone with Python, the right libraries and your code. An API lets any app send JSON and get a prediction back.
- **Why does Pydantic matter?** It validates every request. Wrong or missing fields are rejected with HTTP 422 before our code runs.
- **Training-serving consistency:** the API loads the same sklearn Pipeline (preprocessing + model) saved in Session 1, so transforms are identical in training and serving.
- **Why Docker?** It packages code, libraries and the model into an image that runs the same everywhere (laptop, Hugging Face, Azure).

## 2. Step 2: the API contract (`api/schemas.py`)

1. **How many input fields?** 9 (tenure, MonthlyCharges, TotalCharges, SeniorCitizen, Contract, InternetService, PaymentMethod, PaperlessBilling, TechSupport).
2. **Allowed values for `Contract`:** `"Month-to-month"`, `"One year"`, `"Two year"`.
3. **What does `ge=0` mean on `tenure`?** "Greater than or equal to 0". Negative tenure is rejected (the schema also limits it with `le=100`).
4. **Response fields:** `churn` (bool) and `churn_probability` (float).

## 3. Step 3: API code (TODO S2.1 to S2.4)

- S2.1 `model = joblib.load(MODEL_PATH)` loads the pipeline once at startup. Loading inside `predict()` would reload a file on every request and be very slow.
- S2.2 `/health` returns `{"status": "ok", "model_loaded": model is not None}`.
- S2.3 `pd.DataFrame([customer.model_dump()])` builds a one-row table.
- S2.4 `float(model.predict_proba(row)[0][1])` gives the churn probability; `churn = probability >= 0.5`.

## 4. Step 4: predictions tried in `/docs`

| Customer | churn | churn_probability |
|---|---|---|
| tenure 2, Month-to-month, Fiber optic, Electronic check, MonthlyCharges 85.5 | true | **0.8906** |
| tenure 60, Two year, DSL, Credit card (automatic), MonthlyCharges 60 | false | **0.0418** |

The long-contract, long-tenure customer has a much lower churn probability, which matches intuition.
`/version` locally returns `{"release": "local-dev"}`.

## 5. Step 5: bad requests

| Change | Status | Message |
|---|---|---|
| `"Contract": "Ten years"` | 422 | Input should be 'Month-to-month', 'One year' or 'Two year' (tested) |
| remove `tenure` | 422 | field required |
| `"tenure": -5` | 422 | must be greater than or equal to 0 |
| `"MonthlyCharges": "abc"` | 422 | not a valid number |

**Discussion: what happens without validation if someone sends `"Contract": "Ten years"`?**
The one-hot encoder is created with `handle_unknown="ignore"`, so it would silently ignore the unknown value and the model would return a wrong answer with no error. Validation makes the failure loud and visible.

## 6. Step 6: tests (TODO S2.5)

```python
def test_invalid_category_rejected():
    bad = {**GOOD, "Contract": "Ten years"}
    assert client.post("/predict", json=bad).status_code == 422
```

`pytest -q` gives **7 passed** (3 cleaning tests from Session 1 + 4 API tests).

## 7. Steps 7 and 8: Dockerfile and container

- Requirements are copied and installed before the code. Docker caches each line, so if only code changes the slow `pip install` is skipped.
- Port 7860 is what Hugging Face expects and it is reused for Azure.
- `docker build -t churn-api .` succeeded.
- `docker run --rm -p 7860:7860 churn-api` ran the container.
- `python scripts/smoke_test.py http://127.0.0.1:7860`:
  - HEALTH: `{'status': 'ok', 'model_loaded': True}`
  - PREDICT: `{'churn': True, 'churn_probability': 0.8906}`
  - VERSION: `{'release': 'local-dev'}`
  - **SMOKE TEST PASSED**

## 8. Step 9: release folder

`bash scripts/build_release.sh` created `release/` containing `api/`, `models/model.joblib`, `models/release.json`, `requirements-serving.txt`, `Dockerfile` and `README.md`. This is the exact folder that would be deployed later. `release/` is git-ignored.

## 9. Wrap-up questions

1. **Prediction from the Docker container:** shown on port 7860 (0.8906, churn = true).
2. **A bad request returning 422 and why that is good:** `"Contract": "Ten years"` returns 422. Good because garbage input is rejected clearly instead of producing a silently wrong prediction.
3. **Why `requirements-serving.txt` and not `requirements.txt`?** Serving only needs the libraries the API uses at runtime (scikit-learn, pandas, numpy, joblib, fastapi, uvicorn, pydantic). MLflow, DVC and test tools are not needed, so the image is smaller and safer.

## 10. Troubleshooting notes

- `test_health` failing with `KeyError: 'model_loaded'` meant the branch still had the old placeholder `api/main.py`. Fix: pull the latest `dev` before creating a new branch.
- "failed to connect to the docker API": start Docker Desktop and wait until the engine is running.
