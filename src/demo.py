from emg import load_emg_model, load_emg_data, get_emg_prediction, get_emg_map
from eeg import get_eeg_map, load_eeg_data, train_eeg_model, get_eeg_prediction
from brick_client import discover_esp, send_motor_direction_packet  


CONTROLS = [
    ["Left Hand + Rock",  "Left Hand + Scissors", "Left Hand + Paper",  "Left Hand + OK"],
    ["Right Hand + Rock", "Right Hand + Scissors","Right Hand + Paper", "Right Hand + OK"]
]   

OPTION1 = {"LEFT" : 0, "RIGHT" : 1}
OPTION2 = {"ROCK" : 0, "PAPER" : 1, "SCISSORS" : 2, "OK" : 3}

packet_to_send = [0,0]


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

def print_and_set_results(prediction, input_data, confidence, label_map, type: str):
    print(f"\n{type.upper()} results:")
    print(f"Input Signal Source: Random '{input_data}' sample from dataset")
    print(f"Model Prediction:    {label_map[prediction].upper()}")
    print(f"Confidence:          {confidence:.2f}%")
    
    if label_map[prediction] == input_data:
        print("Result:              CORRECT")
    else:
        print("Result:              INCORRECT")
    print("\n")

    if type == "eeg":
        packet_to_send[0] = OPTION1.get(label_map[prediction].upper())
    elif type == "emg":
        packet_to_send[1] = OPTION2.get(label_map[prediction].upper())

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
    
    esp_ip = discover_esp()

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
        

        print_and_set_results(eeg_prediction, eeg_data, eeg_confidence, eeg_label_map, "eeg")
        print_and_set_results(emg_prediction, emg_data, emg_confidence, emg_label_map, "emg")

        #send to car
        print(f"Instructions sent to car: {CONTROLS[eeg_prediction][emg_prediction]}")
        send_motor_direction_packet(esp_ip, bytes(packet_to_send))
    

if __name__ == "__main__":
    main()