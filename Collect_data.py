# Modified Data Collection System with Auto-Completion Detection

from flask import Flask, render_template_string, request
import csv
import time
import hashlib
import random

app = Flask(__name__)

# Configuration
TARGET_PHRASE = "The quick brown fox jumps over the lazy dog"  # Standard typing test sentence
INACTIVITY_TIMEOUT = 5  # Seconds of inactivity to consider typing finished

# Session storage
typing_sessions = {}

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<body>
    <h2>Type this text:</h2>
    <p id="targetPhrase" style="font-family: monospace">{{ target_phrase }}</p>
    <textarea id="userInput" rows="4" cols="50" style="font-family: monospace" 
              onkeyup="checkCompletion()"></textarea>
    <p id="message"></p>

    <script>
        let lastKeyTime = Date.now();
        let keyData = [];
        const targetPhrase = `{{ target_phrase }}`;

        function logKey(e) {
            const now = Date.now();

            // Log dwell time
            if(e.type === 'keydown' && !e.repeat) {
                keyData.push({
                    key: e.key,
                    action: 'press',
                    timestamp: now
                });
            }

            if(e.type === 'keyup') {
                keyData.push({
                    key: e.key,
                    action: 'release',
                    timestamp: now
                });
            }

            lastKeyTime = now;
        }

        function checkCompletion() {
            const userInput = document.getElementById('userInput').value;

            // Exact match check
            if(userInput === targetPhrase) {
                document.getElementById('message').innerHTML = "✅ Perfect match! Saving data...";
                submitData();
                document.getElementById('userInput').readOnly = true;
            }
        }

        // Submit data automatically when typing stops
        setInterval(() => {
            if((Date.now() - lastKeyTime) > ({{ inactivity_timeout }} * 1000) && keyData.length > 0) {
                document.getElementById('message').innerHTML = "⏳ Saving your progress...";
                submitData();
            }
        }, 1000);

        function submitData() {
            fetch('/submit', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    key_events: keyData,
                    final_text: document.getElementById('userInput').value
                })
            }).then(() => {
                keyData = [];
                document.getElementById('message').innerHTML += " Data saved!";
            });
        }

        // Event listeners
        document.getElementById('userInput').addEventListener('keydown', logKey);
        document.getElementById('userInput').addEventListener('keyup', logKey);
    </script>
</body>
</html>
'''


@app.route('/')
def index():
    session_id = hashlib.sha256(str(time.time()).encode()).hexdigest()
    typing_sessions[session_id] = {
        'start_time': time.time(),
        'key_events': []
    }
    return render_template_string(
        HTML_TEMPLATE,
        target_phrase=TARGET_PHRASE,
        inactivity_timeout=INACTIVITY_TIMEOUT
    )


@app.route('/submit', methods=['POST'])
def submit_data():
    data = request.json
    user_input = data['final_text']

    # Calculate features only if user completed the phrase
    if user_input == TARGET_PHRASE:
        dwell_times, flight_times = process_events(data['key_events'])

        # Save to CSV
        with open('typing_data.csv', 'a') as f:
            writer = csv.writer(f)
            writer.writerow([
                time.time(),
                np.mean(dwell_times),
                np.std(dwell_times),
                np.mean(flight_times),
                np.std(flight_times),
                len(user_input),
                user_input == TARGET_PHRASE  # Accuracy flag
            ])

    return jsonify({'status': 'success'})


def process_events(events):
    dwell_times = []
    flight_times = []
    press_times = {}

    for event in events:
        if event['action'] == 'press':
            press_times[event['key']] = event['timestamp']
        elif event['action'] == 'release':
            if event['key'] in press_times:
                dwell_times.append(event['timestamp'] - press_times[event['key']])

    # Calculate flight times between consecutive presses
    presses = [e for e in events if e['action'] == 'press']
    for i in range(1, len(presses)):
        flight_times.append(presses[i]['timestamp'] - presses[i - 1]['timestamp'])

    return dwell_times, flight_times


if __name__ == '__main__':
    app.run()