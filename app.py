import numpy as np
import sounddevice as sd
import time
import pyttsx3
import random
import threading
from flask import Flask, jsonify, Response

app = Flask(__name__)

fs = 44100
duration = 1  # seconds
chirp_freq = 18000
objects = ["a wall", "a chair", "a table", "a person", "a book", "a window", "a door"]

def speak(message):
    def _speak():
        try:
            engine = pyttsx3.init()
            engine.say(message)
            engine.runAndWait()
        except Exception as e:
            print("Speech error:", e)
    threading.Thread(target=_speak, daemon=True).start()

def emit_chirp():
    t = np.linspace(0, duration, int(fs * duration), endpoint=False)
    chirp = 0.5 * np.sin(2 * np.pi * chirp_freq * t)
    sd.play(chirp, fs)
    sd.wait()

def listen_for_echo():
    recording = sd.rec(int(0.1 * fs), samplerate=fs, channels=1, dtype='float64')
    sd.wait()
    return recording

def calculate_distance(echo_time):
    return (echo_time * 34300) / 2  # cm

def simulate_object():
    obj = random.choice(objects)
    dist = random.uniform(50, 300)
    return obj, dist

@app.route('/')
def index():
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>EchoNav</title>
        <meta charset="UTF-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        <style>
            body {
                font-family: sans-serif;
                background: #101820;
                color: white;
                text-align: center;
                padding: 80px 20px;
            }
            button {
                background: #3498db;
                border: none;
                padding: 12px 24px;
                font-size: 18px;
                color: white;
                border-radius: 8px;
                cursor: pointer;
            }
            #result {
                margin-top: 30px;
                font-size: 20px;
                color: #4cc3ff;
            }
        </style>
    </head>
    <body>
        <h1>🔊 EchoNav Demo</h1>
        <p>Navigate with sound: Chirp + echo + voice feedback</p>
        <button onclick="startDemo()">Request Demo</button>
        <div id="result"></div>

        <script>
            async function startDemo() {
                const resDiv = document.getElementById("result");
                resDiv.innerText = "🔍 Listening...";
                try {
                    const res = await fetch("/echolocation");
                    const data = await res.json();
                    resDiv.innerText = "✅ " + data.message;
                    window.speechSynthesis.cancel();
                    const msg = new SpeechSynthesisUtterance(data.message);
                    msg.lang = "en-US";
                    msg.rate = 1;
                    window.speechSynthesis.speak(msg);
                } catch (e) {
                    resDiv.innerText = "❌ Error reaching echolocation service.";
                }
            }
        </script>
    </body>
    </html>
    """
    return Response(html, mimetype='text/html')

@app.route('/echolocation')
def echolocation():
    try:
        emit_chirp()
        start = time.time()
        recording = listen_for_echo()
        end = time.time()

        amplitude = np.max(np.abs(recording))
        if amplitude > 0.01:
            echo_time = end - start
            distance = calculate_distance(echo_time)
            obj = "an object"
            mode = "Real echo"
        else:
            obj, distance = simulate_object()
            mode = "Simulated echo"

        message = f"{mode}: Detected {obj} approximately {distance:.2f} cm away."
        speak(f"Detected {obj} approximately {distance:.2f} centimeters away.")
        return jsonify({
            "object": obj,
            "distance": f"{distance:.2f}",
            "message": message
        })

    except Exception as e:
        print("Error:", e)
        return jsonify({
            "object": "error",
            "distance": "0",
            "message": "Echolocation failed due to an error."
        }), 500

if __name__ == '__main__':
    app.run(debug=True)
