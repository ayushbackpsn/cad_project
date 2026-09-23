# AI-Based Predictive Auto-Scaling for Cost and Energy-Efficient Cloud Computing

## Overview

This project implements a predictive auto-scaling system for cloud computing that uses machine learning to predict future workload and determine the optimal number of VMs to run. The system is inspired by AWS Auto Scaling concepts but runs entirely locally using CloudSim Plus for simulation.

**Key Research Question:** "Given the predicted future workload, how many VMs should the cloud application run?"

## Research Gaps Addressed

This project addresses three key research gaps in predictive auto-scaling:

### GAP 1: Multi-Resource Predictive Scaling
- **Problem:** Traditional auto-scaling often relies on CPU alone
- **Solution:** Uses CPU, memory, disk, and network metrics for comprehensive workload prediction
- **Implementation:** Random Forest model with time-series lag features for all resource types
- **Key Features:** Multi-resource constraint detection (CPU-constrained, memory-constrained, I/O-intensive, normal)

### GAP 2: Joint Energy + Cost + SLA/QoS + Scaling Overhead Evaluation
- **Problem:** Evaluating auto-scaling based only on prediction accuracy is insufficient
- **Solution:** Comprehensive multi-objective evaluation including:
  - Energy consumption (kWh) using power models
  - Simulated infrastructure cost (configurable VM-hour pricing)
  - SLA/QoS violations (utilization > 90% threshold)
  - Scaling overhead (scale-up/down events, oscillations, churn)
  - Over-provisioning and under-provisioning rates
- **Implementation:** MetricsCalculator class for comprehensive evaluation

### GAP 3: Scaling Stability / Prediction Uncertainty
- **Problem:** Prediction fluctuations can cause unstable scaling (5→6→5→6→5 oscillation)
- **Solution:** Multiple stability mechanisms:
  - Cooldown period (configurable time between scaling actions)
  - Hysteresis/threshold margin (buffer zone: 0.7-1.1 to prevent oscillation)
  - Minimum and maximum VM limits
  - Prediction error tracking
  - Scaling churn measurement
- **Implementation:** ScalingStabilityController with hysteresis, cooldown, and churn tracking

## Architecture

```
Bitbrains Dataset (CPU + Memory + Disk + Network)
       ↓
Data Preprocessing (chronological, no shuffling)
       ↓
Multi-Resource Feature Engineering (lag features)
       ↓
Random Forest Prediction (CPU + Memory targets)
       ↓
Predicted CPU + Predicted Memory
       ↓
Scaling Decision Engine (with hysteresis + cooldown)
       ↓
Required VM Count (multi-resource constraint analysis)
       ↓
CloudSim Plus Simulation
       ↓
Energy + Cost + SLA/QoS + Utilization + Overhead
       ↓
Comparative Evaluation (Static vs Reactive vs Predictive)
       ↓
Dashboard
```

## Project Structure

```
project-root/
├── data/
│   └── bitbrains/          # Bitbrains GWA-T-12 dataset
├── ml/                     # Machine learning components
│   ├── data_loader.py
│   ├── preprocessing.py
│   ├── feature_engineering.py
│   ├── train_model.py
│   ├── predict.py
│   └── evaluate.py
├── autoscaling/            # Auto-scaling engine
│   ├── resource_estimator.py   # Multi-resource constraint detection
│   ├── scaling_engine.py       # Scaling decisions with stability
│   ├── scaling_stability.py    # Stability controller (NEW)
│   ├── metrics_calculator.py    # Comprehensive metrics (NEW)
│   └── policies.py             # Three scaling policies
├── cloudsim/               # CloudSim Plus simulation
│   ├── simulation.py       # Python wrapper with metrics
│   └── src/main/java/      # Java CloudSim Plus code
├── dashboard/              # Web dashboard
│   ├── backend/
│   │   └── app.py         # Flask API with enhanced metrics
│   └── frontend/
│       └── index.html     # Updated UI with new KPIs
├── results/                # Experiment results (CSV files)
├── tests/                  # Unit tests
│   ├── test_scaling_engine.py
│   └── test_metrics_calculator.py (NEW)
├── run_experiments.py      # Experimental runner (NEW)
├── requirements.txt
└── README.md
```

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Step 1: Dataset Preparation
Place the Bitbrains GWA-T-12 dataset in `data/bitbrains/`

### Step 2: Train Model (Optional)
```bash
python ml/train_model.py
```

### Step 3: Run Experiments
```bash
python run_experiments.py
```
This generates CSV files in `results/` with comparison metrics.

### Step 4: Launch Dashboard
```bash
python dashboard/backend/app.py
```
Then open http://localhost:5000

### Step 5: Run Tests
```bash
python tests/test_scaling_engine.py
python tests/test_metrics_calculator.py
```

## Features

### Multi-Resource Workload Monitoring
- CPU utilization (%)
- Memory utilization (%)
- Disk I/O (read/write throughput in KB/s)
- Network I/O (received/transmitted in KB/s)

### Machine Learning
- Random Forest with time-series lag features
- Chronological train/test split (no shuffling)
- Evaluation metrics: MAE, RMSE, R²
- Naive persistence baseline for comparison
- Feature importance reporting

### Auto-Scaling Policies
1. **Static Scaling** - Fixed number of VMs
2. **Reactive Scaling** - Scale based on current workload
3. **Predictive Scaling** - Scale based on predicted future workload (with stability mechanisms)

### Scaling Stability Mechanisms
- **Cooldown**: Configurable time between scaling actions
- **Hysteresis**: Buffer zone (0.7-1.1) to prevent oscillation
- **Min/Max Limits**: Enforce VM count boundaries
- **Churn Tracking**: Measure scaling oscillations

### Comprehensive Metrics
- **Energy**: kWh consumption with power model
- **Cost**: Simulated VM-hour cost (configurable)
- **SLA**: Violations when utilization > 90%
- **Scaling Overhead**: Scale-up/down events, oscillations, churn
- **Provisioning**: Over-provisioning and under-provisioning rates

### Cloud Simulation
- CloudSim Plus for realistic cloud simulation
- Energy consumption measurement
- SLA violation tracking
- Resource utilization monitoring
- Scaling event recording

### Dashboard
- Interactive web interface
- Configurable parameters
- Real-time simulation results
- Enhanced KPI cards (12 metrics including churn, oscillations, provisioning)
- Policy comparison table (14 metrics per policy)
- Charts for VM count, utilization, energy, cost, scaling events

## Experimental Scenarios

1. Normal workload
2. Increasing workload
3. Sudden workload spike
4. Decreasing workload
5. Highly variable workload

## Metrics Tracked

For each policy and scenario:
- Total energy consumption (kWh)
- Simulated cost ($)
- SLA violations (count and rate)
- Average CPU utilization (%)
- Average memory utilization (%)
- Average/Max/Min active VMs
- Scale-up events
- Scale-down events
- Total scaling events
- Scaling oscillations
- Scaling churn
- Over-provisioning rate
- Under-provisioning rate

## AWS Connection

This project is inspired by AWS Auto Scaling but does not require AWS infrastructure:

- **AWS Concept:** Auto Scaling Groups automatically adjust capacity based on demand
- **Our Implementation:** Local predictive auto-scaling simulation using ML predictions
- **Simulation Platform:** CloudSim Plus for realistic cloud environment simulation
- **Machine Learning:** Random Forest for workload prediction
- **Dataset:** Bitbrains GWA-T-12 real cloud workload traces

**Important:** This is an academic simulation and does not use paid AWS services or create actual EC2 instances.

## Difference from VM Placement Optimization

This project focuses on **"HOW MANY VMs should be active?"**
NOT **"WHICH HOST should receive the VM?"**

- VM placement optimization: Mapping VMs to physical hosts
- Auto-scaling: Determining optimal VM count based on demand

## Key Contributions

1. **Integration**: Multi-resource workload prediction + predictive VM scaling + CloudSim simulation
2. **Stability**: Hysteresis, cooldown, and churn mechanisms to prevent oscillation
3. **Evaluation**: Joint energy, cost, SLA, and scaling overhead assessment
4. **Reproducibility**: Complete experimental framework with CSV results and dashboard

## License

This project is for academic purposes.
