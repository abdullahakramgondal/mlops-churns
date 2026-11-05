"""Stage 3: train ONE model using params.yaml and log it to MLflow."""
import os

import joblib
import mlflow
import pandas as pd
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score

from src.config import FEATURES, MODEL_PATH, PROCESSED_DIR, TARGET, load_params
from src.model import build_pipeline

EXPERIMENT_NAME = "churn-prediction"


def train_and_log(train_params: dict, run_name: str = None) -> dict:
    """Train a model, log params/metrics/model to MLflow, return metrics."""
    train_df = pd.read_csv(f"{PROCESSED_DIR}/train.csv")
    test_df = pd.read_csv(f"{PROCESSED_DIR}/test.csv")
    X_train, y_train = train_df[FEATURES], train_df[TARGET]
    X_test, y_test = test_df[FEATURES], test_df[TARGET]

    mlflow.set_experiment(EXPERIMENT_NAME)
    with mlflow.start_run(run_name=run_name):
        # TODO S1.5: Log every training parameter to MLflow.
        # Hint: mlflow.log_params(<a dict>)
        pass

        pipeline = build_pipeline(train_params)
        pipeline.fit(X_train, y_train)
        preds = pipeline.predict(X_test)

        metrics = {
            "accuracy": accuracy_score(y_test, preds),
            "precision": precision_score(y_test, preds),
            "recall": recall_score(y_test, preds),
            "f1": f1_score(y_test, preds),
        }

        # TODO S1.6: Log the metrics dictionary to MLflow.
        # Hint: mlflow.log_metrics(<a dict>)
        pass

        # TODO S1.7: Log the fitted pipeline as an MLflow model.
        # Hint: mlflow.sklearn.log_model(<model>, artifact_path="model")
        pass

    print(f"[{run_name}] " + "  ".join(f"{k}={v:.3f}" for k, v in metrics.items()))
    return {"pipeline": pipeline, "metrics": metrics}


def main():
    train_params = load_params()["train"]
    result = train_and_log(train_params, run_name="dvc-pipeline")
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    joblib.dump(result["pipeline"], MODEL_PATH)
    print(f"Saved model to {MODEL_PATH}")


if __name__ == "__main__":
    main()
