import pandas as pd
import os

RAW_DIR = "dataset/raw"
PROCESSED_DIR = "dataset/processed"
os.makedirs(PROCESSED_DIR, exist_ok=True)

# Corrected schema — third column is min_cpu, not workload_type
CPU_SCHEMA = ["timestamp", "vm_id", "cpu_min", "cpu_max", "cpu_avg"]

VMTABLE_SCHEMA = [
    "vm_id", "subscription_id", "deployment_id", "vm_created", "vm_deleted",
    "max_cpu", "avg_cpu", "p95_max_cpu", "vm_category", "vm_corecount", "vm_memory"
]

def load_cpu_readings():
    df1 = pd.read_csv(f"{RAW_DIR}/trace_data_vm_cpu_readings_vm_cpu_readings-file-1-of-125.csv", names=CPU_SCHEMA)
    df2 = pd.read_csv(f"{RAW_DIR}/trace_data_vm_cpu_readings_vm_cpu_readings-file-2-of-125.csv", names=CPU_SCHEMA)
    combined = pd.concat([df1, df2], ignore_index=True)
    return combined

def load_vmtable():
    vmtable = pd.read_csv(f"{RAW_DIR}/trace_data_vmtable_vmtable.csv", header=None, names=VMTABLE_SCHEMA)
    return vmtable[["vm_id", "vm_category", "vm_corecount", "vm_memory"]]

def main():
    readings = load_cpu_readings()
    vmtable = load_vmtable()

    print(f"Total readings: {len(readings)}")
    print(f"Timestamp range: {readings['timestamp'].min()} to {readings['timestamp'].max()}")

    # Merge to bring in vm_category (Delay-insensitive vs Interactive)
    merged = readings.merge(vmtable, on="vm_id", how="left")

    # Aggregate into one total-workload time series per timestamp
    workload_series = merged.groupby("timestamp").agg(
        total_cpu_avg=("cpu_avg", "sum"),
        mean_cpu_avg=("cpu_avg", "mean"),
        vm_count=("vm_id", "count")
    ).reset_index()

    # Also produce a breakdown by vm_category — useful for the scheduler
    category_series = merged.groupby(["timestamp", "vm_category"]).agg(
        cpu_avg=("cpu_avg", "sum")
    ).reset_index()

    workload_series = workload_series.sort_values("timestamp")

    workload_series.to_csv(f"{PROCESSED_DIR}/workload_timeseries.csv", index=False)
    category_series.to_csv(f"{PROCESSED_DIR}/workload_by_category.csv", index=False)

    print(f"Saved processed files to {PROCESSED_DIR}/")

if __name__ == "__main__":
    main()