"""Carbon-aware temporal scheduling for the Green AI prototype.

The current project data is sampled every 5 minutes. This implementation
uses a simple, explainable rule-based temporal scheduling strategy.
"""

import pandas as pd
from .rules import should_run_now


def carbon_score(workload: float, carbon_intensity: float) -> float:
    """Workload × carbon intensity proxy used by the prototype."""
    return float(workload) * float(carbon_intensity)


def schedule(workload_df: pd.DataFrame, carbon_df: pd.DataFrame,
             capacity_factor: float = 1.25) -> pd.DataFrame:
    """Schedule flexible workload into cleaner future 5-minute slots.

    Required workload columns: timestamp, workload, workload_type
    Required carbon columns: timestamp, carbon_intensity

    ``capacity_factor`` is a simulation constraint: maximum scheduled
    workload per slot is this factor times the maximum input workload.
    Replace it with measured cloud capacity when available.
    """
    required_w = {"timestamp", "workload", "workload_type"}
    required_c = {"timestamp", "carbon_intensity"}
    missing_w = required_w - set(workload_df.columns)
    missing_c = required_c - set(carbon_df.columns)
    if missing_w:
        raise ValueError(f"Missing workload columns: {sorted(missing_w)}")
    if missing_c:
        raise ValueError(f"Missing carbon columns: {sorted(missing_c)}")

    df = (workload_df.merge(carbon_df, on="timestamp", how="inner")
          .sort_values("timestamp").reset_index(drop=True))
    if df.empty:
        raise ValueError("No matching timestamps between workload and carbon data.")

    capacity = max(float(df["workload"].max()) * capacity_factor, 1.0)
    scheduled_load = {i: 0.0 for i in range(len(df))}
    results = []

    for i, row in df.iterrows():
        workload = float(row["workload"])
        current_carbon = float(row["carbon_intensity"])
        category = row["workload_type"]
        target = i

        if not should_run_now(category):
            best_score = carbon_score(workload, current_carbon)
            for j in range(i + 1, len(df)):
                future_carbon = float(df.loc[j, "carbon_intensity"])
                if future_carbon >= current_carbon:
                    continue
                if scheduled_load[j] + workload > capacity:
                    continue
                candidate = carbon_score(workload, future_carbon)
                if candidate < best_score:
                    best_score = candidate
                    target = j

        scheduled_load[target] += workload
        scheduled_carbon = float(df.loc[target, "carbon_intensity"])
        results.append({
            "timestamp": row["timestamp"],
            "workload": workload,
            "workload_type": category,
            "scheduled_timestamp": df.loc[target, "timestamp"],
            "carbon_now": current_carbon,
            "carbon_scheduled": scheduled_carbon,
            "decision": "DEFER" if target != i else "RUN_NOW",
            "delay_minutes": (float(df.loc[target, "timestamp"] - row["timestamp"]) / 60.0),
            "carbon_score": carbon_score(workload, scheduled_carbon),
        })

    return pd.DataFrame(results)
