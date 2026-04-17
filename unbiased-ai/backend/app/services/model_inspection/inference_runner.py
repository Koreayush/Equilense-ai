import numpy as np
import pandas as pd


class InferenceError(Exception):
    pass


def run_inference(model, X: pd.DataFrame, model_path: str):
    """
    Runs inference on sklearn / joblib / pickle / ONNX models.

    Returns:
        y_pred, y_prob
    """
    try:
        if model_path.endswith(".onnx"):
            return _run_onnx_inference(model, X)

        return _run_sklearn_inference(model, X)

    except Exception as e:
        raise InferenceError(f"Inference failed: {str(e)}")


def _run_sklearn_inference(model, X: pd.DataFrame):
    """
    Runs inference for sklearn-compatible models.
    Supports:
    - Pipeline
    - LogisticRegression
    - RandomForest
    - XGBoost sklearn wrapper
    - etc.
    """

    if not hasattr(model, "predict"):
        raise ValueError("Model does not support predict().")

    # -----------------------------
    # Predict labels
    # -----------------------------
    y_pred = model.predict(X)
    y_pred = np.asarray(y_pred).flatten()

    # -----------------------------
    # Predict probabilities (safe)
    # -----------------------------
    y_prob = None

    if hasattr(model, "predict_proba"):
        try:
            probs = model.predict_proba(X)
            probs = np.asarray(probs)

            if len(probs.shape) == 2 and probs.shape[1] > 1:
                y_prob = probs[:, 1]
            elif len(probs.shape) == 1:
                y_prob = probs

        except Exception:
            # If predict_proba fails, continue without probabilities
            y_prob = None

    return y_pred, y_prob


def _run_onnx_inference(model, X: pd.DataFrame):
    """
    Runs inference for ONNX Runtime session.
    """
    input_name = model.get_inputs()[0].name
    outputs = model.run(None, {input_name: X.astype(np.float32).values})

    y_pred = outputs[0]

    if isinstance(y_pred, list):
        y_pred = np.array(y_pred)

    y_pred = np.asarray(y_pred).flatten()

    y_prob = None
    if len(outputs) > 1:
        probs = outputs[1]

        if isinstance(probs, list):
            probs = np.array(probs)

        probs = np.asarray(probs)

        if len(probs.shape) == 2 and probs.shape[1] > 1:
            y_prob = probs[:, 1]
        elif len(probs.shape) == 1:
            y_prob = probs

    return y_pred, y_prob