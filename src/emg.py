import sys
import geomstats.backend as gs
import joblib
import numpy as np
from geomstats.datasets.prepare_emg_data import TimeSeriesCovariance # translates raw electrical signal to Covariance Matricies
import geomstats.datasets.utils as data_utils # helper tool loading the EMG dataset
import random


MODEL = './models/logreg_pipeline.joblib'
N_ELECTRODES = 8    # data was collected with armband using 8 electrodes
N_STEPS = 100       # in the data prep, time series were sampled in 100 steps
MARGIN = 1000       # cuts off 
LABEL_MAP = {"rock": 0, "scissors": 1, "paper": 2, "ok": 3}
REVERSE_LABEL_MAP = {v: k for k, v in LABEL_MAP.items()} # reverses label map for easy lookup

# loads and processes data
def load_and_prep_data():

    print("Loading dataset...")
    
    # Load raw data
    data = data_utils.load_emg()
    data = data[data.label != "rest"]  # Remove 'rest' state. Model was not trained on rest

    # packs data for the TimeSeriesCovariance preprocessor
    data_dict = {
        "time": gs.array(data.time), # clock timestamps in signals
        "raw_data": gs.array(data[["c{}".format(i) for i in range(N_ELECTRODES)]]), # electrical voltage readings
        "label": gs.array(data.label), # label of signal
        "exp": gs.array(data.exp), # experiment id
    }

    # Transform into Covariance Matrices
    cov_data = TimeSeriesCovariance(data_dict, N_STEPS, N_ELECTRODES, LABEL_MAP, MARGIN)
    cov_data.transform() # translates raw voltage signals, calculates covariance matrices, and vectorizes them
    
    # Return the covecs (input model expects) and labels so we can look them up
    return cov_data.covecs, cov_data.labels

def main():
    # load the model
    try:
        print(f"Loading model from {MODEL}...")
        model = joblib.load(MODEL)
        print("Model loaded successfully.")
    except FileNotFoundError:
        print(f"Could not find {MODEL}. Ensure it is in the same directory as this.")
        sys.exit(1)

    # prep data pool
    covecs, labels = load_and_prep_data()

    print("\nEMG model demo.")
    print("Available inputs: rock, paper, scissors, ok")
    print("Type 'exit' to quit.\n")

    # demo loop
    while True:
        input_gest = input("Enter a gesture ('rock', 'paper', 'scissors', 'ok'): ").lower().strip()

        if input_gest == 'exit':
            print("Exiting...")
            break

        if input_gest not in LABEL_MAP:
            print(f"Invalid input. Please choose from: {list(LABEL_MAP.keys())}")
            continue

        # get list of matching indicies
        target_label = LABEL_MAP[input_gest]
        matching_indices = [i for i, label in enumerate(labels) if label == target_label]
        
        if not matching_indices:
            print("Error: No samples found for this gesture in the dataset.")
            continue

        # get random sample
        random_index = random.choice(matching_indices)
        sample_data = covecs[random_index]
        
        # Reshape for the model. Expects 1 row per sample
        sample_data_reshaped = sample_data.reshape(1, -1)

        try:
            prediciton = model.predict(sample_data_reshaped)[0]
            prediction_name = REVERSE_LABEL_MAP.get(prediciton, "Unknown")
            
            # Get confidence
            probs = model.predict_proba(sample_data_reshaped)[0]
            confidence = probs[prediciton] * 100


            print(f"\nResults: ")
            print(f"Input Signal Source: Random '{input_gest}' sample from dataset (ID: {random_index})")
            print(f"Model Prediction:    {prediction_name.upper()}")
            print(f"Confidence:          {confidence:.2f}%")
            
            if prediction_name == input_gest:
                print("Result:              CORRECT")
            else:
                print("Result:              INCORRECT")
            print("n")

        except Exception as e:
            print(f"Prediction error: {e}")
