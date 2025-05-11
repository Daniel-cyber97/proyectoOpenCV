document.addEventListener('DOMContentLoaded', function() {
    // Elementos del DOM
    const videoElement = document.getElementById('video-element');
    const processedCanvas = document.getElementById('processed-canvas');
    const ctx = processedCanvas.getContext('2d');
    const startCameraBtn = document.getElementById('start-camera');
    const stopCameraBtn = document.getElementById('stop-camera');
    const toggleProcessingBtn = document.getElementById('toggle-processing');
    const cameraStatus = document.getElementById('camera-status');
    const processingStatus = document.getElementById('processing-status');
    const effectsContainer = document.getElementById('effects-container');
    const effectInfo = document.getElementById('effect-info');
    const fpsCounter = document.getElementById('fps-counter');
    
    // Variables de estado
    let stream = null;
    let isProcessing = false;
    let processingInterval = null;
    let captureCanvas = document.createElement('canvas');
    let captureCtx = captureCanvas.getContext('2d');
    let currentEffect = 'normal';
    let effects = {};
    let lastFrameTime = 0;
    let frameCount = 0;
    let fps = 0;
    let lastFpsUpdate = 0;
    
    // Función para cargar los efectos disponibles desde el servidor
    async function loadEffects() {
        try {
            const response = await fetch('/get_effects');
            if (!response.ok) throw new Error('Error al cargar efectos');
            
            effects = await response.json();
            
            // Crear botones para cada efecto
            Object.entries(effects).forEach(([effect, description]) => {
                const button = document.createElement('button');
                button.classList.add('effect-btn');
                button.setAttribute('data-effect', effect);
                button.textContent = formatEffectName(effect);
                
                if (effect === currentEffect) {
                    button.classList.add('active');
                    effectInfo.textContent = description;
                }
                
                button.addEventListener('click', () => {
                    // Actualizar efecto actual
                    currentEffect = effect;
                    
                    // Actualizar clase activa
                    document.querySelectorAll('.effect-btn').forEach(btn => {
                        btn.classList.remove('active');
                    });
                    button.classList.add('active');
                    
                    // Actualizar descripción
                    effectInfo.textContent = description;
                });
                
                effectsContainer.appendChild(button);
            });
        } catch (error) {
            console.error('Error al cargar efectos:', error);
            effectInfo.textContent = 'Error al cargar efectos. Por favor, recarga la página.';
        }
    }
    
    // Formatear nombre de efecto para mostrar
    function formatEffectName(effect) {
        return effect
            .split('_')
            .map(word => word.charAt(0).toUpperCase() + word.slice(1))
            .join(' ');
    }
    
    // Iniciar cámara
    async function startCamera() {
        cameraStatus.style.display = 'flex';
        
        try {
            const constraints = {
                video: {
                    width: { ideal: 640 },
                    height: { ideal: 480 },
                    facingMode: 'user'
                }
            };
            
            stream = await navigator.mediaDevices.getUserMedia(constraints);
            videoElement.srcObject = stream;
            
            // Esperar a que el video cargue
            await new Promise(resolve => {
                videoElement.onloadedmetadata = () => {
                    resolve();
                };
            });
            
            // Configurar canvas para captura
            captureCanvas.width = videoElement.videoWidth;
            captureCanvas.height = videoElement.videoHeight;
            
            // Configurar canvas para mostrar resultado
            processedCanvas.width = videoElement.videoWidth;
            processedCanvas.height = videoElement.videoHeight;
            
            // Actualizar UI
            cameraStatus.style.display = 'none';
            startCameraBtn.disabled = true;
            stopCameraBtn.disabled = false;
            toggleProcessingBtn.disabled = false;
            
        } catch (error) {
            console.error('Error al acceder a la cámara:', error);
            cameraStatus.innerHTML = `
                <p style="color: var(--error-color)">Error al acceder a la cámara. Asegúrate de dar permiso.</p>
                <button id="retry-camera" class="control-btn" style="margin-top: 15px;">Reintentar</button>
            `;
            
            document.getElementById('retry-camera').addEventListener('click', startCamera);
        }
    }
    
    // Detener cámara
    function stopCamera() {
        if (stream) {
            // Detener procesamiento si está activo
            if (isProcessing) {
                toggleProcessing();
            }
            
            // Detener todas las pistas de video
            stream.getTracks().forEach(track => track.stop());
            videoElement.srcObject = null;
            stream = null;
            
            // Actualizar UI
            startCameraBtn.disabled = false;
            stopCameraBtn.disabled = true;
            toggleProcessingBtn.disabled = true;
        }
    }
    
    // Cambiar estado de procesamiento
    function toggleProcessing() {
        if (!stream) return;
        
        isProcessing = !isProcessing;
        
        if (isProcessing) {
            // Iniciar procesamiento
            processingStatus.style.display = 'none';
            toggleProcessingBtn.textContent = 'Detener Procesamiento';
            startProcessingLoop();
        } else {
            // Detener procesamiento
            clearInterval(processingInterval);
            processingInterval = null;
            toggleProcessingBtn.textContent = 'Iniciar Procesamiento';
            
            // Limpiar canvas
            ctx.clearRect(0, 0, processedCanvas.width, processedCanvas.height);
            processingStatus.style.display = 'flex';
        }
    }
    
    // Procesar frame
    async function processFrame() {
        // Capturar frame del video
        captureCtx.drawImage(videoElement, 0, 0, captureCanvas.width, captureCanvas.height);
        
        // Convertir canvas a base64
        const imageData = captureCanvas.toDataURL('image/jpeg', 0.7);
        
        try {
            // Enviar al servidor para procesamiento
            const response = await fetch('/process_frame', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    image_data: imageData,
                    effect: currentEffect
                }),
            });
            
            if (!response.ok) {
                throw new Error('Error al procesar el frame');
            }
            
            const data = await response.json();
            
            if (data.status === 'success') {
                // Mostrar imagen procesada
                const img = new Image();
                img.onload = function() {
                    ctx.drawImage(img, 0, 0, processedCanvas.width, processedCanvas.height);
                    
                    // Calcular FPS
                    const now = performance.now();
                    frameCount++;
                    
                    // Actualizar contador de FPS cada segundo
                    if (now - lastFpsUpdate >= 1000) {
                        fps = Math.round((frameCount * 1000) / (now - lastFpsUpdate));
                        lastFpsUpdate = now;
                        frameCount = 0;
                        fpsCounter.textContent = fps;
                    }
                    
                    lastFrameTime = now;
                };
                img.src = data.processed_image;
            }
        } catch (error) {
            console.error('Error al procesar frame:', error);
        }
    }
    
    // Iniciar bucle de procesamiento
    function startProcessingLoop() {
        // Inicializar variables para FPS
        frameCount = 0;
        lastFpsUpdate = performance.now();
        
        // Procesar inmediatamente el primer frame
        processFrame();
        
        // Luego establecer un intervalo para los siguientes
        processingInterval = setInterval(() => {
            if (isProcessing) {
                processFrame();
            }
        }, 100); // Ajustar según sea necesario, 100ms = ~10 FPS
    }
    
    // Eventos
    startCameraBtn.addEventListener('click', startCamera);
    stopCameraBtn.addEventListener('click', stopCamera);
    toggleProcessingBtn.addEventListener('click', toggleProcessing);
    
    // Cargar efectos al iniciar
    loadEffects();
    
    // Ajustar tamaño del canvas cuando la ventana cambia de tamaño
    window.addEventListener('resize', function() {
        if (processedCanvas.width) {
            const aspectRatio = processedCanvas.width / processedCanvas.height;
            const width = processedCanvas.clientWidth;
            processedCanvas.height = width / aspectRatio;
        }
    });
});