# Video Text Remover Pro

Herramienta en Python para eliminar texto o marcas de agua de videos usando aceleración por GPU NVIDIA.

## Historia del Proyecto

Este proyecto evolucionó a través de cuatro versiones principales:

**Versión 1.0 (OpenCV básico)**
Se utilizó OpenCV con cv2.inpaint() para rellenar la zona seleccionada y cv2.selectROI() para la interacción. Funcionaba, pero era muy lento: procesar 1 hora de video tomaba entre 1.5 y 3 horas al ejecutarse exclusivamente en la CPU.

**Versión 2.0 (Multiprocessing)**
Se intentó acelerar el proceso dividiendo el video en bloques y procesándolos en paralelo con ProcessPoolExecutor. La mejora fue mínima porque el costo de serializar los frames entre procesos consumía la ganancia de velocidad.

**Versión 3.0 (FFmpeg + NVENC)**
Se reemplazó el procesamiento frame por frame en Python por FFmpeg. Se usó el filtro delogo para eliminar el texto y el codec h264_nvenc para codificar el video directamente en la GPU NVIDIA. El resultado fue drástico: 1 hora de video pasó de tardar horas a tardar entre 5 y 6 minutos (aproximadamente 10-12 veces más rápido).

**Versión 4.0 (Actual - Profesional)**
Se pulió la experiencia de usuario y la estabilidad. Se corrigió el bug de pantalla blanca en Windows al seleccionar zonas, se agregó un modo de prueba de 30 segundos, tres niveles de calidad configurables, barra de progreso con tiempo estimado, validación automática de FFmpeg y conservación automática del audio original.

## Características

- Selección visual de la zona a eliminar con el mouse
- Aceleración nativa por GPU NVIDIA (NVENC)
- Soporte completo para videos a 60 fps
- Conserva el audio original sin recodificar
- Modo de prueba de 30 segundos antes del procesamiento completo
- Progreso en tiempo real con velocidad y tiempo restante
- Validaciones de entrada y manejo seguro de errores

## Requisitos

Hardware:
- GPU NVIDIA con soporte NVENC (GTX 10-series o superior)
- 8 GB de RAM (16 GB recomendado)
- Espacio en disco libre equivalente al menos al doble del tamaño del video

Software:
- Python 3.10 o superior
- FFmpeg con soporte NVENC compilado
- Paquetes de Python: opencv-python, numpy

## Instalación

1. Clona el repositorio:
   git clone https://github.com/tu-usuario/video-text-remover.git
   cd video-text-remover

2. Instala las dependencias de Python:
   pip install opencv-python numpy

3. Instala FFmpeg en Windows:
   - Recomendado (PowerShell como administrador):
     winget install Gyan.FFmpeg
     (Luego reinicia la terminal para actualizar el PATH)
   - Manual:
     Descarga desde https://www.gyan.dev/ffmpeg/builds/
     Extrae en C:\ffmpeg
     Agrega C:\ffmpeg\bin a la variable de entorno PATH del sistema

## Uso

1. Ejecuta el script:
   python borrar_texto_pro.py

2. Selecciona tu video desde la ventana que se abrirá.

3. Indica en qué segundo del video quieres ver el frame para seleccionar la zona (por defecto se sugiere la mitad del video).

4. Dibuja un rectángulo sobre el texto a eliminar:
   - Tecla C: Confirmar
   - Tecla R: Rehacer
   - Tecla ESC: Cancelar

5. Elige el nivel de calidad:
   - 1: Rápido (mayor velocidad, calidad estándar)
   - 2: Balanceado (recomendado)
   - 3: Calidad (menor velocidad, mejor resultado)

6. Se te preguntará si deseas ejecutar una prueba de 30 segundos. Se recomienda hacerlo para verificar que la zona seleccionada es correcta antes de procesar todo el video.

7. El procesamiento comenzará mostrando el progreso en consola. Al finalizar, el video se guardará con el sufijo _sin_texto.mp4.

## Parámetros Técnicos

El proceso utiliza dos componentes principales de FFmpeg:

Filtro delogo:
-vf delogo=x=POS_X:y=POS_Y:w=ANCHO:h=ALTO:show=0
x e y definen la esquina superior izquierda. w y h definen el tamaño del rectángulo. show=0 oculta el área de debug.

Codificador NVENC:
-c:v h264_nvenc -preset p5 -rc vbr -cq 20
preset controla la relación velocidad/calidad (p1 a p7, p5 es balanceado). rc vbr usa bitrate variable para mantener calidad constante. cq define el nivel de calidad (15 a 51, valores más bajos son mejor calidad).

## Rendimiento Esperado

En una GPU NVIDIA RTX 5060 Ti:
- 1080p a 60 fps (1 hora): 5 a 6 minutos
- 1440p a 60 fps (30 min): 3 a 4 minutos
- 720p a 30 fps (45 min): 3 a 4 minutos

Los tiempos pueden variar según la complejidad visual del video y el tamaño de la zona seleccionada.

## Solución de Problemas

Error: FFmpeg no encontrado
Solución: Verifica la instalación ejecutando ffmpeg -version. Si no se reconoce, reinicia la terminal o agrega la ruta de FFmpeg al PATH del sistema.

Error: NVENC no soportado
Solución: La versión de FFmpeg instalada no incluye codificación NVIDIA. Descarga una build oficial desde gyan.dev que incluya --enable-nvenc.

Ventana blanca al seleccionar zona
Solución: El script ya incluye correcciones para pantallas de alta densidad en Windows. Si persiste, ejecuta el script desde CMD o PowerShell en lugar de un IDE como VS Code.

Bordes visibles después del procesamiento
Solución: Aumenta ligeramente el tamaño del rectángulo seleccionado (añade 5-10 px de margen). También puedes elegir la opción de calidad 3 al ejecutar el script.

Video resultante sin audio
Solución: El script usa -c:a copy para copiar el audio original. Si el codec de audio no es compatible con el contenedor MP4, el audio podría perderse. En ese caso, se requiere recodificar el audio manualmente.

## Alternativas con IA

Si el texto está sobre fondos muy complejos (texturas, paisajes, pelo) y el filtro delogo deja marcas visibles, se recomienda probar herramientas basadas en redes neuronales:

- lama-cleaner: Interfaz web local. Instalación: pip install lama-cleaner. Ejecución: lama-cleaner --model=lama --device=cuda --port=8080. Ventaja: reconstrucción inteligente. Desventaja: 20-30 veces más lento.
- ProPainter: Especializado en video. Requiere configuración avanzada de PyTorch y CUDA. Ventaja: consistencia temporal entre frames. Desventaja: complejo de instalar y muy demandante en VRAM.

## Licencia

Este proyecto está distribuido bajo la licencia MIT. Puedes usarlo, modificarlo y distribuirlo libremente. Consulta el archivo LICENSE para más detalles.
