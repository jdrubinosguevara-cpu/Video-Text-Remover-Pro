import cv2
import numpy as np
import os
import sys
import subprocess
import time
import re
import tkinter as tk
from tkinter import filedialog, messagebox
import ctypes
import shutil

# 🔧 Fix DPI en Windows
if sys.platform == 'win32':
    try: ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except: pass

def seleccionar_archivo(titulo, tipos):
    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)
    ruta = filedialog.askopenfilename(title=titulo, filetypes=tipos)
    root.destroy()
    time.sleep(0.3)
    return ruta

def validar_ffmpeg():
    """Verifica que FFmpeg esté instalado y tenga NVENC"""
    if not shutil.which("ffmpeg"):
        print("❌ FFmpeg no encontrado en el PATH")
        print("📥 Instala con: winget install Gyan.FFmpeg")
        return False
    
    # Verificar soporte NVENC
    result = subprocess.run(['ffmpeg', '-encoders'], capture_output=True, text=True)
    if 'h264_nvenc' not in result.stdout:
        print("⚠️  Tu FFmpeg no tiene soporte NVENC")
        print("💡 Descarga la versión completa desde: https://www.gyan.dev/ffmpeg/builds/")
        return False
    
    print("✅ FFmpeg con NVENC detectado correctamente")
    return True

def obtener_info_video(video_path):
    """Obtiene duración, fps, resolución y codec de audio"""
    cmd = [
        'ffprobe', '-v', 'error',
        '-select_streams', 'v:0',
        '-show_entries', 'stream=width,height,r_frame_rate,duration',
        '-of', 'csv=p=0',
        video_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    parts = result.stdout.strip().split(',')
    
    cmd_audio = [
        'ffprobe', '-v', 'error',
        '-select_streams', 'a:0',
        '-show_entries', 'stream=codec_name',
        '-of', 'csv=p=0',
        video_path
    ]
    result_audio = subprocess.run(cmd_audio, capture_output=True, text=True)
    audio_codec = result_audio.stdout.strip() or 'none'
    
    if len(parts) >= 4:
        width = int(parts[0])
        height = int(parts[1])
        fps = eval(parts[2])
        duration = float(parts[3]) if parts[3] else 0
        return {'width': width, 'height': height, 'fps': fps, 'duration': duration, 'audio_codec': audio_codec}
    return None

def obtener_frame_en(video_path, segundos=600):
    """Lee un frame en el tiempo especificado"""
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened(): 
        return None
    
    total_frames = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    fps = cap.get(cv2.CAP_PROP_FPS)
    duracion_total = total_frames / fps if fps > 0 else 0
    
    target_sec = min(segundos, duracion_total - 1)
    target_ms = max(1000, target_sec * 1000)
    
    cap.set(cv2.CAP_PROP_POS_MSEC, target_ms)
    ret, frame = cap.read()
    cap.release()
    return frame if ret else None

def seleccionar_roi_estable(frame):
    """Selector de ROI con mejor UX"""
    h, w = frame.shape[:2]
    max_dim = 1280
    scale = min(max_dim / w, max_dim / h, 1.0)
    display = cv2.resize(frame, (int(w*scale), int(h*scale)), interpolation=cv2.INTER_AREA) if scale < 1.0 else frame.copy()

    ref_pt, cropping, roi_final, current_mouse = [], False, None, (0, 0)

    def click_event(event, x, y, flags, param):
        nonlocal ref_pt, cropping, roi_final, current_mouse
        current_mouse = (x, y)
        if event == cv2.EVENT_LBUTTONDOWN:
            ref_pt = [(x, y)]
            cropping = True
        elif event == cv2.EVENT_LBUTTONUP:
            if cropping:
                ref_pt.append((x, y))
                cropping = False
                x1, y1 = int(ref_pt[0][0]/scale), int(ref_pt[0][1]/scale)
                x2, y2 = int(ref_pt[1][0]/scale), int(ref_pt[1][1]/scale)
                roi_final = (min(x1,x2), min(y1,y2), abs(x2-x1), abs(y2-y1))

    cv2.namedWindow("Selecciona zona", cv2.WINDOW_GUI_NORMAL | cv2.WINDOW_KEEPRATIO)
    cv2.resizeWindow("Selecciona zona", display.shape[1], display.shape[0])
    cv2.setMouseCallback("Selecciona zona", click_event)
    cv2.waitKey(1)
    cv2.imshow("Selecciona zona", display)
    cv2.waitKey(80)

    print("\n🖱️  INSTRUCCIONES:")
    print("   • Arrastra un rectángulo sobre el texto")
    print("   • 'C' → Confirmar selección")
    print("   • 'R' → Rehacer selección")
    print("   • 'ESC' → Cancelar\n")

    while True:
        temp = display.copy()
        if len(ref_pt) == 1:
            cv2.rectangle(temp, ref_pt[0], current_mouse, (0, 255, 0), 2)
            cv2.putText(temp, "Arrastra...", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        elif len(ref_pt) == 2:
            cv2.rectangle(temp, ref_pt[0], ref_pt[1], (0, 255, 0), 2)
            cv2.putText(temp, "Presiona 'C' para confirmar", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        cv2.imshow("Selecciona zona", temp)
        key = cv2.waitKey(1) & 0xFF
        if key == ord('c') and roi_final:
            break
        elif key == ord('r'):
            ref_pt = []
            roi_final = None
        elif key == 27:
            roi_final = None
            break

    cv2.destroyAllWindows()
    cv2.waitKey(1)
    return roi_final

def procesar_test(input_path, x, y, w, h, duracion_test=30):
    """Procesa solo los primeros N segundos para probar"""
    base, ext = os.path.splitext(input_path)
    test_output = f"{base}_TEST.mp4"
    
    print(f"\n🧪 Procesando prueba de {duracion_test}s...")
    
    cmd = [
        'ffmpeg', '-y', '-i', input_path, '-t', str(duracion_test),
        '-vf', f'delogo=x={x}:y={y}:w={w}:h={h}:show=0',
        '-c:v', 'h264_nvenc', '-preset', 'p5', '-rc', 'vbr', '-cq', '18',
        '-c:a', 'copy',
        test_output
    ]
    
    subprocess.run(cmd, check=True)
    print(f"✅ Prueba guardada en: {test_output}")
    
    if sys.platform == 'win32':
        os.startfile(test_output)
    
    return input(f"\n¿Te gusta el resultado? (s/n): ").strip().lower() == 's'

def main():
    print("="*60)
    print("🎬 ELIMINAR TEXTO DE VIDEO - VERSIÓN PROFESIONAL")
    print("="*60)
    
    # Validar FFmpeg
    if not validar_ffmpeg():
        return
    
    # Seleccionar video
    input_path = seleccionar_archivo("Selecciona video", 
                                     [("Videos", "*.mp4 *.avi *.mov *.mkv *.webm"), ("Todos", "*.*")])
    if not input_path:
        print("⚠️  Cancelado.")
        return

    # Obtener info del video
    print("\n📊 Analizando video...")
    info = obtener_info_video(input_path)
    if not info:
        print("❌ No se pudo leer la información del video")
        return
    
    print(f"   Resolución: {info['width']}x{info['height']}")
    print(f"   FPS: {info['fps']:.2f}")
    print(f"   Duración: {info['duration']/60:.1f} min")
    print(f"   Audio: {info['audio_codec']}")

    # Preguntar tiempo para frame
    try:
        tiempo_default = min(600, info['duration'] * 0.5)  # 50% del video o 10min
        tiempo_str = input(f"\n⏱️  ¿Segundo del frame para seleccionar? (Default: {int(tiempo_default)}) → ").strip()
        tiempo_sec = int(tiempo_str) if tiempo_str else int(tiempo_default)
    except ValueError:
        tiempo_sec = int(tiempo_default)

    print(f"📥 Cargando frame a los {tiempo_sec}s...")
    frame = obtener_frame_en(input_path, tiempo_sec)
    if frame is None:
        print("❌ No se pudo extraer el frame")
        return

    # Seleccionar ROI
    print("\n" + "="*60)
    roi = seleccionar_roi_estable(frame)
    
    if roi is None:
        print("⚠️  Selección cancelada")
        return

    x, y, w, h = roi
    
    # Validar ROI
    if x < 0 or y < 0 or x+w > info['width'] or y+h > info['height']:
        print(f"⚠️  Advertencia: La zona seleccionada excede los límites del video")
        print(f"   Video: {info['width']}x{info['height']}")
        print(f"   Tu zona: x={x}, y={y}, w={w}, h={h}")
        if not input("¿Continuar de todos modos? (s/n): ").strip().lower() == 's':
            return

    print(f"\n✅ ROI final: x={x}, y={y}, ancho={w}, alto={h}")

    # Preguntar modo de procesamiento
    print("\n🔧 CONFIGURACIÓN:")
    print("   1) Rápido (p4, CQ 22) - ~10-15x velocidad")
    print("   2) Balanceado (p5, CQ 20) - ~5-8x velocidad ← RECOMENDADO")
    print("   3) Calidad (p6, CQ 18) - ~3-5x velocidad")
    
    while True:
        modo = input("\nElige modo (1/2/3) [Default: 2]: ").strip() or '2'
        if modo in ['1', '2', '3']:
            presets = {'1': ('p4', 22), '2': ('p5', 20), '3': ('p6', 18)}
            preset, cq = presets[modo]
            break
        print("Opción inválida")

    # Preguntar si quiere hacer prueba
    hacer_test = input("\n🧪 ¿Procesar prueba de 30s primero? (s/n) [Default: s]: ").strip().lower()
    if hacer_test != 'n':
        if not procesar_test(input_path, x, y, w, h, 30):
            print("❌ Ajusta la selección y vuelve a ejecutar")
            return

    # Configuración final
    base, ext = os.path.splitext(input_path)
    output_path = f"{base}_sin_texto.mp4"

    print("\n" + "="*60)
    print(f"📂 Salida: {os.path.basename(output_path)}")
    print(f"⚙️  Config: preset={preset}, CQ={cq}, band=10")
    print("="*60)

    # Comando FFmpeg optimizado
    ffmpeg_cmd = [
        'ffmpeg', '-y', '-i', input_path,
        '-vf', f'delogo=x={x}:y={y}:w={w}:h={h}:show=0',
        '-c:v', 'h264_nvenc', '-preset', preset, '-rc', 'vbr', '-cq', str(cq),
        '-c:a', 'copy',
        output_path
    ]

    print(f"\n⏳ Procesando con NVIDIA NVENC...")
    print("   (Presiona Ctrl+C para cancelar)\n")

    start_time = time.time()
    proc = subprocess.Popen(ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, 
                            text=True, encoding='utf-8', errors='replace')

    progress_regex = re.compile(r'time=(\d+:\d+:\d+\.\d+)')
    total_duration = info['duration']

    try:
        while True:
            line = proc.stdout.readline()
            if not line and proc.poll() is not None:
                break
            if 'time=' in line:
                match = progress_regex.search(line)
                if match:
                    time_str = match.group(1)
                    h_t, m, s = map(float, time_str.split(':'))
                    current_sec = h_t*3600 + m*60 + s
                    pct = min((current_sec / total_duration) * 100, 100)
                    elapsed = time.time() - start_time
                    speed = current_sec / elapsed if elapsed > 0 else 0
                    eta = (total_duration - current_sec) / speed if speed > 0 else 0
                    
                    sys.stdout.write(f"\r📊 Progreso: {pct:5.1f}% | Vel: {speed:5.1f}x | "
                                   f"⏱️ {elapsed/60:.1f}min | ETA: {eta/60:.1f}min   ")
                    sys.stdout.flush()
    except KeyboardInterrupt:
        print("\n\n⚠️  Proceso cancelado por el usuario")
        proc.terminate()
        return

    proc.wait()
    
    if proc.returncode == 0:
        total_time = (time.time() - start_time) / 60
        print(f"\n\n{'='*60}")
        print(f"🎉 ¡PROCESO COMPLETADO!")
        print(f"{'='*60}")
        print(f"📂 Archivo: {output_path}")
        print(f"⏱️  Tiempo total: {total_time:.1f} minutos")
        print(f"📊 Velocidad promedio: {(info['duration']/60)/total_time:.1f}x")
        print(f"💾 Tamaño: {os.path.getsize(output_path)/1024/1024:.1f} MB")
        print(f"{'='*60}\n")
        
        if sys.platform == 'win32':
            os.startfile(output_path)
    else:
        print(f"\n❌ FFmpeg falló (código {proc.returncode})")
        print("💡 Verifica que el video no esté corrupto")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        import traceback
        traceback.print_exc()