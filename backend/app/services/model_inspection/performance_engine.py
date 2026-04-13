from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
)

def compute_performance_metrics(y_true, y_pred, y_prob=None):
    metrics = {
        "accuracy": round(float(accuracy_score(y_true, y_pred)), 4),
        "precision": round(float(precision_score(y_true, y_pred, average="binary", zero_division=0)), 4),
        "recall": round(float(recall_score(y_true, y_pred, average="binary", zero_division=0)), 4),
        "f1_score": round(float(f1_score(y_true, y_pred, average="binary", zero_division=0)), 4),
    }

    if y_prob is not None:
        try:
            metrics["roc_auc"] = round(float(roc_auc_score(y_true, y_prob)), 4)
        except Exception:
            metrics["roc_auc"] = None
    else:
        metrics["roc_auc"] = None

    return metrics