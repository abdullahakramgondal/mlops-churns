"""FastAPI service that serves the trained churn model.

Run locally:  uvicorn api.main:app --reload
Then open:    http://127.0.0.1:8000/docs
"""
import json
import os

import joblib
import pandas as pd
from fastapi import FastAPI

from api.schemas import Customer, Prediction

MODEL_PATH = os.getenv("MODEL_PATH", "models/model.joblib")
RELEASE_PATH = os.getenv("RELEASE_PATH", "models/release.json")

app = FastAPI(title="Churn Prediction API", version="1.0")

# S2.1: load the trained pipeline ONCE, when the app starts
model = joblib.load(MODEL_PATH)


@app.get("/")
def root():
    return {"message": "Churn API is running. Go to /docs to try it."}


@app.get("/health")
def health():
    # S2.2
    return {"status": "ok", "model_loaded": model is not None}


@app.get("/version")
def version():
    """Tells you WHICH model/code release is running (filled in by CI)."""
    if os.path.exists(RELEASE_PATH):
        with open(RELEASE_PATH) as f:
            return json.load(f)
    return {"release": "local-dev"}


@app.post("/predict", response_model=Prediction)
def predict(customer: Customer):
    # S2.3: one-row DataFrame from the request
    row = pd.DataFrame([customer.model_dump()])

    # S2.4: churn probability (class 1) and 0/1 decision
    probability = float(model.predict_proba(row)[0][1])

    return Prediction(churn=probability >= 0.5,
                      churn_probability=round(probability, 4))