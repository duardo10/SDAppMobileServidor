from flask import Flask, request, jsonify, send_from_directory
import os
import datetime
import pygame
from flask_cors import CORS
import threading
import time
import logging

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})  # CORS mais permissivo para testes

# Setup storage directory
UPLOAD_FOLDER = 'security_images'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Alarm state
alarm_active = False
alarm_thread = None

def play_alarm_sound():
    global alarm_active
    
    try:
        pygame.mixer.init()
        # Verificar se o arquivo existe
        alarm_file = 'alarm.mp3'
        if not os.path.exists(alarm_file):
            logger.error(f"Arquivo de alarme '{alarm_file}' não encontrado!")
            return
            
        pygame.mixer.music.load(alarm_file)
        
        while alarm_active:
            if not pygame.mixer.music.get_busy():
                pygame.mixer.music.play()
            time.sleep(0.1)
            
        pygame.mixer.music.stop()
    except Exception as e:
        logger.error(f"Erro ao reproduzir som: {str(e)}")

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        'status': 'ok',
        'message': 'Security System Server',
        'endpoints': {
            'ping': '/ping [GET]',
            'alert': '/alert [POST]',
            'upload': '/upload-photo [POST]',
            'stop_alarm': '/stop-alarm [POST]',
            'images': '/images [GET]',
            'view_image': '/image/<filename> [GET]'
        }
    })

@app.route('/ping', methods=['GET'])
def ping():
    logger.info("Recebido ping")
    return jsonify({'status': 'ok', 'message': 'Server is running'})

@app.route('/alert', methods=['POST'])
def receive_alert():
    global alarm_active, alarm_thread
    
    logger.info("Alerta recebido")
    
    try:
        data = request.get_json()
        if data is None:
            data = {}
        timestamp = data.get('timestamp', datetime.datetime.now().isoformat())
        
        # Log the alert
        with open('alerts.log', 'a') as log_file:
            log_file.write(f"Alert received at {timestamp}\n")
        
        # Start the alarm if not already running
        if not alarm_active:
            alarm_active = True
            alarm_thread = threading.Thread(target=play_alarm_sound)
            alarm_thread.daemon = True  # Thread não bloqueia ao encerrar o programa
            alarm_thread.start()
        
        return jsonify({
            'status': 'ok',
            'message': 'Alert received and alarm triggered',
            'timestamp': timestamp
        })
    except Exception as e:
        logger.error(f"Erro ao processar alerta: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/upload-photo', methods=['POST'])
def upload_photo():
    logger.info("Upload de foto recebido")
    
    try:
        if 'photo' not in request.files:
            return jsonify({'status': 'error', 'message': 'No photo part'}), 400
        
        photo = request.files['photo']
        timestamp = request.form.get('timestamp', datetime.datetime.now().isoformat())
        
        if photo.filename == '':
            return jsonify({'status': 'error', 'message': 'No selected file'}), 400
        
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
    except Exception as e:
        logger.error(f"Erro ao fazer upload da foto: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/stop-alarm', methods=['POST'])
def stop_alarm():
    global alarm_active
    
    logger.info("Solicitação para parar o alarme")
    alarm_active = False
    
    return jsonify({
        'status': 'ok',
        'message': 'Alarm stopped'
    })

@app.route('/images', methods=['GET'])
def list_images():
    try:
        images = []
        for filename in os.listdir(UPLOAD_FOLDER):
            if filename.endswith('.jpg') or filename.endswith('.jpeg'):
                images.append({
                    'filename': filename,
                    'url': f'/image/{filename}',
                    'timestamp': filename.split('_')[1].split('.')[0] if '_' in filename else 'unknown'
                })
        
        return jsonify({
            'status': 'ok',
            'images': images
        })
    except Exception as e:
        logger.error(f"Erro ao listar imagens: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/image/<filename>', methods=['GET'])
def get_image(filename):
    """Endpoint para acessar imagens salvas"""
    return send_from_directory(UPLOAD_FOLDER, filename)

if __name__ == '__main__':
    # Verificar se o arquivo de alarme existe antes de iniciar
    if not os.path.exists('alarm.mp3'):
        logger.warning("Arquivo alarm.mp3 não encontrado. O alarme não irá tocar!")
    
    logger.info("Iniciando servidor de segurança na porta 5000...")
    app.run(host='0.0.0.0', port=5000, debug=True)