"""Run 10 training iterations with different settings, all logged to MLflow.

Usage:  python -m src.run_experiments
Then:   mlflow ui      ->  open http://127.0.0.1:5000 and compare runs.
"""
from src.config import load_params
from src.train import train_and_log

# Each experiment only lists what CHANGES compared with params.yaml.
# S1.8: 3 given + 7 added = 10 experiments.
EXPERIMENTS = [
    {"model": "random_forest", "n_estimators": 50, "max_depth": 4},
    {"model": "random_forest", "n_estimators": 100, "max_depth": 6},
    {"model": "random_forest", "n_estimators": 200, "max_depth": 8},
    {"model": "random_forest", "n_estimators": 300, "max_depth": 10},
    {"model": "random_forest", "n_estimators": 200, "max_depth": 12},
    {"model": "random_forest", "n_estimators": 200, "max_depth": 8, "min_samples_leaf": 1},
    {"model": "random_forest", "n_estimators": 200, "max_depth": 8, "min_samples_leaf": 20},
    {"model": "logistic_regression", "C": 0.1},
    {"model": "logistic_regression", "C": 1.0},
    {"model": "logistic_regression", "C": 10.0},
]


def main():
    base = load_params()["train"]
    print(f"Running {len(EXPERIMENTS)} experiments...")
    for i, changes in enumerate(EXPERIMENTS, start=1):
        # S1.9: start from base settings, apply this run's changes, then train
        run_params = {**base, **changes}
        train_and_log(run_params, run_name=f"exp-{i:02d}")
    print("Done. Run `mlflow ui` and compare the runs.")


if __name__ == "__main__":
    main()