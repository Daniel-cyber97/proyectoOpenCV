import cv2
import numpy as np

class VideoProcessor:
    """Clase para procesar frames de video con OpenCV"""
    
    def __init__(self):
        """Inicializar el procesador de video"""
        # Diccionario con nombre de efecto y su descripción
        self.effects = {
            'normal': 'Visualización normal sin efectos aplicados',
            'Escala Grises': 'Convierte el video a escala de grises',
            'Detector Bordes': 'Detección de bordes con algoritmo Canny',
            'Desenfoque': 'Desenfoque gaussiano para suavizar la imagen',
            'invertir': 'Invierte todos los colores del video',
            'Efecto Dibujo': 'Efecto de dibujo a lápiz',
            'Blanco y Negro': 'Umbral binario (blanco y negro)',
            'Tono sepia': 'Efecto vintage de tono sepia',
            'cartoon': 'Efecto de caricatura o cómic',
            'Detector Rostro': 'Detección de rostros con recuadros',
            'Detector Movimiento': 'Detección de movimiento'
        }
        
        # Para efectos que requieren estado entre frames
        self.prev_frame = None
        self.background_subtractor = cv2.createBackgroundSubtractorMOG2(history=500, varThreshold=16, detectShadows=True)
        
        # Cargar clasificador para detección facial
        try:
            self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        except Exception as e:
            print(f"Error al cargar clasificador facial: {e}")
            self.face_cascade = None
    
    def get_available_effects(self):
        """Devuelve la lista de efectos disponibles con sus descripciones"""
        return self.effects
    
    def process_frame(self, frame, effect):
        """
        Procesa un frame de video con el efecto especificado
        
        Args:
            frame: Frame de video en formato NumPy array
            effect: Nombre del efecto a aplicar
            
        Returns:
            Frame procesado
        """
        # Aplicar el efecto seleccionado
        if effect == 'normal':
            return frame
        
        elif effect == 'Escala Grises':
            return cv2.cvtColor(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY), cv2.COLOR_GRAY2BGR)
        
        elif effect == 'Detector Bordes':
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, 100, 200)
            return cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
        
        elif effect == 'Desenfoque':
            return cv2.GaussianBlur(frame, (21, 21), 0)
        
        elif effect == 'invertir':
            return cv2.bitwise_not(frame)
        
        elif effect == 'Efecto Dibujo':
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            blur = cv2.GaussianBlur(gray, (5, 5), 0)
            edges = cv2.Canny(blur, 10, 70)
            ret, mask = cv2.threshold(edges, 70, 255, cv2.THRESH_BINARY_INV)
            return cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
            
        elif effect == 'Blanco y Negro':
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            _, thresh = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
            return cv2.cvtColor(thresh, cv2.COLOR_GRAY2BGR)
            
        elif effect == 'Tono sepia':
            # Efecto sepia (tono marrón vintage)
            kernel = np.array([[0.272, 0.534, 0.131],
                               [0.349, 0.686, 0.168],
                               [0.393, 0.769, 0.189]])
            return cv2.transform(frame, kernel)
            
        elif effect == 'cartoon':
            # 1. Convertimos a escala de grises
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            # 2. Aplicamos un desenfoque mediano para suavizar la imagen
            gray_blur = cv2.medianBlur(gray, 7)

            # 3. Detectamos bordes con umbral adaptativo
            edges = cv2.adaptiveThreshold(
                gray_blur, 255,
                cv2.ADAPTIVE_THRESH_MEAN_C,
                cv2.THRESH_BINARY,
                blockSize=9,
                C=2
            )

            # 4. Suavizamos la imagen de color con múltiples filtros bilaterales
            color = frame
            for _ in range(2):  # aplicar 2 veces para suavizar más sin perder bordes
                color = cv2.bilateralFilter(color, d=9, sigmaColor=150, sigmaSpace=150)

            # 5. Combinamos la imagen suavizada con los bordes
            cartoon = cv2.bitwise_and(color, color, mask=edges)

            # 6. Opcional: aplicar un leve aumento de contraste
            cartoon = cv2.convertScaleAbs(cartoon, alpha=1.2, beta=10)

            return cartoon

            
        elif effect == 'Detector Rostro' and self.face_cascade is not None:
            # Detección de rostros
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            # Detectar rostros en la imagen
            faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)
            # Dibujar rectángulos alrededor de los rostros
            frame_copy = frame.copy()
            for (x, y, w, h) in faces:
                cv2.rectangle(frame_copy, (x, y), (x+w, y+h), (255, 0, 0), 2)
            return frame_copy
            
        elif effect == 'Detector Movimiento':
            # Detección de movimiento
            # Aplicar sustractor de fondo
            fg_mask = self.background_subtractor.apply(frame)
            
            # Aplicar umbral para eliminar sombras
            _, thresh = cv2.threshold(fg_mask, 200, 255, cv2.THRESH_BINARY)
            
            # Operaciones morfológicas para eliminar ruido
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
            thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
            thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
            
            # Encontrar contornos
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Dibujar contornos de movimiento
            frame_copy = frame.copy()
            for contour in contours:
                if cv2.contourArea(contour) > 500:  # Filtrar contornos pequeños
                    (x, y, w, h) = cv2.boundingRect(contour)
                    cv2.rectangle(frame_copy, (x, y), (x+w, y+h), (0, 255, 0), 2)
            
            return frame_copy
        
        # Si el efecto no existe o no está implementado, devuelve el frame original
        return frame