package com.autoscaling;

import org.cloudsimplus.brokers.DatacenterBroker;
import org.cloudsimplus.brokers.DatacenterBrokerSimple;
import org.cloudsimplus.cloudlets.Cloudlet;
import org.cloudsimplus.cloudlets.CloudletSimple;
import org.cloudsimplus.core.CloudSimPlus;
import org.cloudsimplus.datacenters.Datacenter;
import org.cloudsimplus.datacenters.DatacenterSimple;
import org.cloudsimplus.hosts.Host;
import org.cloudsimplus.hosts.HostSimple;
import org.cloudsimplus.resources.Pe;
import org.cloudsimplus.resources.PeSimple;
import org.cloudsimplus.utilizationmodels.UtilizationModel;
import org.cloudsimplus.utilizationmodels.UtilizationModelDynamic;
import org.cloudsimplus.utilizationmodels.UtilizationModelFull;
import org.cloudsimplus.vms.Vm;
import org.cloudsimplus.vms.VmSimple;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * CloudSim Plus Simulation Runner
 * Simulates cloud environment with auto-scaling
 */
public class SimulationRunner {
    
    private CloudSimPlus simulation;
    private Datacenter datacenter;
    private DatacenterBroker broker;
    private List<Vm> vmList;
    private List<Cloudlet> cloudletList;
    private Map<Integer, Double> energyConsumptionOverTime;
    private Map<Integer, Integer> activeVmsOverTime;
    
    // Simulation parameters
   private int numHosts;
    private int hostPes;
    private long hostMips;
    private long hostRam;
    private long hostBw;
    private long hostStorage;
    
    public SimulationRunner() {
        this.vmList = new ArrayList<>();
        this.cloudletList = new ArrayList<>();
        this.energyConsumptionOverTime = new HashMap<>();
        this.activeVmsOverTime = new HashMap<>();
        
        // Default parameters
        this.numHosts = 10;
        this.hostPes = 4;
        this.hostMips = 1000;
        this.hostRam = 16384; // 16 GB in MB
        this.hostBw = 100000; // 100 GB in MB
        this.hostStorage = 1000000; // 1 TB in MB
    }
    
    /**
     * Initialize the simulation
     */
    public void initialize() {
        simulation = new CloudSimPlus();
        datacenter = createDatacenter();
        broker = new DatacenterBrokerSimple(simulation);
    }
    
    /**
     * Create a datacenter with hosts
     */
    private Datacenter createDatacenter() {
        List<Host> hostList = new ArrayList<>();
        
        for (int i = 0; i < numHosts; i++) {
            List<Pe> peList = new ArrayList<>();
            for (int j = 0; j < hostPes; j++) {
                peList.add(new PeSimple(hostMips));
            }
            
            Host host = new HostSimple(hostRam, hostBw, hostStorage, peList);
            host.setVmScheduler(new org.cloudsimplus.schedulers.VmSchedulerTimeShared());
            hostList.add(host);
        }
        
        return new DatacenterSimple(simulation, hostList);
    }
    
    /**
     * Create VMs with specified workload
     */
    public void createVMs(int numVms, double cpuUtilization, double memoryUtilization) {
        vmList.clear();
        
        long vmMips = hostMips;
        int vmPes = 1;
        long vmRam = (long) (hostRam / 4); // 4 GB
        long vmBw = (long) (hostBw / 10);
        long vmStorage = (long) (hostStorage / 100);
        
        for (int i = 0; i < numVms; i++) {
            Vm vm = new VmSimple(vmMips, vmPes);
            vm.setRam(vmRam);
            vm.setBw(vmBw);
            vm.setSize(vmStorage);
            vmList.add(vm);
        }
        
        broker.submitVmList(vmList);
    }
    
    /**
     * Create cloudlets with workload
     */
    public void createCloudlets(int numCloudlets, double cpuUtilization, double memoryUtilization) {
        cloudletList.clear();
        
        long cloudletLength = 10000;
        int cloudletPes = 1;
        
        for (int i = 0; i < numCloudlets; i++) {
            UtilizationModel utilizationModel = new UtilizationModelDynamic(cpuUtilization);
            Cloudlet cloudlet = new CloudletSimple(cloudletLength, cloudletPes);
            cloudlet.setUtilizationModelCpu(utilizationModel);
            cloudlet.setUtilizationModelRam(new UtilizationModelDynamic(memoryUtilization));
            cloudlet.setUtilizationModelBw(new UtilizationModelFull());
            cloudletList.add(cloudlet);
        }
        
        broker.submitCloudletList(cloudletList);
    }
    
    /**
     * Run the simulation
     */
    public void runSimulation() {
        simulation.start();
        
        // Collect metrics
        collectMetrics();
    }
    
    /**
     * Collect simulation metrics
     */
    private void collectMetrics() {
        double totalEnergy = 0;
        
        for (Host host : datacenter.getHostList()) {
            totalEnergy += host.getPowerModel().getEnergy();
        }
        
        energyConsumptionOverTime.put(0, totalEnergy);
        activeVmsOverTime.put(0, vmList.size());
    }
    
    /**
     * Get simulation results
     */
    public Map<String, Object> getResults() {
        Map<String, Object> results = new HashMap<>();
        
        results.put("total_energy", energyConsumptionOverTime.values().stream().mapToDouble(Double::doubleValue).sum());
        results.put("active_vms", vmList.size());
        results.put("total_cloudlets", cloudletList.size());
        results.put("finished_cloudlets", (int) cloudletList.stream().filter(c -> c.getStatus() == Cloudlet.Status.SUCCESS).count());
        
        double avgCpuUtilization = vmList.stream()
            .mapToDouble(vm -> vm.getCpuPercent() * 100)
            .average()
            .orElse(0.0);
        
        results.put("avg_cpu_utilization", avgCpuUtilization);
        
        return results;
    }
    
    /**
     * Update VM count during simulation (for auto-scaling)
     */
    public void updateVMCount(int newVmCount, double cpuUtilization, double memoryUtilization) {
        // Remove excess VMs
        while (vmList.size() > newVmCount) {
            Vm vm = vmList.remove(vmList.size() - 1);
            vm.destroy();
        }
        
        // Add new VMs
        while (vmList.size() < newVmCount) {
            long vmMips = hostMips;
            int vmPes = 1;
            long vmRam = (long) (hostRam / 4);
            long vmBw = (long) (hostBw / 10);
            long vmStorage = (long) (hostStorage / 100);
            
            Vm vm = new VmSimple(vmMips, vmPes);
            vm.setRam(vmRam);
            vm.setBw(vmBw);
            vm.setSize(vmStorage);
            vmList.add(vm);
        }
    }
    
    /**
     * Main method for testing
     */
    public static void main(String[] args) {
        SimulationRunner runner = new SimulationRunner();
        runner.initialize();
        
        runner.createVMs(5, 0.7, 0.6);
        runner.createCloudlets(10, 0.7, 0.6);
        
        runner.runSimulation();
        
        Map<String, Object> results = runner.getResults();
        System.out.println("Simulation Results:");
        System.out.println("Total Energy: " + results.get("total_energy"));
        System.out.println("Active VMs: " + results.get("active_vms"));
        System.out.println("Average CPU Utilization: " + results.get("avg_cpu_utilization"));
    }
}
