from flask import Flask, request, jsonify, send_from_directory
import os
import datetime
import pygame
from flask_cors import CORS
import threading
import time
import logging
import json

# Configuração de logging mais detalhada
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("security_server.log"),
        logging.StreamHandler()
    ]
)
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
        logger.info("Iniciando reprodução do alarme")
        pygame.mixer.init()
        # Verificar se o arquivo existe
        alarm_file = 'alarm.mp3'
        if not os.path.exists(alarm_file):
            logger.error(f"Arquivo de alarme '{alarm_file}' não encontrado!")
            return
            
        logger.debug(f"Carregando arquivo de alarme: {alarm_file}")
        pygame.mixer.music.load(alarm_file)
        
        while alarm_active:
            if not pygame.mixer.music.get_busy():
                logger.debug("Reiniciando reprodução do alarme")
                pygame.mixer.music.play()
            time.sleep(0.1)
            
        logger.info("Parando reprodução do alarme")
        pygame.mixer.music.stop()
    except Exception as e:
        logger.error(f"Erro ao reproduzir som: {str(e)}")

@app.route('/', methods=['GET'])
def home():
    logger.info("Página inicial acessada")
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
    logger.info("Recebido ping de teste de conexão")
    return jsonify({'status': 'ok', 'message': 'Server is running'})

@app.route('/alert', methods=['POST'])
def receive_alert():
    global alarm_active, alarm_thread
    
    logger.info("Alerta recebido")
    
    try:
        # Log detalhado dos headers da requisição
        headers = dict(request.headers)
        logger.debug(f"Headers da requisição de alerta: {json.dumps(headers, indent=2)}")
        
        # Log do corpo da requisição
        try:
            data = request.get_json()
            logger.debug(f"Corpo da requisição de alerta: {json.dumps(data, indent=2) if data else 'Nenhum'}")
        except Exception as e:
            logger.warning(f"Erro ao parsear JSON do corpo da requisição: {str(e)}")
            data = {}
        
        if data is None:
            data = {}
        
        # Tratar possíveis valores ausentes
        timestamp = data.get('timestamp', datetime.datetime.now().isoformat())
        sensor_data = data.get('sensorData', {})
        
        # Log the alert
        with open('alerts.log', 'a') as log_file:
            log_file.write(f"Alert received at {timestamp} with data: {json.dumps(data)}\n")
        
        # Start the alarm if not already running
        if not alarm_active:
            logger.info("Ativando alarme")
            alarm_active = True
            alarm_thread = threading.Thread(target=play_alarm_sound)
            alarm_thread.daemon = True  # Thread não bloqueia ao encerrar o programa
            alarm_thread.start()
            logger.debug("Thread do alarme iniciada")
        else:
            logger.info("Alarme já está ativo, ignorando ativação")
        
        return jsonify({
            'status': 'ok',
            'message': 'Alert received and alarm triggered',
            'timestamp': timestamp
        })
    except Exception as e:
        logger.error(f"Erro ao processar alerta: {str(e)}", exc_info=True)
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/upload-photo', methods=['POST'])
def upload_photo():
    logger.info("Upload de foto recebido")
    
    try:
        # Log detalhado dos headers da requisição
        headers = dict(request.headers)
        logger.debug(f"Headers da requisição de upload: {json.dumps(headers, indent=2)}")
        
        # Log dos campos do formulário
        form_data = dict(request.form)
        logger.debug(f"Campos do formulário: {json.dumps(form_data, indent=2)}")
        
        # Log dos arquivos enviados
        files = dict([(key, value.filename) for key, value in request.files.items()])
        logger.debug(f"Arquivos enviados: {json.dumps(files, indent=2)}")
        
        if 'photo' not in request.files:
            logger.warning("Nenhuma foto encontrada na requisição")
            return jsonify({'status': 'error', 'message': 'No photo part'}), 400
        
        photo = request.files['photo']
        timestamp = request.form.get('timestamp', datetime.datetime.now().isoformat())
        
        if photo.filename == '':
            logger.warning("Nome de arquivo vazio")
            return jsonify({'status': 'error', 'message': 'No selected file'}), 400
        
        # Create a filename with timestamp
        timestamp_str = timestamp.replace(':', '-').replace('.', '-')
        filename = f"intruder_{timestamp_str}.jpg"
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        
        # Save the file
        logger.debug(f"Salvando arquivo em: {file_path}")
        photo.save(file_path)
        logger.info(f"Foto salva com sucesso: {filename}")
        
        return jsonify({
            'status': 'ok',
            'message': 'Photo uploaded successfully',
            'filename': filename,
            'path': file_path
        })
    except Exception as e:
        logger.error(f"Erro ao fazer upload da foto: {str(e)}", exc_info=True)
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/stop-alarm', methods=['POST'])
def stop_alarm():
    global alarm_active
    
    logger.info("Solicitação para parar o alarme")
    alarm_active = False
    
    # Aguardar a thread do alarme finalizar
    if alarm_thread and alarm_thread.is_alive():
        logger.debug("Aguardando a thread do alarme finalizar")
        alarm_thread.join(timeout=2.0)  # Espera no máximo 2 segundos
    
    # Garantir que a música foi parada
    try:
        if pygame.mixer.get_init() and pygame.mixer.music.get_busy():
            pygame.mixer.music.stop()
            logger.debug("Pygame mixer parado diretamente")
    except Exception as e:
        logger.error(f"Erro ao tentar parar música diretamente: {str(e)}")
    
    return jsonify({
        'status': 'ok',
        'message': 'Alarm stopped'
    })

@app.route('/get-alarm-status', methods=['GET'])
def get_alarm_status():
    """Retorna o status atual do alarme"""
    logger.debug(f"Consultando status do alarme: {alarm_active}")
    return jsonify({
        'status': 'ok',
        'alarm_active': alarm_active
    })

@app.route('/images', methods=['GET'])
def list_images():
    logger.info("Solicitação para listar imagens")
    try:
        images = []
        for filename in os.listdir(UPLOAD_FOLDER):
            if filename.endswith('.jpg') or filename.endswith('.jpeg'):
                images.append({
                    'filename': filename,
                    'url': f'/image/{filename}',
                    'timestamp': filename.split('_')[1].split('.')[0] if '_' in filename else 'unknown'
                })
        
        logger.debug(f"Encontradas {len(images)} imagens")
        return jsonify({
            'status': 'ok',
            'images': images
        })
    except Exception as e:
        logger.error(f"Erro ao listar imagens: {str(e)}", exc_info=True)
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/image/<filename>', methods=['GET'])
def get_image(filename):
    """Endpoint para acessar imagens salvas"""
    logger.debug(f"Solicitação para acessar imagem: {filename}")
    return send_from_directory(UPLOAD_FOLDER, filename)

if __name__ == '__main__':
    # Verificar se o arquivo de alarme existe antes de iniciar
    if not os.path.exists('alarm.mp3'):
        logger.warning("Arquivo alarm.mp3 não encontrado. O alarme não irá tocar!")
    
    logger.info("Iniciando servidor de segurança na porta 5000...")
    app.run(host='0.0.0.0', port=5000, debug=True)