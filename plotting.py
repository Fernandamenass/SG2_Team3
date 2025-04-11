import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import json
import os
from EUMV_FMS import run_all_runs

def generate_visualizations(all_results):
    sns.set_theme(style="whitegrid")

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
    plt.savefig('production_defect_rates.png')
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
    plt.savefig('station_occupancy_rates.png')
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
    plt.savefig('station_downtime.png')
    plt.close()

    # Plot 4: Supplier Utilization
    plt.figure(figsize=(8, 6))
    sns.boxplot(x=supplier_occs)
    plt.title('Supplier Utilization Rate')
    plt.xlabel('Utilization Rate')
    plt.savefig('supplier_utilization.png')
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
    plt.savefig('average_fixing_time.png')
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
    plt.savefig('bottleneck_delays.png')
    plt.close()


def generate_station_json(all_results, output_folder='../SG2_Tean3_MidTermII/data', filename='StationsInfo1.json'):
    import math
    os.makedirs(output_folder, exist_ok=True)

    num_stations = len(all_results[0]['stations'])
    station_ids = [f"WS-{111 + i * 111}" for i in range(num_stations)]
    station_names = [f"Station {chr(65 + i)}" for i in range(num_stations)]

    # Inicializar estructura por estación
    stations_data = []

    for i in range(num_stations):
        # Obtener 365 registros diarios para esta estación
        daily_metrics = [result['stations'][i] for result in all_results]

        def compute_block(day_start, day_end):
            block = daily_metrics[day_start:day_end]
            production = sum(day.get("good_products", 0) for day in block)
            rejected = sum(day.get("rejected_products", 0) for day in block)
            occupancy = sum(day.get("occupancy", 0) * 24 for day in block)
            accidents = sum(day.get("accidents", 0) for day in block)
            delay = sum(day.get("downtime", 0) or 0 for day in block)
            prod_time = sum(day.get("avg_fixing_time", 0) for day in block)

            count = len(block)
            rejection_pct = round(rejected / (production + rejected) * 100, 1) if (production + rejected) > 0 else 0.0

            return {
                "production": int(production),
                "occupancy_hours": int(occupancy),
                "avg_production_time_min": int(prod_time / count) if count else 0,
                "rejected_units": int(rejected),
                "rejection_percentage": rejection_pct,
                "avg_delay_minutes": int(delay / count) if count else 0,
                "accidents": int(accidents)
            }

        station_info = {
            "workstation_id": station_ids[i],
            "name": station_names[i],
            "daily_data": compute_block(0, 1),
            "weekly_data": compute_block(0, 7),
            "monthly_data": compute_block(0, 30),
            "quarterly_data": compute_block(0, 90),
            "yearly_data": compute_block(0, 365)
        }

        stations_data.append(station_info)

    output_path = os.path.join(output_folder, filename)
    with open(output_path, 'w') as f:
        json.dump(stations_data, f, indent=2)

    print(f"Archivo JSON generado en: {output_path}")


if __name__ == "__main__":
    simulation_results = run_all_runs(num_runs=365, simulation_time=5000)
    # generate_visualizations(simulation_results)
    generate_station_json(simulation_results, output_folder='./SG2_Tean3_MidTermII/data')
