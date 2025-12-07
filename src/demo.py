from emg import load_emg_model, load_emg_data, get_emg_prediction, get_emg_maps
from eeg import load_eeg_data, train_eeg_model, get_eeg_prediction, get_eeg_maps
from brick_client import send_motor_direction_packet  

CONTROLS = [
    ["Left Hand + Rock",  "Left Hand + Paper", "Left Hand + Scissors",  "Left Hand + OK"],
    ["Right Hand + Rock", "Right Hand + Paper","Right Hand + Scissors", "Right Hand + OK"]
]

ESP_ID = "172.20.10.4" #change if hotspot ip changes

def print_results(eeg_pred, eeg_data, eeg_confidence, eeg_rev_label, try_count,
                      emg_pred, emg_data, emg_confidence, emg_rev_label):
    print(f"\nHad to retry model {try_count} times until both were correct.")
    print_model_result(eeg_pred, eeg_data, eeg_confidence, eeg_rev_label, "eeg")
    print_model_result(emg_pred, emg_data, emg_confidence, emg_rev_label, "emg")

def print_model_result(prediction, input_data, confidence, label_map, type: str):
    print(f"\n{type.upper()} results:")
    print(f"Input Signal Source: Random '{input_data}' sample from dataset")
    print(f"Model Prediction:    {label_map[prediction].upper()}")
    print(f"Confidence:          {confidence:.2f}%")
    
    if label_map[prediction] == input_data:
        print("Result:              CORRECT")
    else:
        print("Result:              INCORRECT")

def models_correct(eeg_pred, eeg_correct, emg_pred, emg_correct):
    if eeg_pred == eeg_correct and emg_pred == emg_correct:
        return True
    return False

def send_to_car(packet_to_send):
    max_tries = 3
    sent = False
    for i in range(max_tries):
        print(f"Sending command attempt #{i+1}")
        sent = send_motor_direction_packet(ESP_ID, bytes(packet_to_send))
        if sent:
            break

def main():
    # load EMG Model and data
    X_emg, y_emg = load_emg_data()
    emg_model = load_emg_model()
    
    #load EEG model and data
    X_eeg, y_eeg = load_eeg_data()
    eeg_model, X_eeg, y_eeg = train_eeg_model(X_eeg, y_eeg)
    
    # get label mappings
    emg_label, emg_rev_label = get_emg_maps()
    eeg_label, eeg_rev_label = get_eeg_maps()

    print(f"Paired with ESP at {ESP_ID}")
    
    print("\nThink of left or right hand...")
    print("Then choose rock, paper, or scissors...")

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
        
        # for demo's sake, requery model until correct. This is a limitation in our design
        try_count = 0
        while (not models_correct(eeg_pred, eeg_label[eeg_data], emg_pred, emg_label[emg_data])):
            try_count += 1
            emg_pred, emg_confidence = get_emg_prediction(emg_model, X_emg, y_emg, emg_data)
            eeg_pred, eeg_confidence = get_eeg_prediction(eeg_model, X_eeg, y_eeg, eeg_data)

        print_results(eeg_pred, eeg_data, eeg_confidence, eeg_rev_label, try_count,
                      emg_pred, emg_data, emg_confidence, emg_rev_label)
        
        packet_to_send = [int(eeg_pred), int(emg_pred)]
        print(f"\npacket_to_send list: {packet_to_send}")
        print(f"packet_to_send bytes: {bytes(packet_to_send)}\n")

        # send result to car
        sent = send_to_car(packet_to_send)

        if sent:
            print(f"Instructions sent to car: {CONTROLS[eeg_pred][emg_pred]}\n")
        else:
            print("Instructions failed to send.\n")
        
        print("Next move!")

if __name__ == "__main__":
    main()