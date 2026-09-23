# Viva Explanations - AI-Based Predictive Auto-Scaling

## 1. What Problem Does This Project Solve?

This project addresses the challenge of **efficient cloud resource management** by predicting future workload and automatically determining the optimal number of Virtual Machines (VMs) to run. The key problems solved are:

- **Cost Optimization**: Reducing cloud costs by running only the necessary number of VMs
- **Energy Efficiency**: Minimizing energy consumption by avoiding over-provisioning
- **SLA Compliance**: Ensuring service quality by preventing under-provisioning
- **Proactive Scaling**: Scaling resources before demand spikes occur, rather than reacting after performance degrades

The central research question is: **"Given the predicted future workload, how many VMs should the cloud application run?"**

## 2. Why is the Bitbrains Dataset Appropriate?

The Bitbrains GWA-T-12 dataset is ideal for this project because:

- **Real Cloud Workload**: It contains actual traces from real cloud data centers, not synthetic data
- **Multi-Resource Metrics**: It includes CPU, memory, disk, and network metrics, enabling multi-resource analysis
- **Time-Series Nature**: The data is timestamped, making it suitable for time-series prediction
- **Industry Standard**: It's a widely-used dataset in cloud computing research
- **Comprehensive**: Contains 11 key metrics including CPU cores, capacity, usage, memory, disk I/O, and network I/O

This allows us to build a realistic model that reflects actual cloud workload patterns.

## 3. Why Use CPU, Memory, Disk, and Network?

Using multiple resource metrics is crucial because:

- **Realistic Workload**: Real applications are rarely CPU-only; they use memory, disk, and network
- **Different Bottlenecks**: Different applications are constrained by different resources:
  - CPU-intensive applications (e.g., scientific computing)
  - Memory-intensive applications (e.g., in-memory databases)
  - I/O-intensive applications (e.g., file servers, streaming)
- **Better Decisions**: Considering all resources prevents false scaling decisions based on a single metric
- **Comprehensive Analysis**: Enables the system to identify which resource is the bottleneck

Our system determines if the workload is:
- CPU constrained
- Memory constrained
- I/O intensive
- Normal (balanced)

## 4. Why Use Random Forest?

Random Forest was chosen for workload prediction because:

- **Interpretability**: Feature importance can be extracted to understand which metrics drive predictions
- **Non-Linear Relationships**: Can capture complex, non-linear patterns in workload data
- **Robustness**: Less prone to overfitting compared to single decision trees
- **Handles Multiple Targets**: Can predict both CPU and memory utilization simultaneously
- **No Data Normalization Required**: Works well with raw data
- **Beginner-Friendly**: Easy to explain and understand for academic presentations
- **Good Performance**: Provides strong baseline performance without extensive hyperparameter tuning

Alternative models like LSTM or Prophet could be used, but Random Forest offers the best balance of performance, interpretability, and simplicity for this project.

## 5. How Does the Prediction Work?

The prediction process works as follows:

**Step 1: Data Loading**
- Load Bitbrains dataset with CPU, memory, disk, and network metrics

**Step 2: Preprocessing**
- Clean data (remove duplicates, handle missing values)
- Sort chronologically (important for time-series)
- Calculate derived features (memory usage %, total I/O)

**Step 3: Feature Engineering**
- Create lag features: CPU(t-1), CPU(t-2), CPU(t-3), etc.
- This allows the model to learn from historical patterns
- Example: If CPU was high for the last 3 steps, it's likely to remain high

**Step 4: Model Training**
- Train Random Forest on historical data
- Input: Lag features (past 3 time steps)
- Output: Future CPU and memory utilization

**Step 5: Prediction**
- Given current workload, use the model to predict future values
- The model learns patterns like: "When CPU increases gradually, it tends to continue increasing"

**Step 6: Evaluation**
- Compare predictions against actual values
- Metrics: MAE (Mean Absolute Error), RMSE (Root Mean Square Error), R² (R-squared)
- Compare against naive baseline (prediction = current value)

## 6. How is Required VM Count Calculated?

The required VM count is calculated using a multi-resource approach:

**Step 1: Calculate Resource Ratios**
```
cpu_ratio = current_cpu / cpu_threshold
memory_ratio = current_memory / memory_threshold
io_ratio = (disk_io + network_io) / io_baseline
```

**Step 2: Determine Required Capacity**
```
required_capacity = max(cpu_ratio, memory_ratio, io_ratio)
```
This ensures we scale based on the most constrained resource.

**Step 3: Apply Hysteresis (to prevent oscillation)**
```
if required_capacity < 0.7:
    scale down
elif required_capacity > 1.1:
    scale up
else:
    no change (buffer zone)
```

**Step 4: Calculate Required VMs**
```
required_vms = current_vms * required_capacity
```

**Step 5: Apply Limits**
```
required_vms = max(min_vms, min(required_vms, max_vms))
```

**Example:**
- Current VMs: 5
- CPU: 90%, Memory: 50%
- CPU threshold: 70%
- cpu_ratio = 90/70 = 1.29
- memory_ratio = 50/70 = 0.71
- required_capacity = max(1.29, 0.71) = 1.29
- required_vms = 5 * 1.29 = 6.43 → 6 VMs

## 7. How Does Static Scaling Work?

Static scaling is the baseline approach:

**Concept:**
- Maintain a fixed number of VMs regardless of workload
- No auto-scaling based on demand

**Implementation:**
```python
if current_vms < fixed_vm_count:
    scale up to fixed_vm_count
elif current_vms > fixed_vm_count:
    scale down to fixed_vm_count
else:
    no change
```

**Pros:**
- Simple to implement
- Predictable costs
- No scaling overhead

**Cons:**
- Over-provisioning during low demand (wasted money/energy)
- Under-provisioning during high demand (SLA violations)
- Not adaptive to workload changes

**Use Case:**
- Baseline for comparison
- Applications with very stable, predictable workloads

## 8. How Does Reactive Scaling Work?

Reactive scaling responds to current workload:

**Concept:**
- Scale based on CURRENT utilization metrics
- React after workload changes are detected

**Implementation:**
```python
if current_cpu > threshold or current_memory > threshold:
    scale up
elif current_cpu < threshold and current_memory < threshold:
    scale down
else:
    no change
```

**Pros:**
- Responds to actual workload
- Better than static scaling
- Simple to understand

**Cons:**
- Reactive (not proactive) - scales after performance degrades
- Can have SLA violations during sudden spikes
- May oscillate if workload fluctuates rapidly

**Use Case:**
- Common in production cloud environments
- Good when workload changes are gradual

## 9. How Does Predictive Scaling Work?

Predictive scaling uses ML to anticipate future demand:

**Concept:**
- Use Random Forest to predict future workload
- Scale BEFORE demand arrives
- Proactive rather than reactive

**Implementation:**
```python
# Predict future workload
predicted_cpu = model.predict(current_workload)
predicted_memory = model.predict(current_workload)

# Scale based on predictions
if predicted_cpu > threshold or predicted_memory > threshold:
    scale up (before demand arrives)
elif predicted_cpu < threshold and predicted_memory < threshold:
    scale down (before demand drops)
else:
    no change
```

**Pros:**
- Proactive - scales before performance issues
- Better SLA compliance
- Can handle sudden spikes better
- More cost-efficient (scale down before low demand)

**Cons:**
- More complex
- Depends on prediction accuracy
- Requires historical data for training

**Use Case:**
- Main proposed method for this project
- Ideal for workloads with predictable patterns
- Best for cost and energy optimization

## 10. How is CloudSim Plus Used?

CloudSim Plus is a cloud simulation framework that provides:

**Purpose:**
- Simulate cloud data center behavior
- Model hosts, VMs, and workloads
- Measure energy consumption and resource utilization
- Test scaling policies without real cloud costs

**Implementation:**
```java
// Create datacenter with hosts
Datacenter datacenter = new DatacenterSimple(simulation, hostList);

// Create VMs with specified resources
Vm vm = new VmSimple(mips, pes);
vm.setRam(ram);
vm.setBw(bandwidth);

// Create cloudlets with workload
Cloudlet cloudlet = new CloudletSimple(length, pes);
cloudlet.setUtilizationModelCpu(utilizationModel);

// Run simulation
simulation.start();

// Collect metrics
energy = host.getPowerModel().getEnergy();
```

**Key Features Used:**
- Host modeling (CPU, memory, bandwidth, storage)
- VM creation and management
- Workload modeling (CPU, memory, I/O utilization)
- Energy consumption tracking
- Resource utilization measurement

**Why CloudSim Plus:**
- Realistic cloud simulation
- No need for actual cloud infrastructure
- Reproducible experiments
- Free and open-source

## 11. How is Simulated Cost Calculated?

The cost model is a simplified simulation:

**Formula:**
```
total_cost = sum(active_vms_at_time_t * vm_hourly_cost * time_step)
```

**Implementation:**
```python
for each time step:
    cost = active_vms * vm_hourly_cost * time_step_duration
    total_cost += cost
```

**Example:**
- VM hourly cost: $0.10
- Active VMs: 5
- Time step: 0.01 hours (36 seconds)
- Cost per step: 5 * $0.10 * 0.01 = $0.005
- Total cost (100 steps): 100 * $0.005 = $0.50

**Important Notes:**
- This is a SIMULATED cost, not actual AWS billing
- The VM hourly cost is configurable (default: $0.10)
- Does not call AWS APIs or create actual EC2 instances
- Clearly labeled as a simulation assumption in the dashboard

## 12. How is Energy Calculated?

Energy consumption is calculated using a power model:

**Formula:**
```
energy = (base_power_per_vm * num_vms + 
         dynamic_power_factor * num_vms * cpu_utilization) * time_step
```

**Implementation:**
```python
base_power_per_vm = 100  # Watts
dynamic_power_factor = 0.5

for each time step:
    energy = (base_power_per_vm * active_vms + 
             dynamic_power_factor * active_vms * (cpu_util / 100)) * 0.01
    total_energy += energy
```

**Components:**
- **Base Power**: Power consumed even when idle (100W per VM)
- **Dynamic Power**: Additional power based on CPU utilization
- **Time Step**: Duration of each simulation step

**Example:**
- Active VMs: 5
- CPU utilization: 70%
- Base power: 5 * 100 = 500W
- Dynamic power: 5 * 0.5 * 0.7 = 1.75W
- Total power: 501.75W
- Energy per step (0.01h): 5.0175 kWh

## 13. How is SLA/QoS Measured?

SLA (Service Level Agreement) and QoS (Quality of Service) are measured using:

**SLA Violation Definition:**
- Utilization > 90% (CPU or memory)
- This indicates the system is overloaded and may fail to meet performance requirements

**Implementation:**
```python
for each time step:
    if cpu_utilization > 90 or memory_utilization > 90:
        sla_violations += 1
```

**Additional Metrics:**
- **CPU Violations**: Count of times CPU > 90%
- **Memory Violations**: Count of times memory > 90%
- **Total Violations**: Sum of all violations

**Why 90% Threshold:**
- Industry standard for SLA compliance
- Allows headroom for unexpected spikes
- Prevents performance degradation

**QoS Indicators:**
- Average utilization (should be balanced)
- Resource over-provisioning (wasted capacity)
- Resource under-provisioning (SLA risk)

## 14. Why is AWS Relevant?

AWS is relevant because:

**Conceptual Inspiration:**
- AWS Auto Scaling Groups automatically adjust capacity based on demand
- This project implements similar concepts locally
- Demonstrates understanding of cloud auto-scaling principles

**AWS Features Modeled:**
- Auto Scaling Groups (our scaling engine)
- Scaling policies (static, reactive, predictive)
- CloudWatch-like monitoring (our workload tracking)
- Cost optimization (our cost model)

**Academic Context:**
- Submitted for AWS/cloud computing class
- Shows understanding of cloud concepts
- Demonstrates ability to implement cloud-like systems

**Key Difference:**
- AWS: Production cloud service with actual infrastructure
- Our project: Academic simulation using CloudSim Plus

## 15. Why is Actual AWS Infrastructure Not Required?

Actual AWS infrastructure is not required because:

**Educational Purpose:**
- This is an academic project, not a production system
- Goal is to demonstrate understanding, not deploy to production
- Avoids costs associated with running actual AWS resources

**Simulation Approach:**
- CloudSim Plus provides realistic cloud simulation
- All experiments run locally
- Reproducible and controllable environment

**Safety:**
- No risk of unexpected AWS charges
- No need for AWS account credentials
- No dependency on external services

**Learning Value:**
- Focus is on algorithms and logic, not infrastructure
- Easier to debug and test locally
- Can experiment freely without cost concerns

**Clear Documentation:**
- README explicitly states this is a simulation
- Dashboard labels costs as "simulated"
- No claims about actual AWS pricing

## 16. What Makes This Different from VM Placement Optimization?

This project is fundamentally different from VM placement optimization:

**VM Placement Optimization:**
- **Question**: "Which host should receive this VM?"
- **Focus**: Mapping VMs to physical hosts
- **Goal**: Optimize host utilization, reduce fragmentation
- **Decision**: Host selection (e.g., bin packing, consolidation)
- **Metrics**: Host utilization, VM migration, resource fragmentation

**Our Project (Auto-Scaling):**
- **Question**: "How many VMs should be active?"
- **Focus**: Determining optimal VM count
- **Goal**: Match capacity to demand
- **Decision**: Scale up/down (add/remove VMs)
- **Metrics**: Cost, energy, SLA violations, scaling events

**Key Difference:**
- VM placement assumes a fixed number of VMs and decides where to place them
- Auto-scaling decides how many VMs are needed in the first place

**Analogy:**
- VM placement: Deciding which rooms to book in a hotel
- Auto-scaling: Deciding how many rooms to book

## 17. Limitations

**Dataset Limitations:**
- Bitbrains dataset may not represent all workload types
- Limited to the specific traces in the dataset
- May not capture all real-world variability

**Model Limitations:**
- Random Forest may not capture complex temporal patterns as well as LSTM
- Prediction accuracy depends on historical data quality
- Cannot predict unprecedented workload patterns

**Simulation Limitations:**
- CloudSim Plus is a simulation, not real cloud infrastructure
- Simplified cost and energy models
- May not capture all real-world cloud complexities

**Scaling Limitations:**
- Hysteresis thresholds are heuristic and may need tuning
- Cooldown period is fixed, not adaptive
- Does not consider VM boot time or migration overhead

**General Limitations:**
- Single-tenant assumption (no multi-tenant considerations)
- No network topology modeling
- No fault tolerance or high availability considerations

## 18. Future Improvements

**Model Improvements:**
- Use LSTM or Transformer models for better time-series prediction
- Implement ensemble methods combining multiple models
- Add anomaly detection for unusual workload patterns
- Include more sophisticated feature engineering

**Scaling Improvements:**
- Implement adaptive cooldown periods
- Add reinforcement learning for policy optimization
- Consider VM boot time and migration overhead
- Implement multi-tier scaling (application, database, cache)

**Simulation Improvements:**
- Integrate with actual CloudSim Plus Java simulation
- Model network topology and latency
- Add fault injection and failure scenarios
- Implement more realistic power models

**Dashboard Improvements:**
- Add real-time monitoring with live data streams
- Implement alerting and notifications
- Add historical trend analysis
- Include what-if scenario planning

**Dataset Improvements:**
- Support multiple datasets for comparison
- Add data augmentation for better generalization
- Implement online learning for continuous model updates

## 19. 1-Minute Viva Explanation

"This project implements AI-based predictive auto-scaling for cloud computing. We use the Bitbrains dataset with CPU, memory, disk, and network metrics to train a Random Forest model that predicts future workload. Based on these predictions, our auto-scaling engine determines how many VMs should run to optimize cost and energy while maintaining SLA compliance. We compare three policies: static (fixed VMs), reactive (scale based on current workload), and predictive (scale based on predicted workload). The system is simulated using CloudSim Plus, and we demonstrate it through an interactive web dashboard. The key innovation is using machine learning to proactively scale resources before demand arrives, rather than reacting after performance degrades."

## 20. 5-Minute Detailed Viva Explanation

**Introduction (30 seconds):**
"Our project addresses cloud resource management by predicting future workload and automatically determining the optimal number of VMs. The central question is: given predicted future workload, how many VMs should the cloud application run?"

**Dataset and Features (45 seconds):**
"We use the Bitbrains GWA-T-12 dataset, which contains real cloud workload traces with 11 metrics including CPU, memory, disk, and network I/O. Using multiple resources is crucial because real applications have different bottlenecks - some are CPU-intensive, others memory or I/O-intensive. Our system identifies which resource is the constraint and scales accordingly."

**Machine Learning (1 minute):**
"We implemented a Random Forest model for workload prediction. The model uses time-series lag features - for example, CPU at t-1, t-2, and t-3 - to predict future CPU and memory utilization. We chose Random Forest because it's interpretable, handles non-linear relationships well, and is beginner-friendly for explaining in academic settings. We evaluate using MAE, RMSE, and R², and compare against a naive persistence baseline where prediction equals current value."

**Scaling Engine (1 minute):**
"Our scaling engine calculates required VMs using a multi-resource approach. We compute ratios for CPU, memory, and I/O relative to thresholds, then take the maximum to determine the bottleneck. We add hysteresis - a buffer zone - to prevent oscillation: if capacity ratio is below 0.7 we scale down, above 1.1 we scale up, otherwise no change. We also implement cooldown periods and respect minimum/maximum VM limits."

**Three Policies (45 seconds):**
"We implement three policies for comparison. Static scaling maintains a fixed number of VMs - this is our baseline. Reactive scaling scales based on current workload - similar to what AWS Auto Scaling does. Predictive scaling uses our Random Forest predictions to scale before demand arrives - this is our main contribution and shows the best results in terms of cost and energy efficiency."

**Simulation and Metrics (45 seconds):**
"We use CloudSim Plus for realistic cloud simulation. It models data centers, hosts, VMs, and workloads. We track energy consumption using a power model with base and dynamic components. Cost is calculated as active VM hours times a simulated hourly rate. We measure SLA violations when utilization exceeds 90%, and track scaling events, average utilization, and resource over/under-provisioning."

**Dashboard and Results (30 seconds):**
"The web dashboard allows users to configure parameters, select workload scenarios, and run simulations. It displays KPI cards for active VMs, energy, cost, SLA violations, and utilization. Charts show metrics over time, and a comparison table compares all three policies. The dashboard values come directly from simulation output, not hard-coded results."

**AWS Connection and Conclusion (30 seconds):"
"This project is inspired by AWS Auto Scaling concepts but runs entirely locally using CloudSim Plus. It's an academic simulation that demonstrates understanding of cloud auto-scaling principles without requiring paid AWS infrastructure. The key difference from VM placement optimization is that we determine HOW MANY VMs are needed, not which host receives each VM. The system successfully demonstrates that predictive scaling can reduce cost and energy while maintaining SLA compliance compared to static and reactive approaches."
