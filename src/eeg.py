import sys
import os
import numpy as np
import random
import warnings
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from geomstats.geometry.spd_matrices import SPDMatrices, SPDAffineMetric
from geomstats.learning.preprocessing import ToTangentSpace

# warnings.filterwarnings("ignore", category=UserWarning)

DATA = "./data/eeg_data.npz"
LABEL_MAP = {"left": 0, "right": 1} 
REVERSE_LABEL_MAP = {0: "Left Hand", 1: "Right Hand"}

def load_data():

    try:
        data = np.load(DATA)
        covs = data['X']
        y = data['y']
        print(f"Successfully loaded data from {DATA}")
        return covs, y
    except Exception as e:
        sys.exit(f"\n[ERROR] Could not read the data file: {e}")

def train_model(covs, y):
    # Split data: Train on 80%, keep 20% for the interactive demo
    X_train, X_demo, y_train, y_demo = train_test_split(covs, y, test_size=0.2, random_state=42)
    
    print("Training Model...")
    
    n_electrodes = covs.shape[1]
    
    # Initialize Manifold
    manifold = SPDMatrices(n_electrodes, equip=False)
    manifold.equip_with_metric(SPDAffineMetric)

    # Define Pipeline
    pipeline = Pipeline(steps=[
        ("tangent_space", ToTangentSpace(space=manifold)),
        ("scaler", StandardScaler()),
        ("classifier", LogisticRegression())
    ])
    
    # Train
    pipeline.fit(X_train, y_train)
    
    # Accuracy Check
    accuracy = pipeline.score(X_train, y_train)
    print(f"Model ready. Training Accuracy: {accuracy*100:.1f}%")
    
    return pipeline, X_demo, y_demo

def main():
    # 1. Load Data
    covs, labels  = load_data()
    
    # 2. Train Model
    model, covs_demo, labels_demo = train_model(covs, labels)

    print("EEG Motor Imagery Demo")
    print("Available commands: left, right, exit")
    
    # 3. Interaction Loop
    while True:

        user_input = input("\nVisualize 'left', 'right', or 'exit': ").lower().strip()

        if user_input == 'exit':
            print("Exiting...")
            break

        if user_input not in LABEL_MAP:
            print(f"Invalid input. Please type 'left' or 'right'.")
            continue

        target_label = LABEL_MAP[user_input]
        
        # Filter demo pool for the requested class
        matching_indices = [i for i, label in enumerate(labels_demo) if label == target_label]

        if not matching_indices:
            print("No more test samples left for this specific class!")
            continue

        # Pick random trial from test set
        random_idx = random.choice(matching_indices)
        sample_cov = covs_demo[random_idx]
        
        # Reshape for prediction (1, 64, 64)
        sample_reshaped = np.array([sample_cov])
        
        # Predict
        prediction_idx = model.predict(sample_reshaped)[0]
        prediction_name = REVERSE_LABEL_MAP[prediction_idx]
        
        # Confidence
        probs = model.predict_proba(sample_reshaped)[0]
        confidence = probs[prediction_idx] * 100

        print(f"Input Signal Source: Test Set Trial #{random_idx}")
        print(f"Requested Action:    {user_input.upper()} HAND")
        print(f"Model Prediction:    {prediction_name.upper()}")
        print(f"Confidence:          {confidence:.2f}%")

        if prediction_idx == target_label:
            print("Result:              CORRECT")
        else:
            print("Result:              INCORRECT")

if __name__ == "__main__":
    main()