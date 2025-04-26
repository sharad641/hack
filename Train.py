# Train.py
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import joblib
import numpy as np

# Load data with error handling
try:
    # First attempt with automatic column detection
    data = pd.read_csv('typing_data.csv', on_bad_lines='warn')
except pd.errors.ParserError:
    # If errors occur, manually specify columns
    cols = ['dwell_mean', 'dwell_std', 'flight_mean', 'flight_std', 'score']
    data = pd.read_csv('typing_data.csv', names=cols, skiprows=1, on_bad_lines='skip')

# Clean data
data = data.dropna()
data = data[(np.abs(data['dwell_mean']) < 1000) &
          (np.abs(data['flight_mean']) < 1000)]  # Remove outliers

# Prepare features
features = data[['dwell_mean', 'dwell_std', 'flight_mean', 'flight_std']]

# Normalize
scaler = StandardScaler()
scaled_features = scaler.fit_transform(features)

# Train model
model = IsolationForest(
    n_estimators=150,
    contamination=0.05,
    max_features=0.8,
    random_state=42
)
model.fit(scaled_features)

# Save artifacts
joblib.dump(model, 'typing_model.pkl')
joblib.dump(scaler, 'scaler.pkl')
print(f"Model trained successfully on {len(data)} valid samples!")

# Print data quality report
print("\nData Quality Report:")
print(f"Total rows processed: {len(data)}")
print(f"Invalid rows skipped: {len(pd.read_csv('typing_data.csv')) - len(data)}")
print("Feature distributions:")
print(features.describe())