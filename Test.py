import time
import numpy as np
import tensorflow as tf
from pynput import keyboard
from win10toast import ToastNotifier
import threading
import csv
import os

# Initialize variables
key_timestamps = []
toaster = ToastNotifier()
THRESHOLD = 0.8  # Score below this indicates a different user
DATA_FILE = "typing_data.csv"

# Load the TensorFlow Lite model
interpreter = tf.lite.Interpreter(model_path="model.tflite")
interpreter.allocate_tensors()
input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()


def extract_features(timestamps):
    # Calculate dwell and flight times
    dwell_times = []
    flight_times = []
    for i in range(1, len(timestamps)):
        dwell = (timestamps[i] - timestamps[i - 1]) / 1000  # Convert to seconds
        dwell_times.append(dwell)
        if i > 1:
            flight = (timestamps[i] - timestamps[i - 2]) / 1000
            flight_times.append(flight)

    # Compute statistical features
    features = [
        np.mean(dwell_times) if dwell_times else 0,
        np.std(dwell_times) if dwell_times else 0,
        np.mean(flight_times) if flight_times else 0,
        np.std(flight_times) if flight_times else 0
    ]
    return np.array(features, dtype=np.float32)


def save_data(features, score):
    # Ensure the file exists with headers
    headers = ["dwell_mean", "dwell_std", "flight_mean", "flight_std", "score"]
    file_exists = os.path.isfile(DATA_FILE)

    with open(DATA_FILE, mode='a', newline='') as file:
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow(headers)
        writer.writerow([f"{x:.4f}" for x in features] + [f"{score:.4f}"])


def analyze_typing():
    global key_timestamps
    if len(key_timestamps) < 5:  # Need at least 5 keystrokes for analysis
        return

    # Extract features
    features = extract_features(key_timestamps)

    # Prepare input for TFLite model
    input_data = np.array([features], dtype=np.float32)
    interpreter.set_tensor(input_details[0]['index'], input_data)

    # Run inference
    interpreter.invoke()
    output_data = interpreter.get_tensor(output_details[0]['index'])
    score = output_data[0][0]  # Probability score (0 to 1)

    print(f"Analysis Score: {score:.2f}")

    # Save the data for retraining
    save_data(features, score)

    # Check if the user is different from the owner
    if score < THRESHOLD:
        print("Alert: Different user detected!")
        toaster.show_toast(
            "Typing Behavior Alert",
            "Different user detected! Score: {:.2f}".format(score),
            duration=5,
            threaded=True
        )
    else:
        print("Confirmed: Typing matches the owner.")

    # Reset timestamps for the next window
    key_timestamps = []


def on_press(key):
    global key_timestamps
    try:
        # Record the timestamp of the key press
        key_timestamps.append(time.time() * 1000)  # Convert to milliseconds

        # Analyze every 5 keystrokes
        if len(key_timestamps) >= 5:
            threading.Thread(target=analyze_typing).start()
    except Exception as e:
        print(f"Error: {e}")


def on_release(key):
    # Stop the listener if Esc is pressed
    if key == keyboard.Key.esc:
        return False


def main():
    print("Monitoring typing behavior... Press Esc to stop.")
    with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
        listener.join()


if __name__ == "__main__":
    main()