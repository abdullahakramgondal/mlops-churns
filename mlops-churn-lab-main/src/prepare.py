"""Stage 2: basic cleaning with pandas, then train/test split."""
import os

import pandas as pd
from sklearn.model_selection import train_test_split

from src.config import FEATURES, PROCESSED_DIR, TARGET, load_params


def clean(df: pd.DataFrame) -> pd.DataFrame:
    """Return a cleaned copy of the raw churn table."""
    df = df.copy()

    # TODO S1.1: Remove exact duplicate rows.
    # Hint: pandas has a one-line method for this.
    pass

    # TODO S1.2: 'TotalCharges' is stored as text and has blank strings (" ").
    # Convert it to numbers; blanks should become NaN.
    # Hint: pd.to_numeric(..., errors="coerce")
    pass

    # TODO S1.3: Drop rows where TotalCharges is missing.
    # Hint: df.dropna(subset=[...])
    pass

    # TODO S1.4: Convert the target 'Churn' from "Yes"/"No" to 1/0.
    # Hint: df[TARGET].map({...})
    pass

    # Keep only the columns the model uses (customerID etc. are dropped).
    return df[FEATURES + [TARGET]]


def main():
    params = load_params()["data"]
    raw = pd.read_csv(params["raw_path"])
    df = clean(raw)
    print(f"Raw rows: {len(raw)}  ->  Clean rows: {len(df)}")

    train_df, test_df = train_test_split(
        df,
        test_size=params["test_size"],
        random_state=params["random_state"],
        stratify=df[TARGET],
    )
    os.makedirs(PROCESSED_DIR, exist_ok=True)
    train_df.to_csv(f"{PROCESSED_DIR}/train.csv", index=False)
    test_df.to_csv(f"{PROCESSED_DIR}/test.csv", index=False)
    print(f"Train: {len(train_df)} rows, Test: {len(test_df)} rows")


if __name__ == "__main__":
    main()
