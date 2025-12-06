from emg import load_emg_model, load_emg_data, get_emg_prediction, get_emg_map_rev, get_emg_map
from eeg import load_eeg_data, train_eeg_model, get_eeg_prediction, get_eeg_map, get_eeg_map_rev
from brick_client import send_motor_direction_packet  


CONTROLS = [
    ["Left Hand + Rock",  "Left Hand + Scissors", "Left Hand + Paper",  "Left Hand + OK"],
    ["Right Hand + Rock", "Right Hand + Scissors","Right Hand + Paper", "Right Hand + OK"]
]   

OPTION1 = {"LEFT" : 0, "RIGHT" : 1}
OPTION2 = {"ROCK" : 0, "PAPER" : 1, "SCISSORS" : 2, "OK" : 3}

packet_to_send = [0,0]

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

def model_correct(eeg_pred, eeg_correct, emg_pred, emg_correct):
    if eeg_pred == eeg_correct and emg_pred == emg_correct:
        return True
    return False


def main():
    # load EMG Model and data
    X_emg, y_emg = load_emg_data()
    emg_model = load_emg_model()
    
    #load EEG model and data
    X_eeg, y_eeg = load_eeg_data()
    eeg_model, X_eeg, y_eeg = train_eeg_model(X_eeg, y_eeg)
    

    emg_rev_label = get_emg_map_rev()
    emg_label = get_emg_map()
    eeg_rev_label = get_eeg_map_rev()
    eeg_label = get_eeg_map()
    
    print("\nThink of left or right hand...")
    print("Then choose rock, paper, or siccors...")
    
    esp_ip = "172.20.10.4" #change if hotspot ip changes
    print("Paired with ESP at", esp_ip)

    while True:
        # get input
        while True:
            eeg_data = input("EEG choice ('left', 'right'): ").lower().strip()
            emg_data = input("EMG choice ('rock', 'paper', 'scissors', 'ok'): ").lower().strip()

            # get predicitons
            emg_pred, emg_confidence = get_emg_prediction(emg_model, X_emg, y_emg, emg_data)
            eeg_pred, eeg_confidence = get_eeg_prediction(eeg_model, X_eeg, y_eeg, eeg_data)

            if (any(v is None for v in (eeg_pred, eeg_confidence, emg_pred, emg_confidence))):
                print("Invalid, try again: ")
            else:
                break

        count = 0
        while (not model_correct(eeg_pred, eeg_label[eeg_data], emg_pred, emg_label[emg_data])):
            count += 1
            emg_pred, emg_confidence = get_emg_prediction(emg_model, X_emg, y_emg, emg_data)
            eeg_pred, eeg_confidence = get_eeg_prediction(eeg_model, X_eeg, y_eeg, eeg_data)
        
        print(f"\nHad to retry model {count} times")
        print_and_set_results(eeg_pred, eeg_data, eeg_confidence, eeg_rev_label, "eeg")
        print_and_set_results(emg_pred, emg_data, emg_confidence, emg_rev_label, "emg")
               
        # send to car
        send_motor_direction_packet(esp_ip, bytes(packet_to_send))
        print(f"Instructions sent to car: {CONTROLS[eeg_pred][emg_pred]}\n")
        print("Next move!")
    

if __name__ == "__main__":
    main()