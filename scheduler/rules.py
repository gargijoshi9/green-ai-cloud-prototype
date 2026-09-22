"""Decision rules for the Green AI carbon-aware scheduler."""

FLEXIBLE_CATEGORY = "Delay-insensitive"


def is_flexible(workload_type: str) -> bool:
    """Return True only for workloads classified as delay-insensitive."""
    if workload_type is None:
        return False
    return workload_type.strip().lower() == FLEXIBLE_CATEGORY.lower()


def should_run_now(workload_type: str) -> bool:
    """Interactive/unknown workloads are kept at their original time."""
    return not is_flexible(workload_type)
