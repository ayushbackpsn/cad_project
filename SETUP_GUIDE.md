# Setup Guide - AI-Based Predictive Auto-Scaling

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Java 11 or higher (for CloudSim Plus - optional, Python simulation works without it)
- Maven (for CloudSim Plus compilation - optional)

## Installation Steps

### Step 1: Install Python Dependencies

```bash
pip install -r requirements.txt
```

This will install:
- pandas, numpy (data processing)
- scikit-learn (machine learning)
- matplotlib, seaborn (visualization)
- flask, flask-cors (dashboard backend)

### Step 2: Prepare Dataset

1. Download the Bitbrains GWA-T-12 dataset from:
   https://www.upscale-project.eu/en/resources/datasets/bitbrains-fast-storage

2. Place the dataset file (e.g., `RND_5k.csv`) in:
   ```
   data/bitbrains/
   ```

3. The dataset should contain these columns:
   - Timestamp [ms]
   - CPU cores
   - CPU capacity provisioned [MHZ]
   - CPU usage [MHZ]
   - CPU usage [%]
   - Memory capacity provisioned [KB]
   - Memory usage [KB]
   - Disk read throughput [KB/s]
   - Disk write throughput [KB/s]
   - Network received throughput [KB/s]
   - Network transmitted throughput [KB/s]

### Step 3: Train the Model (Optional)

If you want to train the Random Forest model with your dataset:

```bash
cd ml
python train_model.py
```

This will:
- Load and preprocess the dataset
- Create time-series lag features
- Train the Random Forest model
- Save the model to `results/model.pkl`

**Note:** The dashboard can work without a trained model by using synthetic workload data for demonstration.

### Step 4: Run Unit Tests

Verify the scaling engine works correctly:

```bash
python tests/test_scaling_engine.py
```

All 18 tests should pass.

### Step 5: Launch the Dashboard

```bash
cd dashboard/backend
python app.py
```

The dashboard will be available at:
```
http://localhost:5000
```

## Using the Dashboard

### Running a Single Policy Simulation

1. Select a workload scenario:
   - Normal Workload
   - Increasing Workload
   - Sudden Spike
   - Decreasing Workload
   - Highly Variable

2. Select a scaling policy:
   - Predictive Scaling (recommended)
   - Reactive Scaling
   - Static Scaling

3. Configure parameters:
   - Initial VMs: Starting number of VMs
   - Minimum VMs: Lower limit for scaling
   - Maximum VMs: Upper limit for scaling
   - CPU Threshold: CPU utilization % for scaling decisions
   - Memory Threshold: Memory utilization % for scaling decisions
   - Cooldown: Seconds between scaling actions
   - Simulation Duration: Number of time steps
   - VM Hourly Cost: Simulated cost per VM per hour

4. Click "RUN SIMULATION"

5. View results:
   - KPI cards (Active VMs, Energy, Cost, SLA violations, etc.)
   - Charts (VM count over time, utilization, energy, cost)
   - Scaling events timeline

### Comparing All Policies

1. Configure parameters as above
2. Click "COMPARE ALL POLICIES"
3. View comparison table showing:
   - Total energy for each policy
   - Total cost for each policy
   - SLA violations for each policy
   - Average utilization for each policy
   - Scaling events for each policy

## Project Structure

```
cad/
├── data/
│   └── bitbrains/              # Dataset files
├── ml/                         # Machine learning components
│   ├── data_loader.py          # Load Bitbrains dataset
│   ├── preprocessing.py        # Clean and normalize data
│   ├── feature_engineering.py  # Create lag features
│   ├── train_model.py          # Train Random Forest
│   ├── predict.py              # Make predictions
│   └── evaluate.py             # Evaluate model (MAE, RMSE, R²)
├── autoscaling/                # Auto-scaling engine
│   ├── resource_estimator.py   # Calculate required capacity
│   ├── scaling_engine.py       # Decide scale up/down/no change
│   └── policies.py             # Static, Reactive, Predictive policies
├── cloudsim/                   # Cloud simulation
│   ├── pom.xml                 # Maven configuration
│   ├── simulation.py           # Python simulation wrapper
│   └── src/main/java/          # Java CloudSim Plus code
├── dashboard/                  # Web dashboard
│   ├── backend/
│   │   └── app.py             # Flask backend API
│   └── frontend/
│       └── index.html         # Dashboard UI
├── tests/
│   └── test_scaling_engine.py  # Unit tests
├── results/                    # Model and results storage
├── requirements.txt            # Python dependencies
├── README.md                   # Project overview
├── SETUP_GUIDE.md             # This file
└── VIVA_EXPLANATIONS.md       # Viva preparation
```

## Testing Individual Components

### Test Data Loader
```bash
python ml/data_loader.py
```

### Test Preprocessing
```bash
python ml/preprocessing.py
```

### Test Feature Engineering
```bash
python ml/feature_engineering.py
```

### Train Model
```bash
python ml/train_model.py
```

### Evaluate Model
```bash
python ml/evaluate.py
```

### Test Resource Estimator
```bash
python autoscaling/resource_estimator.py
```

### Test Scaling Engine
```bash
python autoscaling/scaling_engine.py
```

### Test Policies
```bash
python autoscaling/policies.py
```

### Test Cloud Simulation
```bash
python cloudsim/simulation.py
```

## Troubleshooting

### Dataset Not Found Error

**Error:** `FileNotFoundError: Dataset file not found`

**Solution:**
1. Ensure the Bitbrains dataset is in `data/bitbrains/`
2. Check the filename matches what's expected in `data_loader.py`
3. The dashboard will work with synthetic data even without the dataset

### Import Errors

**Error:** `ModuleNotFoundError: No module named 'xyz'`

**Solution:**
```bash
pip install -r requirements.txt
```

### Port Already in Use

**Error:** `Address already in use` when starting dashboard

**Solution:**
1. Change the port in `dashboard/backend/app.py`:
   ```python
   app.run(debug=True, host='0.0.0.0', port=5001)  # Use 5001 instead of 5000
   ```
2. Or stop the process using port 5000

### Java/Maven Issues (Optional)

If you want to use the actual CloudSim Plus Java simulation:

**Error:** `mvn: command not found`

**Solution:**
1. Install Maven from https://maven.apache.org/download.cgi
2. Add Maven to your system PATH
3. Alternatively, use the Python simulation (which works without Java)

## Performance Tips

- For faster simulations, reduce the "Simulation Duration" parameter
- For more accurate results, increase the duration
- The dashboard uses synthetic workload by default - for real results, train the model with the Bitbrains dataset

## Academic Use

This project is designed for academic purposes:

- All code is beginner-friendly and well-documented
- The scaling logic is explainable (not a black box)
- Unit tests demonstrate correctness
- VIVA_EXPLANATIONS.md provides detailed explanations for presentations
- The dashboard provides visual demonstrations

## Next Steps

After setup:

1. Explore the dataset using `ml/data_loader.py`
2. Train the model with your data using `ml/train_model.py`
3. Evaluate model performance using `ml/evaluate.py`
4. Test scaling policies using the dashboard
5. Compare policies to see which performs best for different scenarios
6. Prepare for viva using `VIVA_EXPLANATIONS.md`

## Support

For issues or questions:
1. Check the error messages in the terminal
2. Review the code comments in each module
3. Refer to VIVA_EXPLANATIONS.md for conceptual understanding
4. Check that all dependencies are installed correctly
