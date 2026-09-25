# scheduler/scheduler.py

from __future__ import annotations

import pandas as pd

try:
    from .rules import is_flexible
except ImportError:
    from rules import is_flexible


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


def load_workload_with_forecast(data_dir=None) -> pd.DataFrame:
    """
    Loads historical workload alongside the model's forecast output
    so the scheduler acts on upcoming forecasted demand in addition to historical data.
    """
    from pathlib import Path

    if data_dir is None:
        data_dir = Path(__file__).resolve().parent.parent / "dataset" / "processed"
    else:
        data_dir = Path(data_dir)

    workload_df = pd.read_csv(data_dir / "workload_by_category.csv")
    forecast_path = data_dir / "forecast_output.csv"

    if forecast_path.exists():
        forecast_df = pd.read_csv(forecast_path)
        ts_path = data_dir / "workload_timeseries.csv"
        avg_vm_count = (
            pd.read_csv(ts_path)["vm_count"].mean()
            if ts_path.exists()
            else 1.0
        )
        if forecast_df["forecast"].mean() < 1000:
            scaled_forecast = forecast_df["forecast"] * avg_vm_count
        else:
            scaled_forecast = forecast_df["forecast"]

        max_hist_time = workload_df["timestamp"].max()
        future_timestamps = max_hist_time + 300 + (forecast_df.index * 300)

        # Allocate future forecast across flexible (Delay-insensitive: ~53%) and interactive (~47%)
        forecast_flexible = pd.DataFrame({
            "timestamp": future_timestamps,
            "cpu_avg": scaled_forecast * 0.53,
            "vm_category": "Delay-insensitive",
        })
        forecast_interactive = pd.DataFrame({
            "timestamp": future_timestamps,
            "cpu_avg": scaled_forecast * 0.47,
            "vm_category": "Interactive",
        })
        workload_df = pd.concat(
            [workload_df, forecast_flexible, forecast_interactive],
            ignore_index=True,
        )

    return workload_df


if __name__ == "__main__":
    from pathlib import Path

    root = Path(__file__).resolve().parent.parent
    data_dir = root / "dataset" / "processed"
    carbon_path = root / "carbon_data" / "india_carbon_intensity_all_states.csv"

    print("Loading historical workload combined with prediction forecast...")
    workload_df = load_workload_with_forecast(data_dir)

    carbon_df = pd.read_csv(carbon_path)
    carbon_df["timestamp"] = pd.to_datetime(carbon_df["timestamp"], utc=True)
    carbon_df = carbon_df.groupby(
        "timestamp", as_index=False
    )["carbon_intensity_gco2_kwh"].mean()

    carbon_start = carbon_df["timestamp"].min()
    workload_df["timestamp"] = carbon_start + pd.to_timedelta(
        workload_df["timestamp"], unit="s"
    )
    workload_df = workload_df.rename(
        columns={"cpu_avg": "workload", "vm_category": "workload_type"}
    )

    print("Running carbon-aware scheduling...")
    results = carbon_aware_schedule(
        workload_df[["timestamp", "workload", "workload_type"]],
        carbon_df,
    )

    base = results["carbon_score_now"].sum()
    opt = results["carbon_score_scheduled"].sum()
    reduction = ((base - opt) / base * 100) if base else 0.0
    delayed = results[results["decision"] == "SHIFTED"]

    print("\n==========================================")
    print(" CARBON-AWARE SCHEDULER RESULTS")
    print("==========================================")
    print(f"Total jobs scheduled  : {len(results)}")
    print(f"Jobs shifted to green : {len(delayed)}")
    print(f"Average wait time     : {delayed['delay_minutes'].mean():.2f} mins" if not delayed.empty else "Average wait time     : 0 mins")
    print(f"Carbon reduction      : {reduction:.2f}%")
    print("==========================================")
