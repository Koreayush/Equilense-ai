from __future__ import annotations

import pandas as pd
from typing import Any


class SchemaValidationError(Exception):
    """Raised when evaluation data does not match model input expectations."""


def validate_and_prepare_features(model: Any, df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """
    Validate evaluation dataframe against model expectations and align feature columns.

    Supports:
    - sklearn models / pipelines with feature_names_in_
    - estimators with n_features_in_
    - ONNX sessions (best-effort shape validation)

    Returns
    -------
    X_aligned : pd.DataFrame
        Feature matrix aligned to expected model schema.
    metadata : dict
        Schema diagnostics for reporting.
    """

    metadata = {
        "input_columns_received": list(df.columns),
        "expected_columns": None,
        "dropped_extra_columns": [],
        "missing_expected_columns": [],
        "schema_aligned": True,
    }

    # ─────────────────────────────────────────────────────────────
    # ONNX handling
    # ─────────────────────────────────────────────────────────────
    if model.__class__.__name__ == "InferenceSession":
        try:
            input_meta = model.get_inputs()[0]
            expected_shape = input_meta.shape
            metadata["expected_columns"] = f"ONNX input shape: {expected_shape}"

            # ONNX usually does not preserve column names reliably.
            # Best-effort: only ensure dataframe is numeric.
            X = df.copy()

            for col in X.columns:
                X[col] = pd.to_numeric(X[col], errors="coerce")

            if X.isna().any().any():
                raise SchemaValidationError(
                    "ONNX model input contains non-numeric or invalid values after coercion."
                )

            return X, metadata

        except Exception as e:
            raise SchemaValidationError(f"Failed ONNX schema validation: {e}")

    # ─────────────────────────────────────────────────────────────
    # sklearn / pipeline feature-name alignment
    # ─────────────────────────────────────────────────────────────
    expected_cols = None

    if hasattr(model, "feature_names_in_"):
        try:
            expected_cols = [str(c) for c in model.feature_names_in_]
        except Exception:
            expected_cols = None

    if expected_cols:
        metadata["expected_columns"] = expected_cols

        missing = [c for c in expected_cols if c not in df.columns]
        extra = [c for c in df.columns if c not in expected_cols]

        metadata["missing_expected_columns"] = missing
        metadata["dropped_extra_columns"] = extra

        if missing:
            metadata["schema_aligned"] = False
            raise SchemaValidationError(
                f"Evaluation dataset is missing required model input columns: {missing}"
            )

        X = df[expected_cols].copy()
        return X, metadata

    # ─────────────────────────────────────────────────────────────
    # sklearn fallback using n_features_in_
    # ─────────────────────────────────────────────────────────────
    if hasattr(model, "n_features_in_"):
        try:
            expected_n = int(model.n_features_in_)
            metadata["expected_columns"] = f"{expected_n} unnamed features"

            if df.shape[1] != expected_n:
                metadata["schema_aligned"] = False
                raise SchemaValidationError(
                    f"Model expects {expected_n} input features, but received {df.shape[1]}."
                )

            return df.copy(), metadata
        except Exception as e:
            raise SchemaValidationError(f"Feature-count validation failed: {e}")

    # ─────────────────────────────────────────────────────────────
    # final fallback
    # ─────────────────────────────────────────────────────────────
    return df.copy(), metadata