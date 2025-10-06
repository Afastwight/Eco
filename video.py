import os
import sys
import yt_dlp
import subprocess
import time
import threading # Importamos threading

def get_ffmpeg_path():
    """
    Obtiene la ruta a ffmpeg.exe, ya sea en desarrollo o empaquetado por PyInstaller.
    """

    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    ffmpeg_local = os.path.join(base_path, 'ffmpeg.exe')
    
    if os.path.exists(ffmpeg_local):
        return ffmpeg_local

    return 'ffmpeg' 

def convertir_a_mp4_compatible(ruta_video):
    """
    Convierte un video a MP4 usando ffmpeg con configuración optimizada.
    """
    if not os.path.exists(ruta_video):
        print(f"Error: El archivo no existe")
        return False

    salida = ruta_video.rsplit('.', 1)[0] + '.mp4'

    if ruta_video == salida:
        print("El archivo ya es MP4")
        return True

    ffmpeg_path = get_ffmpeg_path()

    # Configuración más rápida de FFmpeg
    comando = [
        ffmpeg_path,
        '-i', ruta_video,
        '-c:v', 'copy',  # Copiar video sin recodificar (más rápido)
        '-c:a', 'aac',   # Solo recodificar audio
        '-y',
        salida
    ]

    try:
        # Usar subprocess.run para mejor control
        subprocess.run(comando, check=True, creationflags=subprocess.CREATE_NO_WINDOW)
        print(f"✔ Video convertido exitosamente: {salida}")
        os.remove(ruta_video)
        return True
    except subprocess.CalledProcessError as e:
        print(f"✘ Error al convertir: {ruta_video}. Código de error: {e.returncode}")
        return False

def progress_hook(d, callback):
    """
    Función de gancho de progreso para yt-dlp.
    """
    if d['status'] == 'downloading':
        # Obtener el porcentaje de progreso
        total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate')
        downloaded_bytes = d.get('downloaded_bytes')
        if total_bytes and downloaded_bytes:
            percent = downloaded_bytes / total_bytes * 100
            # Llamar al callback con el progreso en un hilo seguro para la GUI
            callback(percent)

def descargar_por_url(url, ruta_pendrive, progress_callback):
    """Descarga un video de YouTube por su URL y lo convierte a MP4 si es necesario."""
    try:
        if not os.path.exists(ruta_pendrive):
            raise FileNotFoundError(f"La ruta del pendrive '{ruta_pendrive}' no existe.")

        ydl_opts = {
            'outtmpl': os.path.join(ruta_pendrive, '%(title)s.%(ext)s'),
            'format': 'bv*+ba/bestvideo+bestaudio/best',
            'quiet': False,
            'noplaylist': True,
            'ffmpeg_location': get_ffmpeg_path(),
            'progress_hooks': [lambda d: progress_hook(d, progress_callback)], # ¡Nuevo!
        }
        
        print(f"\nBuscando video en la URL: {url}\n")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            if info:
                titulo = info.get('title', 'video')
                archivos = os.listdir(ruta_pendrive)
                archivo_descargado = None
                
                for archivo in archivos:
                    if titulo in archivo or info.get('id', '') in archivo:
                        ruta_completa = os.path.join(ruta_pendrive, archivo)
                        if os.path.isfile(ruta_completa):
                            archivo_descargado = ruta_completa
                            break
                
                if archivo_descargado:
                    # Si no es MP4, convertir
                    if not archivo_descargado.endswith('.mp4'):
                        print(f"\nEl archivo se descargo como: {os.path.basename(archivo_descargado)}")
                        print("Convirtiendo a MP4...")
                        if convertir_a_mp4_compatible(archivo_descargado):
                            print("\nConversion completada exitosamente")
                        else:
                            print("\nAdvertencia: La conversion fallo")
                            print("El archivo se quedo como .webm")
                    else:
                        print("\nArchivo ya esta en formato MP4")
                
        print(f"\nProceso completado. Archivos en: {ruta_pendrive}")

    except FileNotFoundError as fnf_error:
        print(fnf_error)
    except yt_dlp.utils.DownloadError as dl_error:
        print(f"Error de descarga: {dl_error}")
    except Exception as e:
        print(f"Error: {e}")