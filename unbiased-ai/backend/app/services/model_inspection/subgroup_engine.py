from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix


def compute_subgroup_performance(
    df,
    sensitive_col: str,
    y_true_col: str,
    y_pred_col: str,
    positive_label=1,
):
    results = []

    grouped = df.groupby(sensitive_col, dropna=False)

    for group_name, group_df in grouped:
        if len(group_df) == 0:
            continue

        y_true = group_df[y_true_col]
        y_pred = group_df[y_pred_col]

        try:
            acc = accuracy_score(y_true, y_pred)
            prec = precision_score(y_true, y_pred, pos_label=positive_label, zero_division=0)
            rec = recall_score(y_true, y_pred, pos_label=positive_label, zero_division=0)
            f1 = f1_score(y_true, y_pred, pos_label=positive_label, zero_division=0)

            labels = [x for x in sorted(set(y_true.unique()).union(set(y_pred.unique())))]

            if len(labels) == 2 and positive_label in labels:
                negative_label = [l for l in labels if l != positive_label][0]
                cm = confusion_matrix(y_true, y_pred, labels=[negative_label, positive_label])
                tn, fp, fn, tp = cm.ravel()

                fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
                fnr = fn / (fn + tp) if (fn + tp) > 0 else 0.0
            else:
                fpr = 0.0
                fnr = 0.0

            results.append({
                "sensitive_attribute": sensitive_col,
                "group": str(group_name),
                "n_samples": int(len(group_df)),
                "accuracy": round(float(acc), 4),
                "precision": round(float(prec), 4),
                "recall": round(float(rec), 4),
                "f1": round(float(f1), 4),
                "fpr": round(float(fpr), 4),
                "fnr": round(float(fnr), 4),
            })

        except Exception:
            continue

    return results