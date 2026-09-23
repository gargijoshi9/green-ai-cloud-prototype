# scheduler/scheduler.py

from __future__ import annotations

import pandas as pd

from .rules import is_flexible


def carbon_score(workload: float, carbon_intensity: float) -> float:
    """
    Relative carbon-impact score.

    This is NOT physical CO2e because the current workload value is
    CPU workload rather than measured electricity consumption in kWh.
    """
    return float(workload) * float(carbon_intensity)


def carbon_aware_schedule(
    workload_df: pd.DataFrame,
    carbon_df: pd.DataFrame,
    capacity_factor: float = 1.25,
    max_delay_minutes: int = 360,
) -> pd.DataFrame:
    """
    Schedule each workload at its original time or, for flexible work,
    at a later lower-carbon feasible slot.

    Required workload columns:
        timestamp, workload, workload_type

    Required carbon columns:
        timestamp, carbon_intensity_gco2_kwh

    The scheduler only shifts rows whose workload_type is
    'Delay-insensitive'. Non-flexible rows always run now.
    """
    workload_df = workload_df.copy()
    carbon_df = carbon_df.copy()

    workload_df["timestamp"] = pd.to_datetime(
        workload_df["timestamp"], utc=True
    )
    carbon_df["timestamp"] = pd.to_datetime(
        carbon_df["timestamp"], utc=True
    )

    required_workload = {"timestamp", "workload", "workload_type"}
    required_carbon = {"timestamp", "carbon_intensity_gco2_kwh"}

    missing = required_workload - set(workload_df.columns)
    if missing:
        raise ValueError(f"Missing workload columns: {sorted(missing)}")

    missing = required_carbon - set(carbon_df.columns)
    if missing:
        raise ValueError(f"Missing carbon columns: {sorted(missing)}")

    if workload_df.empty or carbon_df.empty:
        raise ValueError("Workload and carbon datasets must not be empty.")

    workload_df = workload_df.sort_values("timestamp").reset_index(drop=True)
    carbon_df = (
        carbon_df.sort_values("timestamp")
        .drop_duplicates("timestamp")
        .reset_index(drop=True)
    )

    max_workload = float(workload_df["workload"].max())
    capacity = max_workload * capacity_factor

    # Load already assigned to each execution slot.
    scheduled_load: dict[pd.Timestamp, float] = {}

    results = []

    for _, job in workload_df.iterrows():
        original_time = job["timestamp"]
        workload = float(job["workload"])
        workload_type = str(job["workload_type"])

        # Exact timestamp if available; otherwise nearest carbon point.
        exact = carbon_df[carbon_df["timestamp"] == original_time]
        if not exact.empty:
            current_carbon = float(
                exact.iloc[0]["carbon_intensity_gco2_kwh"]
            )
        else:
            idx = (
                carbon_df["timestamp"] - original_time
            ).abs().idxmin()
            current_carbon = float(
                carbon_df.loc[idx, "carbon_intensity_gco2_kwh"]
            )

        current_score = carbon_score(workload, current_carbon)

        # Non-flexible workloads execute immediately.
        if not is_flexible(workload_type):
            scheduled_time = original_time
            scheduled_carbon = current_carbon
            decision = "RUN_NOW"

        else:
            latest_allowed = original_time + pd.Timedelta(
                minutes=max_delay_minutes
            )
            future = carbon_df[
                (carbon_df["timestamp"] > original_time)
                & (carbon_df["timestamp"] <= latest_allowed)
            ]

            candidates = []

            for _, slot in future.iterrows():
                candidate_time = slot["timestamp"]
                candidate_carbon = float(
                    slot["carbon_intensity_gco2_kwh"]
                )

                used = scheduled_load.get(candidate_time, 0.0)

                # Respect the simple simulated capacity constraint.
                if used + workload > capacity:
                    continue

                # Only shift to a lower-carbon slot.
                if candidate_carbon < current_carbon:
                    candidates.append(
                        (
                            carbon_score(workload, candidate_carbon),
                            candidate_time,
                            candidate_carbon,
                        )
                    )

            if candidates:
                _, scheduled_time, scheduled_carbon = min(
                    candidates, key=lambda x: x[0]
                )
                decision = "SHIFTED"
            else:
                scheduled_time = original_time
                scheduled_carbon = current_carbon
                decision = "RUN_NOW_NO_BETTER_SLOT"

        scheduled_load[scheduled_time] = (
            scheduled_load.get(scheduled_time, 0.0) + workload
        )

        scheduled_score = carbon_score(workload, scheduled_carbon)

        delay_minutes = (
            scheduled_time - original_time
        ).total_seconds() / 60.0

        results.append(
            {
                "timestamp": original_time,
                "workload": workload,
                "workload_type": workload_type,
                "scheduled_timestamp": scheduled_time,
                "carbon_now_gco2_kwh": current_carbon,
                "carbon_scheduled_gco2_kwh": scheduled_carbon,
                "carbon_score_now": current_score,
                "carbon_score_scheduled": scheduled_score,
                "decision": decision,
                "delay_minutes": delay_minutes,
            }
        )

    return pd.DataFrame(results)
