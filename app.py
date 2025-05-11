import os
import uuid
import base64
import cv2
import numpy as np
from flask import Flask, render_template, request, jsonify
from processor import VideoProcessor

app = Flask(__name__)

# Configuración
PROCESSED_FOLDER = os.path.join('static', 'processed')
os.makedirs(PROCESSED_FOLDER, exist_ok=True)

app.config['PROCESSED_FOLDER'] = PROCESSED_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max

# Crear instancia del procesador de video
processor = VideoProcessor()

@app.route('/')
def index():
    """Página principal"""
    return render_template('index.html')

@app.route('/process_frame', methods=['POST'])
def process_frame():
    """Recibe un frame, lo procesa con OpenCV y devuelve el resultado"""
    data = request.json
    if not data or 'image_data' not in data or 'effect' not in data:
        return jsonify({'error': 'Datos incompletos'}), 400
    
    # Obtener datos de la imagen y el efecto a aplicar
    image_data = data['image_data'].split(",")[1]  # Eliminar prefijo "data:image/jpeg;base64,"
    effect = data['effect']
    
    try:
        # Decodificar la imagen base64
        image_bytes = base64.b64decode(image_data)
        image_array = np.frombuffer(image_bytes, dtype=np.uint8)
        image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
        
        # Procesar la imagen con OpenCV
        processed_image = processor.process_frame(image, effect)
        
        # Codificar la imagen procesada a base64
        _, buffer = cv2.imencode('.jpg', processed_image)
        processed_image_data = base64.b64encode(buffer).decode('utf-8')
        
        return jsonify({
            'status': 'success',
            'processed_image': f"data:image/jpeg;base64,{processed_image_data}"
        })
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/get_effects', methods=['GET'])
def get_effects():
    """Devuelve la lista de efectos disponibles"""
    effects = processor.get_available_effects()
    return jsonify(effects)

if __name__ == '__main__':
    app.run(debug=True)