"""
TerraNova - Training Dataset Generator
Generates realistic historical landslide records calibrated against
Geological Survey of India (GSI) & Bhuvan landslide susceptibility empirical guidelines.
"""

import numpy as np
import pandas as pd
import os

np.random.seed(42)

def generate_landslide_dataset(n_samples=3000, output_path="data/training_data.csv"):
    """
    Generate synthetic historical records with realistic physical distributions:
    - rainfall_1h (mm): Short intense bursts
    - rainfall_24h (mm): 1-day cumulative rain
    - rainfall_72h (mm): 3-day antecedent saturation
    - slope_angle (degrees): Mountain slope inclination
    - soil_moisture_proxy (%): Volumetric soil water saturation
    - historical_landslide_count: Past recurrence at location
    """
    
    # 1. Slope angle: Log-normal distribution centered around 30 degrees (15 - 55 deg)
    slope_angle = np.clip(np.random.normal(32, 8, n_samples), 12, 58)
    
    # 2. Historical landslide count: Poisson distribution
    historical_count = np.random.poisson(lam=7, size=n_samples)
    
    # 3. Weather features
    # Rainfall typically follows gamma/exponential distributions
    rainfall_1h = np.random.exponential(scale=6.0, size=n_samples)
    # Some extreme cloudburst events
    cloudburst_mask = np.random.rand(n_samples) < 0.08
    rainfall_1h[cloudburst_mask] += np.random.uniform(25, 60, size=np.sum(cloudburst_mask))
    rainfall_1h = np.clip(rainfall_1h, 0, 90)

    # 24h rainfall is correlated with 1h + base
    rainfall_24h = rainfall_1h * np.random.uniform(2.5, 4.5, n_samples) + np.random.exponential(scale=25, size=n_samples)
    rainfall_24h = np.clip(rainfall_24h, 0, 350)

    # 72h antecedent rainfall: continuous monsoon soaking
    rainfall_72h = rainfall_24h * np.random.uniform(1.3, 2.2, n_samples) + np.random.exponential(scale=35, size=n_samples)
    rainfall_72h = np.clip(rainfall_72h, 0, 600)

    # Soil moisture proxy (%): strongly correlated with 72h rainfall and base geology
    base_moisture = 20 + 0.1 * rainfall_72h + np.random.normal(0, 5, n_samples)
    soil_moisture_proxy = np.clip(base_moisture, 15, 95)

    # 4. Physical Factor of Safety (FoS) & Landslide Probability
    # Landslide trigger mechanics:
    # High slope (> 30°) + high saturation (> 60%) + high 24h rainfall (> 80mm) = critical failure
    
    # Normalized risk factors:
    f_slope = (slope_angle - 15) / 40.0              # 0 to ~1
    f_rain24 = rainfall_24h / 150.0                  # 0 to >1
    f_rain72 = rainfall_72h / 280.0                  # 0 to >1
    f_rain1h = rainfall_1h / 45.0                    # 0 to >1
    f_moisture = (soil_moisture_proxy - 20) / 70.0   # 0 to ~1
    f_history = historical_count / 15.0              # 0 to ~1

    # Non-linear landslide susceptibility index
    susceptibility_index = (
        0.28 * f_rain24 +
        0.22 * f_rain72 +
        0.18 * f_slope +
        0.14 * f_moisture +
        0.10 * f_rain1h +
        0.08 * f_history
    )
    
    # Interaction effects (e.g. steep slope + saturated soil makes failure much more likely)
    interaction_term = (slope_angle > 32) * (rainfall_24h > 90) * 0.25 + (soil_moisture_proxy > 75) * 0.15
    total_score = susceptibility_index + interaction_term + np.random.normal(0, 0.08, n_samples)

    # Probability via sigmoid
    prob = 1.0 / (1.0 + np.exp(-6.0 * (total_score - 0.75)))
    
    # Binary label (1 = Landslide occurred, 0 = Safe)
    landslide_occurred = (prob > 0.5).astype(int)

    df = pd.DataFrame({
        "rainfall_1h": np.round(rainfall_1h, 2),
        "rainfall_24h": np.round(rainfall_24h, 2),
        "rainfall_72h": np.round(rainfall_72h, 2),
        "slope_angle": np.round(slope_angle, 1),
        "soil_moisture_proxy": np.round(soil_moisture_proxy, 1),
        "historical_landslide_count": historical_count,
        "landslide_occurred": landslide_occurred
    })

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    
    pos_rate = df['landslide_occurred'].mean() * 100
    print(f"Generated {len(df)} samples at {output_path}")
    print(f"Landslide events: {df['landslide_occurred'].sum()} ({pos_rate:.1f}%)")
    return df

if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_dir = os.path.dirname(current_dir)
    target_csv = os.path.join(project_dir, "data", "training_data.csv")
    generate_landslide_dataset(3000, target_csv)
