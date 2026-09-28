# Green AI for Sustainable Cloud Computing

## Team

| Name                        | Role        |
| --------------------------- | ----------- |
| **Gargi Joshi**             | Team Leader |
| **Ayman Nisar Kazi**        | Team Member |
| **Hemanshu Vikas Ganekar**  | Team Member |
| **Rajvardhani Amol Pawar**  | Team Member |
| **Anmay Vinod Chavan**      | Team Member |
| **Kamble Pranjali Kalidas** | Team Member |

---

## How to Start the Application

### 1. Clone the Repository

```powershell
git clone <repository-url>
cd <project-folder>
```

### 2. Set Up the Dataset

Download the Green AI workload dataset:

[Green AI Dataset ZIP](https://drive.google.com/file/d/1ekXGp0rh72kzT95Vs6NqHTP1eoi99nB4/view?usp=sharing)

Extract the downloaded ZIP and place the extracted files inside:

```text
dataset/raw/
```

The project should have a structure similar to:

```text
Green-AI/
├── dataset/
│   └── raw/
│       ├── dataset files...
│
├── prediction/
├── scheduler/
├── inference/
├── dashboard/
├── requirements.txt
└── README.md
```

> **Note:** `dataset/raw/` is excluded from Git because the dataset contains large files.

### 3. Create a Python Virtual Environment

From the project root:

```powershell
python -m venv .venv
```

Activate it on Windows:

```powershell
.venv\Scripts\activate
```

If PowerShell blocks script execution, run:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Then activate the environment again:

```powershell
.venv\Scripts\activate
```

### 4. Install Dependencies

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 5. Run the Dashboard

Start the Flask backend from the project root:

```powershell
python dashboard/app.py
```

You should see Flask start on port `5000`.

Open your browser and visit:

```text
http://localhost:5000
```

### 6. Available API Endpoints

The Flask backend provides the following endpoints:

| Endpoint                      | Purpose                                          |
| ----------------------------- | ------------------------------------------------ |
| `/api/health`                 | Checks whether the backend is running            |
| `/api/dashboard`              | Returns dashboard data and overall results       |
| `/api/inference-metrics`      | Returns FP32 vs INT8 inference benchmark results |
| `/api/sustainability-metrics` | Returns energy and carbon-reduction metrics      |

For example:

```text
http://localhost:5000/api/health
```



### 7. Application Workflow

Once the application is running, the pipeline works as follows:

```text
Cloud Workload Dataset
        ↓
Data Preprocessing
        ↓
Workload Prediction
        ↓
Carbon-Aware Scheduler
        ↓
Baseline vs Green AI Simulation
        ↓
Efficient Inference Benchmark
        ↓
Flask API
        ↓
Dashboard
        ↓
Energy & Carbon Metrics
```

The dashboard compares:

* **Baseline:** Immediate execution + FP32 inference + no carbon awareness
* **Green AI Pipeline:** Workload prediction + carbon-aware scheduling + INT8 inference

### 8. First Run

The first dashboard request may take a few seconds because the application performs the required model processing and inference benchmarking.

Results are cached for the running Flask process, so subsequent dashboard requests should be faster.

### 9. Verify the Application

After starting the server, first check:

```text
http://localhost:5000/api/health
```

If the backend is working, then open:

```text
http://localhost:5000
```

The dashboard should display the workload analysis, scheduling results, inference benchmarks, and sustainability metrics.

---

## Expected Outcome

The completed prototype runs simulated workloads in two scenarios:

1. **Baseline execution**
2. **Green AI optimized execution**

It then compares the two scenarios to quantify:

* ⚡ Energy consumption
* 🌱 Carbon emissions
* 📊 Workload shifted to lower-carbon periods
* 🤖 FP32 vs INT8 inference performance
* 📉 Overall percentage reduction in energy and carbon emissions

## System Architecture

```mermaid
flowchart TD
    %% Styling definitions
    classDef data fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px,color:#1b5e20,rx:8,ry:8
    classDef model fill:#e1f5fe,stroke:#0288d1,stroke-width:2px,color:#01579b,rx:8,ry:8
    classDef engine fill:#ede7f6,stroke:#5e35b1,stroke-width:2px,color:#311b92,rx:8,ry:8
    classDef backend fill:#fff3e0,stroke:#ef6c00,stroke-width:2px,color:#e65100,rx:8,ry:8
    classDef dashboard fill:#fce4ec,stroke:#c2185b,stroke-width:2px,color:#880e4f,rx:8,ry:8
    classDef metrics fill:#f1f8e9,stroke:#689f38,stroke-width:2px,color:#33691e,rx:15,ry:15

    %% Modules
    subgraph S1 ["📡 1. Data Ingestion"]
        direction LR
        D1[("📊 Telemetry Dataset<br/><small>CPU, Memory, Task Traces</small>")]:::data
        D2[("🌱 Carbon Grid API<br/><small>Solar/Wind Intensity Curves</small>")]:::data
    end

    subgraph S2 ["🧠 2. Prediction Module"]
        P1{"📈 Differenced Ridge Forecaster<br/><small>Predicts short-term cluster load</small>"}:::model
    end

    subgraph S3 ["⚙️ 3. Optimization Engine"]
        direction TB
        C1["🌿 Carbon-Aware Scheduler<br/><small>Greedy CO₂ minimization</small>"]:::engine
        I1["🤖 Efficient AI Inference<br/><small>5-Layer MLP (INT8 Quantized)</small>"]:::engine
    end

    subgraph S4 ["🌐 4. Web Application"]
        direction TB
        B1("🚀 Flask API Backend<br/><small>Cached Pipeline Execution</small>"):::backend
        DB["🖥️ Chart.js Dashboard<br/><small>Live Comparative Visualization</small>"]:::dashboard
    end

    subgraph S5 ["🏆 5. Tangible Outcomes"]
        direction LR
        O1(("⚡ Energy Reduced")):::metrics
        O2(("📉 Carbon Avoided")):::metrics
        O3(("🚀 Faster Inference")):::metrics
    end

    %% Data flow
    D1 ==>|"Time-Series Load"| P1
    D2 ==>|"CO₂ Signals"| C1
    
    P1 ==>|"Predicted Demand"| C1
    
    C1 ==>|"Scheduled Workloads"| B1
    I1 ==>|"Benchmark Stats"| B1
    
    B1 ==>|"JSON Analytics"| DB
    DB ===> O1 & O2 & O3
```

The goal is to demonstrate how **AI-based workload prediction, carbon-aware scheduling, and efficient model inference can work together as a unified sustainable cloud-computing pipeline.**
