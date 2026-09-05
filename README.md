# Green AI for Sustainable Cloud Computing

## The Problem

Cloud data centers run computing jobs the moment they're submitted, regardless of how the electricity powering them is generated at that moment. Whether the grid is running on solar and wind or on coal and gas, jobs execute immediately. This means a huge amount of avoidable carbon emissions comes not from *how much* computing we do, but from *when* and *how* we do it.

Data centers are one of the fastest-growing sources of global electricity demand, and most of that demand is not scheduled with any awareness of the environmental cost behind it.

## The Solution

This project builds a working prototype of a **smarter cloud system** — one that reduces energy consumption and carbon footprint using AI, without requiring new hardware or slowing down critical work.

It does this through three combined techniques:

### 1. Workload Prediction
Before jobs even run, the system forecasts near-future computing demand using historical workload patterns. Knowing what's coming next is the foundation for making any scheduling decision — you can't optimize timing if you don't know what needs to run.

### 2. Carbon-Aware Scheduling
Once the system knows what's coming, it checks how carbon-intensive the electricity grid is at that moment. Jobs that aren't time-critical are delayed and shifted to run during cleaner, lower-carbon windows instead of running immediately regardless of grid conditions. This is the same core idea used in Google's production carbon-intelligent computing system, adapted here at prototype scale.

### 3. Energy-Efficient Inference
Separately, the AI models used for prediction and processing are optimized (via techniques like quantization) to consume less energy per computation, without meaningfully sacrificing accuracy — making the AI itself "lighter" to run.

### Putting It Together

The prototype runs a full pipeline:

```
Historical Data → Workload Prediction → Carbon-Aware Scheduling Decision → Efficient Model Execution → Results Dashboard
```

The final output is a side-by-side comparison: a **baseline system** (jobs run immediately, no optimization) versus **this system** (predicts, schedules around carbon intensity, and runs efficient models) — showing measurable reductions in total energy consumed and estimated carbon emitted for the same amount of computing work.

## What's Novel Here vs. What's Existing Research

This project does not invent new algorithms. It builds on well-established techniques:

- ML-based workload forecasting — established research area
- Carbon-aware job scheduling — used in real production systems (e.g. Google)
- Model quantization for energy efficiency — standard ML efficiency technique

**The contribution of this project** is combining all three into one integrated, working pipeline and measuring their *combined* effect — most existing research studies these techniques in isolation. This prototype demonstrates and quantifies what happens when they're used together.

## Project Structure

```
/data          → Datasets used for workload simulation
/prediction    → Workload forecasting module
/scheduler     → Carbon-aware scheduling logic
/inference     → Energy-efficient model execution module
/dashboard     → Visualization of results and comparisons
/paper         → Research paper drafts and references
/notes         → Meeting logs and research notes
```

## Datasets & Tools

- **Workload data:** Public cloud workload traces (e.g. Google Cluster Trace / Azure Public Dataset)
- **Carbon intensity data:** Real or simulated grid carbon-intensity signal (e.g. WattTime, Electricity Maps)

## Expected Outcome

A working demo that runs the same simulated workload twice — once without optimization, once with this system's pipeline — and visibly shows a reduction in total energy used and carbon emitted, backed by a research paper explaining the approach, related work, methodology, and results in detail.
