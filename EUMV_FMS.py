"""! @file manufacturing_simulation.py
    @brief Manufacturing facility simulation with multiple stations and quality control.
    
    This module implements a discrete event simulation of a manufacturing facility
    using SimPy. The facility consists of 6 stations with various failure rates,
    processing times, and a quality control system.

    @author: Eduardo Ulises Martinez
    @author: Fernanda Mena
    @author: Brandon Avalos
"""

import time
import simpy
import numpy as np
from dataclasses import dataclass
from typing import List, Dict

np.random.seed(int(time.time()))

@dataclass
class StationMetrics:
    """! Class to track performance metrics for each manufacturing station.
    
    @details Maintains counters and time series data for various performance indicators
    including processing times, maintenance events, and bottleneck analysis.
    """
    processed_items: int = 0
    busy_time: float = 0
    downtime: float = 0
    fixing_times: List[float] = None
    waiting_times: List[float] = None
    bottleneck_delays: List[float] = None
    good_products: int = 0
    rejected_products: int = 0
    accident_count: int = 0

    
    def __post_init__(self):
        """! Initialize empty lists for data collection."""
        self.fixing_times = []
        self.waiting_times = []
        self.bottleneck_delays = []
        self.good_products = 0
        self.rejected_products = 0
        self.accident_count = 0


class ManufacturingFacility:
    """! Main class representing the manufacturing facility simulation.
    
    @details Implements a production line with 6 stations, including parallel processing
    capabilities, maintenance events, and quality control.
    """
    def __init__(self, env):
        """! Initialize the manufacturing facility.
        @param env SimPy environment instance
        """
        self.env = env
        self.stations = [simpy.Resource(env, capacity=1) for _ in range(6)]
        self.bins = [25, 25, 25, 25, 25, 25]
        self.suppliers = simpy.Resource(env, capacity=3)
        
        self.metrics = {i: StationMetrics() for i in range(6)}
        self.total_production = 0
        self.rejected_products = 0
        self.supplier_busy_time = 0
        self.last_product_time = 0
        self.failure_probs = [0.02, 0.01, 0.05, 0.15, 0.07, 0.06]
        self.product_metrics = {}
        
    def resupply_bin(self, station_id):
        """! Process to resupply materials to a station's bin.
        @param station_id Index of the station that is requiring resupply
        @return Generator for SimPy environment
        """
        start_time = self.env.now
        with self.suppliers.request() as req:
            yield req
            delay = abs(np.random.normal(2, 0.5))
            yield self.env.timeout(delay)
            self.bins[station_id] = 25
            self.supplier_busy_time += self.env.now - start_time

    def process_station(self, product_id, station_id, start_queue_time):
        """! Process a product at a specific station.
        @param product_id Unique identifier for the product
        @param station_id Index of the processing station
        @param start_queue_time Time when product entered the station's queue
        @return Generator for SimPy environment
        """

        self.metrics[station_id].waiting_times.append(self.env.now - start_queue_time)
        
        process_time = abs(np.random.normal(4, 1))
        yield self.env.timeout(process_time)
        
        self.metrics[station_id].processed_items += 1
        self.metrics[station_id].busy_time += process_time
    
        if self.metrics[station_id].processed_items % 5 == 0:
            if np.random.random() < self.failure_probs[station_id]:
                fixing_time = np.random.exponential(3)
                yield self.env.timeout(fixing_time)
                self.metrics[station_id].downtime += fixing_time
                self.metrics[station_id].fixing_times.append(fixing_time)
                
        if self.last_product_time > 0:
            delay = self.env.now - self.last_product_time - process_time
            if delay > 0:
                self.metrics[station_id].bottleneck_delays.append(delay)
        self.last_product_time = self.env.now
        
        # Simulación de rechazo por estación (opcional: puedes variar la probabilidad por estación)
        if np.random.random() < 0.01:  # 1% de rechazo por estación (puedes ajustar)
            self.metrics[station_id].rejected_products += 1
            self.product_metrics[product_id]["quality"] = "rejected"
            raise simpy.Interrupt(f"Producto {product_id} rechazado en estación {station_id}")


    def process_product(self, product_id):
        """! Process a single product through all stations.
        @param product_id Unique identifier for the product
        @return Generator for SimPy environment
        """

        self.product_metrics[product_id] = {
            "start_time": self.env.now,
            "end_time": None,
            "stations_visit": [],
            "quality": "unknown",
            "total_wait_time": 0,
            "total_process_time": 0
        }

        # Procesar por estaciones secuenciales (0 a 3)
        for i in range(4):
            station_start = self.env.now
            if self.bins[i] <= 0:
                yield self.env.process(self.resupply_bin(i))
            self.bins[i] -= 1

            start_queue = self.env.now
            with self.stations[i].request() as req:
                yield req
                wait_time = self.env.now - start_queue
                self.product_metrics[product_id]["total_wait_time"] += wait_time

                process_start = self.env.now
                try:
                    yield self.env.process(self.process_station(product_id, i, start_queue))
                except simpy.Interrupt:
                    self.metrics[i].rejected_products += 1
                    self.rejected_products += 1
                    self.product_metrics[product_id]["quality"] = "rejected"
                    self.product_metrics[product_id]["end_time"] = self.env.now
                    return

                process_time = self.env.now - process_start
                self.product_metrics[product_id]["stations_visit"].append({
                    "station_id": i,
                    "entry_time": station_start,
                    "exit_time": self.env.now,
                    "wait_time": wait_time,
                    "process_time": process_time
                })
                self.product_metrics[product_id]["total_process_time"] += process_time
                self.metrics[i].good_products += 1

        # Elegir primera estación paralela (4 o 5)
        if len(self.stations[4].queue) <= len(self.stations[5].queue):
            parallel_first = 4
        else:
            parallel_first = 5

        # Procesar en primera paralela
        station_start = self.env.now
        if self.bins[parallel_first] <= 0:
            yield self.env.process(self.resupply_bin(parallel_first))
        self.bins[parallel_first] -= 1

        start_queue = self.env.now
        with self.stations[parallel_first].request() as req:
            yield req
            wait_time = self.env.now - start_queue
            self.product_metrics[product_id]["total_wait_time"] += wait_time

            process_start = self.env.now
            try:
                yield self.env.process(self.process_station(product_id, parallel_first, start_queue))
            except simpy.Interrupt:
                self.metrics[parallel_first].rejected_products += 1
                self.rejected_products += 1
                self.product_metrics[product_id]["quality"] = "rejected"
                self.product_metrics[product_id]["end_time"] = self.env.now
                return

            process_time = self.env.now - process_start
            self.product_metrics[product_id]["stations_visit"].append({
                "station_id": parallel_first,
                "entry_time": station_start,
                "exit_time": self.env.now,
                "wait_time": wait_time,
                "process_time": process_time
            })
            self.product_metrics[product_id]["total_process_time"] += process_time
            self.metrics[parallel_first].good_products += 1

        # Segunda estación paralela
        parallel_second = 9 - parallel_first
        station_start = self.env.now
        if self.bins[parallel_second] <= 0:
            yield self.env.process(self.resupply_bin(parallel_second))
        self.bins[parallel_second] -= 1

        start_queue = self.env.now
        with self.stations[parallel_second].request() as req:
            yield req
            wait_time = self.env.now - start_queue
            self.product_metrics[product_id]["total_wait_time"] += wait_time

            process_start = self.env.now
            try:
                yield self.env.process(self.process_station(product_id, parallel_second, start_queue))
            except simpy.Interrupt:
                self.metrics[parallel_second].rejected_products += 1
                self.rejected_products += 1
                self.product_metrics[product_id]["quality"] = "rejected"
                self.product_metrics[product_id]["end_time"] = self.env.now
                return

            process_time = self.env.now - process_start
            self.product_metrics[product_id]["stations_visit"].append({
                "station_id": parallel_second,
                "entry_time": station_start,
                "exit_time": self.env.now,
                "wait_time": wait_time,
                "process_time": process_time
            })
            self.product_metrics[product_id]["total_process_time"] += process_time
            self.metrics[parallel_second].good_products += 1

        # Si llegó al final sin rechazo
        self.total_production += 1
        self.product_metrics[product_id]["quality"] = "good"
        self.product_metrics[product_id]["end_time"] = self.env.now

    
    
    # This is the fixed method - it no longer creates a new facility and environment
    def run_production(self, simulation_time):
        """! Run the manufacturing facility production process
        @param simulation_time Total time to simulate
        @return Generator for SimPy environment
        """
        product_id = 0
        while self.env.now < simulation_time:
            if np.random.random() < 0.0001 / (simulation_time / 24): 
                accident_station = np.random.randint(0, 6)
                self.metrics[accident_station].accident_count += 1
                print(f"Facility accident at time {self.env.now}. Stopping this simulation run.")
                break
            
            self.env.process(self.process_product(product_id))
            product_id += 1
            
            if len(self.stations[0].queue) > 5:
                yield self.env.timeout(2)
            else:
                yield self.env.timeout(1)

def run_simulation(run_id, simulation_time):
    """! Execute a single simulation run with specified parameters.
    @param run_id Identifier for the simulation run
    @param simulation_time Total time to simulate
    @return Dict containing simulation results and metrics
    """
    np.random.seed(run_id + 1000)
    env = simpy.Environment()
    facility = ManufacturingFacility(env)
    
    # Fixed: Use the new run_production method instead of recursively calling run_simulation
    env.process(facility.run_production(simulation_time))
    env.run(until=simulation_time)
    
    results = {
        'run_id': run_id,
        'production': facility.total_production,
        'rejected': facility.rejected_products,
        'supplier_occupancy': facility.supplier_busy_time / simulation_time,
        'stations': {},
        'products': facility.product_metrics
    }
    
    for i, metrics in facility.metrics.items():
            results['stations'][i] = {
        'occupancy': metrics.busy_time / simulation_time,
        'downtime': metrics.downtime,
        'avg_fixing_time': np.mean(metrics.fixing_times) if metrics.fixing_times else 0,
        'avg_waiting_time': np.mean(metrics.waiting_times) if metrics.waiting_times else 0,
        'avg_bottleneck_delay': np.mean(metrics.bottleneck_delays) if metrics.bottleneck_delays else 0,
        'good_products': metrics.good_products,
        'rejected_products': metrics.rejected_products,
        'accidents': metrics.accident_count
    }

    
    return results

def run_simulation_per_run(num_runs, simulation_time):
    """! Execute multiple simulation runs and display detailed results.
    @param num_runs Number of simulation runs to execute
    @param simulation_time Duration of each simulation run
    @return List of results from all runs
    """
    all_results = []
    
    for run_id in range(num_runs):
        result = run_simulation(run_id, simulation_time)
        all_results.append(result)
    
    print("\nPer-Run Simulation Results:")
    print("-" * 50)
    for result in all_results:
        print(f"\nRun {result['run_id']}:")
        print(f"  Production: {result['production']}")
        print(f"  Rejected Products: {result['rejected']}")
        print(f"  Supplier Occupancy: {result['supplier_occupancy']:.3f}")
        for station in range(6):
            print(f"  Station {station}:")
            print(f"    Occupancy Rate: {result['stations'][station]['occupancy']:.3f}")
            print(f"    Downtime: {result['stations'][station]['downtime']:.2f}")
            print(f"    Avg Fixing Time: {result['stations'][station]['avg_fixing_time']:.2f}")
            print(f"    Avg Waiting Time: {result['stations'][station]['avg_waiting_time']:.2f}")
            print(f"    Avg Bottleneck Delay: {result['stations'][station]['avg_bottleneck_delay']:.2f}")
    
    return all_results

def run_all_runs(num_runs, simulation_time):
    """! Execute multiple simulation runs and generate summary statistics.
    @param num_runs Number of simulation runs to execute
    @param simulation_time Duration of each simulation run
    @return List of results from all runs
    """
    all_results = []
    
    for run_id in range(num_runs):
        result = run_simulation(run_id, simulation_time)
        all_results.append(result)
    
    print("\nSimulation Results Summary (All Runs):")
    print("-" * 50)
    
    productions = [r['production'] for r in all_results]
    rejections = [r['rejected'] for r in all_results]
    supplier_occs = [r['supplier_occupancy'] for r in all_results]
    
    print(f"Average Production per Run: {np.mean(productions):.2f}")
    print(f"Average Rejection Rate: {np.mean([r/(p+r) for p,r in zip(productions, rejections) if (p+r) > 0]):.3f}")
    print(f"Average Supplier Occupancy: {np.mean(supplier_occs):.3f}")
    
    print("\nWorkstation Statistics (All Runs):")
    for station in range(6):
        stats = [r['stations'][station] for r in all_results]
        print(f"\nStation {station}:")
        print(f"  Occupancy Rate: {np.mean([s['occupancy'] for s in stats]):.3f}")
        print(f"  Average Downtime: {np.mean([s['downtime'] for s in stats]):.2f}")
        print(f"  Average Waiting Time: {np.mean([s['avg_waiting_time'] for s in stats]):.2f}")
        print(f"  Average Fixing Time: {np.mean([s['avg_fixing_time'] for s in stats]):.2f}")
        print(f"  Average Bottleneck Delay: {np.mean([s['avg_bottleneck_delay'] for s in stats]):.2f}")
    
    return all_results

if __name__ == "__main__":
    run_all_runs(num_runs=5, simulation_time=5000)