from emg import load_emg_model, load_emg_data, get_emg_prediction, get_emg_map
from eeg import get_eeg_map, load_eeg_data, train_eeg_model, get_eeg_prediction

CONTROLS = [
    ["Left Hand + Rock",  "Left Hand + Scissors", "Left Hand + Paper",  "Left Hand + OK"],
    ["Right Hand + Rock", "Right Hand + Scissors","Right Hand + Paper", "Right Hand + OK"]
]        

def print_results(prediction, input_data, confidence, label_map, type: str):
    print(f"\n{type.upper()} results:")
    print(f"Input Signal Source: Random '{input_data}' sample from dataset")
    print(f"Model Prediction:    {label_map[prediction].upper()}")
    print(f"Confidence:          {confidence:.2f}%")
    
    if label_map[prediction] == input_data:
        print("Result:              CORRECT")
    else:
        print("Result:              INCORRECT")
    print("\n")


def main():

    # load EMG Model and data
    X_emg, y_emg = load_emg_data()
    emg_model = load_emg_model()
    
    #load EEG model and data
    X_eeg, y_eeg = load_eeg_data()
    eeg_model, X_eeg, y_eeg = train_eeg_model(X_eeg, y_eeg)
    

    emg_label_map = get_emg_map()
    eeg_label_map = get_eeg_map()
    
    print("\nThink of left or right hand...")
    print("Then choose rock, paper, or siccors...")
    
    while True:
        # get input
        while True:
            user_in = input("Enter choices here (eeg, emg): ").lower().split(',')
            eeg_data, emg_data = [choice.strip() for choice in user_in]

            # get predicitons
            emg_prediction, emg_confidence = get_emg_prediction(emg_model, X_emg, y_emg, emg_data)
            eeg_prediction, eeg_confidence = get_eeg_prediction(eeg_model, X_eeg, y_eeg, eeg_data)

            if (any(v is None for v in (eeg_prediction, eeg_confidence, emg_prediction, emg_confidence))):
                print("Invalid, try again: ")
            else:
                break

        print_results(eeg_prediction, eeg_data, eeg_confidence, eeg_label_map, "eeg")
        print_results(emg_prediction, emg_data, emg_confidence, emg_label_map, "emg")

        #send to car
        print(f"Instructions sent to car: {CONTROLS[eeg_prediction][emg_prediction]}")

if __name__ == "__main__":
    main()