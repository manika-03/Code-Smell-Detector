"""
train_model.py
--------------
One-time training script for the Code Smell severity classifier.

Run from the backend/ directory:
    python train_model.py

Outputs:
    model/classifier.pkl     - Best trained model (RF or XGB)
    model/label_encoder.pkl  - LabelEncoder for LOW/MEDIUM/HIGH
    model/features.pkl       - Feature name list
    data/synthetic_metrics.csv - Generated training dataset
"""

import os
import json
import warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
import joblib

from sklearn.ensemble        import RandomForestClassifier
from sklearn.model_selection import train_test_split, GridSearchCV, StratifiedKFold
from sklearn.preprocessing   import LabelEncoder
from sklearn.feature_selection import RFE
from sklearn.metrics         import classification_report, f1_score

try:
    from xgboost import XGBClassifier
    XGB_AVAILABLE = True
except ImportError:
    XGB_AVAILABLE = False
    print("[WARN] xgboost not found — will only train RandomForest.")

try:
    from imblearn.over_sampling import SMOTE
    SMOTE_AVAILABLE = True
except ImportError:
    SMOTE_AVAILABLE = False
    print("[WARN] imbalanced-learn not found — skipping SMOTE.")


# ────────────────────────────────────────────────────────────
#  Paths
# ────────────────────────────────────────────────────────────
BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
DATA_DIR   = os.path.join(BASE_DIR, "data")
MODEL_DIR  = os.path.join(BASE_DIR, "model")
CSV_PATH   = os.path.join(DATA_DIR, "synthetic_metrics.csv")
MODEL_PATH = os.path.join(MODEL_DIR, "classifier.pkl")
LE_PATH    = os.path.join(MODEL_DIR, "label_encoder.pkl")
FEAT_PATH  = os.path.join(MODEL_DIR, "features.pkl")

os.makedirs(DATA_DIR,  exist_ok=True)
os.makedirs(MODEL_DIR, exist_ok=True)

# ────────────────────────────────────────────────────────────
#  Feature definitions
# ────────────────────────────────────────────────────────────
FEATURES = [
    "loc",
    "cyclomatic_complexity",
    "num_functions",
    "avg_function_length",
    "max_function_length",
    "num_classes",
    "duplicate_ratio",
    "max_nesting_depth",
    "comment_ratio",
    "avg_params",
]


# ────────────────────────────────────────────────────────────
#  Step 1: Generate Synthetic Dataset
# ────────────────────────────────────────────────────────────

def rule_label(row) -> str:
    """Ground-truth labeller: mirrors rule_based_severity in analyzer.py"""
    score = 0

    # Smell checks
    if row["avg_function_length"]   > 30:    score += 1
    if row["num_functions"]          > 15:    score += 1
    if row["duplicate_ratio"]        > 0.25:  score += 1
    if row["cyclomatic_complexity"]  > 10:    score += 1
    if row["avg_params"]             > 4:     score += 1
    if row["num_classes"] >= 1 and (row["num_functions"] / max(row["num_classes"], 1)) > 12:
        score += 1

    # Extra weight for extreme values
    if row["cyclomatic_complexity"] > 15:    score += 2
    if row["cyclomatic_complexity"] > 10:    score += 1
    if row["loc"]                   > 500:   score += 1
    if row["loc"]                   > 200:   score += 1
    if row["max_nesting_depth"]     > 5:     score += 1

    if score >= 5:
        return "HIGH"
    elif score >= 2:
        return "MEDIUM"
    return "LOW"


def generate_dataset(n: int = 12000, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    print(f"[INFO] Generating {n} synthetic samples...")

    data = {
        "loc":                   rng.integers(10, 1200, n).astype(float),
        "cyclomatic_complexity":  np.clip(rng.gamma(2.5, 3.0, n), 1, 35),
        "num_functions":          rng.integers(0, 40, n).astype(float),
        "avg_function_length":    np.clip(rng.gamma(3, 8, n), 1, 150),
        "max_function_length":    np.clip(rng.gamma(4, 12, n), 1, 200),
        "num_classes":            rng.integers(0, 10, n).astype(float),
        "duplicate_ratio":        np.clip(rng.beta(1.5, 6, n), 0, 1),
        "max_nesting_depth":      rng.integers(0, 10, n).astype(float),
        "comment_ratio":          np.clip(rng.beta(2, 5, n), 0, 1),
        "avg_params":             np.clip(rng.gamma(1.5, 1.8, n), 0, 12),
    }

    # Ensure max_function_length >= avg_function_length
    data["max_function_length"] = np.maximum(
        data["max_function_length"], data["avg_function_length"]
    )

    # Add small Gaussian noise to blur rule boundaries
    for key in ["cyclomatic_complexity", "avg_function_length", "duplicate_ratio", "avg_params"]:
        noise = rng.normal(0, 0.05 * (data[key].max() - data[key].min()), n)
        data[key] = np.clip(data[key] + noise, 0, None)

    df = pd.DataFrame(data)
    df["severity"] = df.apply(rule_label, axis=1)

    print(f"[INFO] Label distribution:\n{df['severity'].value_counts()}\n")
    df.to_csv(CSV_PATH, index=False)
    print(f"[INFO] Saved dataset to: {CSV_PATH}")
    return df


# ────────────────────────────────────────────────────────────
#  Step 2: Train & Evaluate
# ────────────────────────────────────────────────────────────

def train(df: pd.DataFrame):
    X = df[FEATURES].values
    le = LabelEncoder()
    y  = le.fit_transform(df["severity"])

    print(f"[INFO] Classes: {list(le.classes_)}")

    # Train/test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # SMOTE
    if SMOTE_AVAILABLE:
        print("[INFO] Applying SMOTE...")
        smote = SMOTE(random_state=42)
        X_train, y_train = smote.fit_resample(X_train, y_train)
        print(f"[INFO] Post-SMOTE training size: {len(X_train)}")

    # Feature selection via RFE
    print("[INFO] Running RFE feature selection...")
    rf_for_rfe = RandomForestClassifier(n_estimators=50, random_state=42, n_jobs=-1)
    rfe = RFE(rf_for_rfe, n_features_to_select=8, step=1)
    rfe.fit(X_train, y_train)
    selected_features = [FEATURES[i] for i in range(len(FEATURES)) if rfe.support_[i]]
    print(f"[INFO] Selected features: {selected_features}")

    X_train_sel = X_train[:, rfe.support_]
    X_test_sel  = X_test[:,  rfe.support_]

    # ── Candidate Models ──
    candidates = {}

    # Random Forest
    print("\n[INFO] GridSearch: RandomForest...")
    rf_param_grid = {
        "n_estimators": [100, 200],
        "max_depth":    [5, 10, None],
        "min_samples_split": [2, 5],
    }
    rf = RandomForestClassifier(random_state=42, n_jobs=-1)
    rf_gs = GridSearchCV(
        rf, rf_param_grid, cv=StratifiedKFold(5),
        scoring="f1_weighted", n_jobs=-1, verbose=0
    )
    rf_gs.fit(X_train_sel, y_train)
    rf_best = rf_gs.best_estimator_
    rf_score = f1_score(y_test, rf_best.predict(X_test_sel), average="weighted")
    candidates["RandomForest"] = (rf_best, rf_score)
    print(f"       Best params: {rf_gs.best_params_}")
    print(f"       Test F1 (weighted): {rf_score:.4f}")

    # XGBoost
    if XGB_AVAILABLE:
        print("\n[INFO] GridSearch: XGBoost...")
        xgb_param_grid = {
            "n_estimators":  [100, 200],
            "learning_rate": [0.05, 0.1],
            "max_depth":     [4, 6],
        }
        xgb = XGBClassifier(
            use_label_encoder=False,
            eval_metric="mlogloss",
            random_state=42,
            n_jobs=-1,
            verbosity=0,
        )
        xgb_gs = GridSearchCV(
            xgb, xgb_param_grid, cv=StratifiedKFold(5),
            scoring="f1_weighted", n_jobs=-1, verbose=0
        )
        xgb_gs.fit(X_train_sel, y_train)
        xgb_best = xgb_gs.best_estimator_
        xgb_score = f1_score(y_test, xgb_best.predict(X_test_sel), average="weighted")
        candidates["XGBoost"] = (xgb_best, xgb_score)
        print(f"       Best params: {xgb_gs.best_params_}")
        print(f"       Test F1 (weighted): {xgb_score:.4f}")

    # ── Pick Winner ──
    best_name, (best_model, best_score) = max(candidates.items(), key=lambda x: x[1][1])
    print(f"\n[INFO] ✓ Best model: {best_name}  (F1={best_score:.4f})")

    # ── Full Classification Report ──
    X_test_final = X_test_sel if len(selected_features) == 8 else X_test
    y_pred = best_model.predict(X_test_final)
    print("\n[INFO] Classification Report:")
    print(classification_report(y_test, y_pred, target_names=le.classes_))

    # ── Save ──
    joblib.dump(best_model,      MODEL_PATH)
    joblib.dump(le,              LE_PATH)
    joblib.dump(selected_features, FEAT_PATH)

    print(f"\n[INFO] Saved model to:   {MODEL_PATH}")
    print(f"[INFO] Saved encoder to: {LE_PATH}")
    print(f"[INFO] Saved features to: {FEAT_PATH}")
    print("\n✅  Training complete!")


# ────────────────────────────────────────────────────────────
#  Entry Point
# ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    df = generate_dataset(n=12000)
    train(df)
