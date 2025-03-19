from flask import Flask, request, jsonify
import os
import datetime
import pygame
from flask_cors import CORS
import threading
import time

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Setup storage directory
UPLOAD_FOLDER = 'security_images'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Alarm state
alarm_active = False
alarm_thread = None

def play_alarm_sound():
    global alarm_active
    
    pygame.mixer.init()
    pygame.mixer.music.load('alarm.mp3')  # Make sure to have an alarm.mp3 file in your server directory
    
    while alarm_active:
        if not pygame.mixer.music.get_busy():
            pygame.mixer.music.play()
        time.sleep(0.1)
    
    pygame.mixer.music.stop()

@app.route('/ping', methods=['GET'])
def ping():
    return jsonify({'status': 'ok', 'message': 'Server is running'})

@app.route('/alert', methods=['POST'])
def receive_alert():
    global alarm_active, alarm_thread
    
    data = request.json
    timestamp = data.get('timestamp', datetime.datetime.now().isoformat())
    
    # Log the alert
    with open('alerts.log', 'a') as log_file:
        log_file.write(f"Alert received at {timestamp}\n")
    
    # Start the alarm if not already running
    if not alarm_active:
        alarm_active = True
        alarm_thread = threading.Thread(target=play_alarm_sound)
        alarm_thread.start()
    
    return jsonify({
        'status': 'ok',
        'message': 'Alert received and alarm triggered',
        'timestamp': timestamp
    })

@app.route('/upload-photo', methods=['POST'])
def upload_photo():
    if 'photo' not in request.files:
        return jsonify({'status': 'error', 'message': 'No photo part'})
    
    photo = request.files['photo']
    timestamp = request.form.get('timestamp', datetime.datetime.now().isoformat())
    
    if photo.filename == '':
        return jsonify({'status': 'error', 'message': 'No selected file'})
    
    # Create a filename with timestamp
    timestamp_str = timestamp.replace(':', '-').replace('.', '-')
    filename = f"intruder_{timestamp_str}.jpg"
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    
    # Save the file
    photo.save(file_path)
    
    return jsonify({
        'status': 'ok',
        'message': 'Photo uploaded successfully',
        'filename': filename,
        'path': file_path
    })

@app.route('/stop-alarm', methods=['POST'])
def stop_alarm():
    global alarm_active
    
    alarm_active = False
    
    return jsonify({
        'status': 'ok',
        'message': 'Alarm stopped'
    })

@app.route('/images', methods=['GET'])
def list_images():
    images = []
    for filename in os.listdir(UPLOAD_FOLDER):
        if filename.endswith('.jpg') or filename.endswith('.jpeg'):
            images.append({
                'filename': filename,
                'path': os.path.join(UPLOAD_FOLDER, filename),
                'timestamp': filename.split('_')[1].split('.')[0]
            })
    
    return jsonify({
        'status': 'ok',
        'images': images
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)