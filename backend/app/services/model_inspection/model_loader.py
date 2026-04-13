"""
model_loader.py
===============
Production-safe model loader for Layer 2 model inspection.

Supports:
- .pkl
- .pickle
- .joblib
- .onnx

WARNING:
Deserializing pickle/joblib is unsafe for untrusted files.
Only use in trusted environments.
"""

from __future__ import annotations

import pickle
import joblib
from pathlib import Path
from typing import Any

try:
    from sklearn.utils.validation import check_is_fitted
except Exception:
    check_is_fitted = None


SUPPORTED_EXTENSIONS = {".joblib", ".pkl", ".pickle", ".onnx"}


class ModelLoadError(Exception):
    pass


def load_model(model_path: str | Path) -> Any:
    path = Path(model_path)

    if not path.exists():
        raise ModelLoadError(f"Model file not found: {path}")

    if not path.is_file():
        raise ModelLoadError(f"Provided model path is not a file: {path}")

    suffix = path.suffix.lower()

    if suffix not in SUPPORTED_EXTENSIONS:
        raise ModelLoadError(
            f"Unsupported model file extension '{suffix}'. "
            f"Supported: {sorted(SUPPORTED_EXTENSIONS)}"
        )

    model = _deserialize_model(path, suffix)
    _validate_interface(model, path)
    _validate_fitted_state(model, path)

    return model


def _deserialize_model(path: Path, suffix: str) -> Any:
    if suffix == ".joblib":
        return joblib.load(path)

    if suffix in {".pkl", ".pickle"}:
        with open(path, "rb") as fh:
            return pickle.load(fh)

    if suffix == ".onnx":
        try:
            import onnxruntime as ort
        except ImportError:
            raise ModelLoadError(
                "onnxruntime is required for .onnx models. "
                "Install using: pip install onnxruntime"
            )
        return ort.InferenceSession(str(path))

    raise ModelLoadError(f"Unsupported model type: {suffix}")


def _validate_interface(model: Any, path: Path):
    if model.__class__.__name__ == "InferenceSession":
        return

    if not callable(getattr(model, "predict", None)):
        raise ModelLoadError(
            f"Loaded object from '{path.name}' does not support predict()."
        )


def _validate_fitted_state(model: Any, path: Path):
    if model.__class__.__name__ == "InferenceSession":
        return

    if check_is_fitted is not None:
        try:
            check_is_fitted(model)
            return
        except Exception:
            pass

    fitted_indicators = (
        "classes_",
        "n_features_in_",
        "feature_names_in_",
        "coef_",
        "estimators_",
        "tree_",
    )

    if not any(hasattr(model, attr) for attr in fitted_indicators):
        raise ModelLoadError(
            f"Loaded object from '{path.name}' does not appear to be a trained model."
        )


def extract_model_metadata(model: Any) -> dict:
    metadata = {
        "model_type": type(model).__name__,
        "has_predict": callable(getattr(model, "predict", None)),
        "has_predict_proba": callable(getattr(model, "predict_proba", None)),
        "feature_names_in": None,
        "n_features_in": None,
        "classes": None,
    }

    if model.__class__.__name__ == "InferenceSession":
        metadata["model_type"] = "ONNX InferenceSession"
        try:
            metadata["onnx_inputs"] = [i.name for i in model.get_inputs()]
            metadata["onnx_outputs"] = [o.name for o in model.get_outputs()]
        except Exception:
            pass
        return metadata

    if hasattr(model, "feature_names_in_"):
        try:
            metadata["feature_names_in"] = [str(c) for c in model.feature_names_in_]
        except Exception:
            pass

    if hasattr(model, "n_features_in_"):
        try:
            metadata["n_features_in"] = int(model.n_features_in_)
        except Exception:
            pass

    if hasattr(model, "classes_"):
        try:
            metadata["classes"] = [str(c) for c in model.classes_]
        except Exception:
            pass

    return metadata