import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import json
import os
from EUMV_FMS import run_all_runs

def generate_visualizations(all_results):
    """Generate standard visualization plots of simulation results
    
    @param all_results List of simulation run results
    """
    sns.set_theme(style="whitegrid")
    os.makedirs("plots", exist_ok=True)

    productions = [result['production'] for result in all_results]
    rejections = [result['rejected'] for result in all_results]
    defect_rates = [rej / (prod + rej) if (prod + rej) > 0 else 0 for prod, rej in zip(productions, rejections)]
    supplier_occs = [result['supplier_occupancy'] for result in all_results]

    # Plot 1: Production and Defect Rates
    plt.figure(figsize=(14, 6))
    plt.subplot(1, 2, 1)
    sns.boxplot(x=productions)
    plt.title('Production per Run')
    plt.xlabel('Total Production')

    plt.subplot(1, 2, 2)
    sns.boxplot(x=defect_rates)
    plt.title('Defect Rate per Run')
    plt.xlabel('Defect Rate')
    plt.tight_layout()
    plt.savefig('plots/production_defect_rates.png')
    plt.close()

    # Plot 2: Station Occupancy Rates
    occupancy_data = []
    for station in range(6):
        occupancies = [result['stations'][station]['occupancy'] for result in all_results]
        occupancy_data.append(occupancies)

    plt.figure(figsize=(14, 8))
    sns.boxplot(data=occupancy_data)
    plt.xticks(range(6), [f'Station {i}' for i in range(6)])
    plt.title('Station Occupancy Rates')
    plt.ylabel('Occupancy Rate')
    plt.savefig('plots/station_occupancy_rates.png')
    plt.close()

    # Plot 3: Station Downtime
    downtime_data = []
    for station in range(6):
        downtimes = [result['stations'][station]['downtime'] for result in all_results]
        downtime_data.append(downtimes)

    plt.figure(figsize=(14, 8))
    sns.boxplot(data=downtime_data)
    plt.xticks(range(6), [f'Station {i}' for i in range(6)])
    plt.title('Station Downtime')
    plt.ylabel('Downtime (Units)')
    plt.savefig('plots/station_downtime.png')
    plt.close()

    # Plot 4: Supplier Utilization
    plt.figure(figsize=(8, 6))
    sns.boxplot(x=supplier_occs)
    plt.title('Supplier Utilization Rate')
    plt.xlabel('Utilization Rate')
    plt.savefig('plots/supplier_utilization.png')
    plt.close()

    # Plot 5: Average Fixing Time per Station
    fixing_data = []
    for station in range(6):
        fixes = [result['stations'][station]['avg_fixing_time'] for result in all_results]
        fixing_data.append(fixes)

    plt.figure(figsize=(14, 8))
    sns.boxplot(data=fixing_data)
    plt.xticks(range(6), [f'Station {i}' for i in range(6)])
    plt.title('Average Fixing Time per Station')
    plt.ylabel('Fixing Time (Units)')
    plt.savefig('plots/average_fixing_time.png')
    plt.close()

    # Plot 6: Bottleneck Delays
    bottleneck_data = []
    for station in range(6):
        delays = [result['stations'][station]['avg_bottleneck_delay'] for result in all_results]
        bottleneck_data.append(delays)

    plt.figure(figsize=(14, 8))
    sns.boxplot(data=bottleneck_data)
    plt.xticks(range(6), [f'Station {i}' for i in range(6)])
    plt.title('Average Bottleneck Delay per Station')
    plt.ylabel('Delay (Units)')
    plt.savefig('plots/bottleneck_delays.png')
    plt.close()
    
    print("Visualization plots generated in the 'plots' directory")


def generate_station_json(all_results, output_folder='./data', filename='StationsInfo.json'):
    """Generate station-level JSON data for dashboard
    
    @param all_results List of simulation run results
    @param output_folder Output directory for JSON files
    @param filename Output JSON filename
    """
    import os
    import json
    
    os.makedirs(output_folder, exist_ok=True)

    num_stations = len(all_results[0]['stations'])
    station_ids = [f"WS-{111 + i * 111}" for i in range(num_stations)]
    station_names = [f"Station {chr(65 + i)}" for i in range(num_stations)]

    # Initialize station data structure
    stations_data = []

    for i in range(num_stations):
        # Get metrics for this station from all runs
        daily_metrics = [result['stations'][i] for result in all_results]

        def compute_block(day_start, day_end):
            """Compute aggregated metrics for a time period
            
            @param day_start Start day index
            @param day_end End day index
            @return Dict of aggregated metrics
            """
            block = daily_metrics[day_start:day_end]
            if not block:  # Handle empty block case
                return {
                    "production": 0,
                    "occupancy_hours": 0,
                    "avg_production_time_min": 0,
                    "rejected_units": 0,
                    "rejection_percentage": 0.0,
                    "avg_delay_minutes": 0,
                    "accidents": 0
                }
                
            # Fixed lines to correctly access good_products and rejected_products
            production = sum(day["good_products"] for day in block)
            rejected = sum(day["rejected_products"] for day in block)
            occupancy = sum(day.get("occupancy", 0) * 24 for day in block)
            accidents = sum(day.get("accidents", 0) for day in block)
            delay = sum(day.get("downtime", 0) or 0 for day in block)
            
            # Avoid division by zero
            count = len(block)
            avg_fixing_time = sum(day.get("avg_fixing_time", 0) for day in block)
            
            rejection_pct = 0.0
            if production + rejected > 0:
                rejection_pct = round(rejected / (production + rejected) * 100, 1)

            return {
                "production": int(production),
                "occupancy_hours": int(occupancy),
                "avg_production_time_min": int(avg_fixing_time / count) if count else 0,
                "rejected_units": int(rejected),
                "rejection_percentage": rejection_pct,
                "avg_delay_minutes": int(delay / count) if count else 0,
                "accidents": int(accidents)
            }

        # Limit to available data length
        available_days = len(daily_metrics)
        station_info = {
            "workstation_id": station_ids[i],
            "name": station_names[i],
            "daily_data": compute_block(0, min(1, available_days)),
            "weekly_data": compute_block(0, min(7, available_days)),
            "monthly_data": compute_block(0, min(30, available_days)),
            "quarterly_data": compute_block(0, min(90, available_days)),
            "yearly_data": compute_block(0, min(365, available_days))
        }

        stations_data.append(station_info)

    output_path = os.path.join(output_folder, filename)
    with open(output_path, 'w') as f:
        json.dump(stations_data, f, indent=2)

    print(f"Station JSON file generated: {output_path}")


def generate_product_json(all_results, output_folder='./data', filename='ProductsInfo.json'):
    """Generate product-level JSON data for dashboard
    
    @param all_results List of simulation run results
    @param output_folder Output directory for JSON files
    @param filename Output JSON filename
    """
    os.makedirs(output_folder, exist_ok=True)
    
    # Extract product-level data
    product_data = []
    for run in all_results:
        if 'products' in run:  # Check if products key exists
            run_id = run.get('run_id', 0)
            for product_id, metrics in run['products'].items():
                # Convert product_id to string if it's not already
                product_id_str = str(product_id)
                
                # Filter out incomplete product data
                if metrics.get("end_time") is None:
                    continue
                    
                # Create product entry with basic metrics
                product_entry = {
                    "product_id": f"{run_id}-{product_id_str}",
                    "run_id": run_id,
                    "cycle_time": metrics["end_time"] - metrics["start_time"],
                    "wait_time": metrics["total_wait_time"],
                    "process_time": metrics["total_process_time"],
                    "quality": metrics["quality"],
                    "stations_data": []
                }
                
                # Add station visit data
                for visit in metrics.get("stations_visit", []):
                    station_id = visit.get("station_id", 0)
                    product_entry["stations_data"].append({
                        "station_id": f"WS-{111 + station_id * 111}",
                        "station_name": f"Station {chr(65 + station_id)}",
                        "wait_time": visit.get("wait_time", 0),
                        "process_time": visit.get("process_time", 0)
                    })
                
                product_data.append(product_entry)
    
    output_path = os.path.join(output_folder, filename)
    with open(output_path, 'w') as f:
        json.dump(product_data, f, indent=2)
    
    print(f"Product JSON file generated: {output_path}")


def generate_plant_json(all_results, output_folder='./data', filename='PlantInfo.json'):
    """Generate plant-level JSON data for dashboard
    
    @param all_results List of simulation run results
    @param output_folder Output directory for JSON files
    @param filename Output JSON filename
    """
    os.makedirs(output_folder, exist_ok=True)
    
    available_days = len(all_results)
    
    # Generate plant-level summary data
    plant_data = {
        "daily_summary": generate_plant_summary(all_results, min(1, available_days)),
        "weekly_summary": generate_plant_summary(all_results, min(7, available_days)),
        "monthly_summary": generate_plant_summary(all_results, min(30, available_days)),
        "quarterly_summary": generate_plant_summary(all_results, min(90, available_days)),
        "yearly_summary": generate_plant_summary(all_results, min(365, available_days))
    }
    
    output_path = os.path.join(output_folder, filename)
    with open(output_path, 'w') as f:
        json.dump(plant_data, f, indent=2)
    
    print(f"Plant JSON file generated: {output_path}")


def generate_plant_summary(all_results, days):
    """Generate plant-level summary for specified number of days
    
    @param all_results List of simulation run results
    @param days Number of days to include in summary
    @return Dict with plant-level summary metrics
    """
    if days <= 0 or not all_results:
        return {
            "total_production": 0,
            "total_rejected": 0,
            "rejection_rate": 0,
            "supplier_utilization": 0,
            "station_metrics": {str(i): {"avg_occupancy": 0, "avg_downtime": 0, "avg_bottleneck_delay": 0} for i in range(6)}
        }
    
    results_subset = all_results[:days]
    
    # Calculate aggregated metrics
    total_production = sum(r.get('production', 0) for r in results_subset)
    total_rejected = sum(r.get('rejected', 0) for r in results_subset)
    
    rejection_rate = 0
    if total_production + total_rejected > 0:
        rejection_rate = total_rejected / (total_production + total_rejected)
    
    supplier_utilization = 0
    if results_subset:
        supplier_utilization = sum(r.get('supplier_occupancy', 0) for r in results_subset) / len(results_subset)
    
    # Build station metrics
    station_metrics = {}
    for i in range(6):
        station_metrics[str(i)] = {
            "avg_occupancy": 0,
            "avg_downtime": 0,
            "avg_bottleneck_delay": 0
        }
        
        if results_subset:
            station_metrics[str(i)]["avg_occupancy"] = sum(r.get('stations', {}).get(i, {}).get('occupancy', 0) for r in results_subset) / len(results_subset)
            station_metrics[str(i)]["avg_downtime"] = sum(r.get('stations', {}).get(i, {}).get('downtime', 0) for r in results_subset) / len(results_subset)
            station_metrics[str(i)]["avg_bottleneck_delay"] = sum(r.get('stations', {}).get(i, {}).get('avg_bottleneck_delay', 0) for r in results_subset) / len(results_subset)
    
    return {
        "total_production": total_production,
        "total_rejected": total_rejected,
        "rejection_rate": rejection_rate,
        "supplier_utilization": supplier_utilization,
        "station_metrics": station_metrics
    }


def generate_complete_json(all_results, output_folder='./data'):
    """Generate all JSON files needed for the dashboard
    
    @param all_results List of simulation run results
    @param output_folder Output directory for JSON files
    """
    os.makedirs(output_folder, exist_ok=True)
    
    # Generate all three JSON files
    generate_station_json(all_results, output_folder)
    generate_product_json(all_results, output_folder)
    generate_plant_json(all_results, output_folder)
    
    print(f"All JSON files generated in: {output_folder}")


def run_complete_pipeline(num_runs=365, simulation_time=5000, output_folder='./data'):
    """Run complete pipeline: simulation, data processing, and JSON generation
    
    @param num_runs Number of simulation runs to execute
    @param simulation_time Duration of each simulation run
    @param output_folder Output directory for JSON files
    """
    print("Running manufacturing simulation...")
    simulation_results = run_all_runs(num_runs=num_runs, simulation_time=simulation_time)
    
    print("Generating visualization files...")
    generate_visualizations(simulation_results)
    
    print("Generating dashboard data files...")
    generate_complete_json(simulation_results, output_folder)
    
    print("Pipeline completed successfully!")
    return simulation_results


if __name__ == "__main__":
    run_complete_pipeline()