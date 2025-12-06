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
REVERSE_LABEL_MAP = {0: "left", 1: "right"}

def load_eeg_data():
    try:
        data = np.load(DATA)
        covs = data['X']
        y = data['y']
        print(f"Successfully loaded EEG data from {DATA}")
        return covs, y
    except Exception as e:
        sys.exit(f"\n[ERROR] Could not read the EEG data file: {e}")

def train_eeg_model(covs, y):
    # Split data: Train on 80%, keep 20% for the interactive demo
    X_train, X_demo, y_train, y_demo = train_test_split(covs, y, test_size=0.2, random_state=42)
    
    print("Training EEG Model...")
    
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
    print(f"EEG model ready. Training Accuracy: {accuracy*100:.1f}%")
    
    return pipeline, X_demo, y_demo

def get_eeg_prediction(model, X, y, user_in):

    if user_in not in LABEL_MAP:
        print(f"Invalid input. Please type 'left' or 'right'.")
        return None, None

    target_label = LABEL_MAP[user_in]
    
    # Filter demo pool for the requested class
    matching_indices = [i for i, label in enumerate(y) if label == target_label]

    if not matching_indices:
        print("No more test samples left for this specific class!")
        return None, None

    # Pick random trial from test set
    random_idx = random.choice(matching_indices)
    sample_cov = X[random_idx]
    
    # Reshape for prediction (1, 64, 64)
    sample_reshaped = np.array([sample_cov])
    
    # Predict
    prediction = model.predict(sample_reshaped)[0]
    
    # Confidence
    probs = model.predict_proba(sample_reshaped)[0]
    confidence = probs[prediction] * 100

    return prediction, confidence

def get_eeg_map_rev():
    return REVERSE_LABEL_MAP

def get_eeg_map():
    return LABEL_MAP