"""Basic cleaning and observed SOH/RUL labels."""

import numpy as np
import pandas as pd


def clean_data(raw):
    """Remove duplicates/invalid discharges while retaining valid capacity recovery."""
    data = raw.copy()
    key = ["dataset", "battery", "cycle"]
    # Quarantine contradictory copies instead of arbitrarily keeping one.
    values = data.groupby(key)[["capacity_Ah", "rated_Ah", "time"]].transform("nunique")
    conflict = values.gt(1).any(axis=1)
    data["reason"] = ""
    data.loc[conflict, "reason"] = "conflicting_duplicate"
    duplicate = data.duplicated(key, keep="first") & ~conflict
    data.loc[duplicate, "reason"] = "duplicate"
    invalid = (
        ~np.isfinite(data["capacity_Ah"])
        | (data["capacity_Ah"] <= 0)
        | ~np.isfinite(data["rated_Ah"])
        | (data["rated_Ah"] <= 0)
        | ~data["complete"]
    )
    data.loc[invalid & data["reason"].eq(""), "reason"] = "invalid_or_incomplete"
    summary = (
        data.groupby(["dataset", "battery"])
        .agg(
            original_rows=("reason", "size"),
            removed_rows=("reason", lambda x: x.ne("").sum()),
        )
        .reset_index()
    )
    summary["kept_rows"] = summary["original_rows"] - summary["removed_rows"]
    clean = data[data["reason"].eq("")].copy()
    clean = clean.sort_values(key).reset_index(drop=True)
    clean["SOH"] = clean["capacity_Ah"] / clean["rated_Ah"]
    # Do not renumber cycles after cleaning, smooth labels, or delete recovery.
    return clean.drop(columns=["reason"]), data[data["reason"].ne("")], summary


def add_rul(data, threshold=0.8):
    """Label the first observed crossing. Unobserved endpoints stay unknown."""
    if not 0 < threshold < 1:
        raise ValueError("threshold must be a fraction between 0 and 1")
    result = data.copy()
    result["RUL"] = np.nan
    result["label_status"] = "right_censored"
    endpoints = []
    for (dataset, battery), group in result.groupby(["dataset", "battery"]):
        crossing = group[group["SOH"] <= threshold]
        eol = crossing["cycle"].iloc[0] if len(crossing) else np.nan
        status = "observed" if len(crossing) else "right_censored"
        if group["SOH"].iloc[0] <= threshold:
            status = "initial_below_threshold"
        result.loc[group.index, "label_status"] = status
        if status == "observed":
            before = group[group["cycle"] < eol].index
            result.loc[before, "RUL"] = eol - result.loc[before, "cycle"]
        endpoints.append(
            {
                "dataset": dataset,
                "battery": battery,
                "threshold": threshold,
                "EOL": eol,
                "status": status,
            }
        )
    return result, pd.DataFrame(endpoints)
