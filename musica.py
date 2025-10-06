import os
import yt_dlp
from difflib import SequenceMatcher
import sys
import subprocess

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
        '-strict', 'experimental',
        '-y',
        salida
    ]
    
    try:
        subprocess.run(comando, check=True, capture_output=True, text=True)
        print(f"✓ Video convertido exitosamente: {salida}")
        os.remove(ruta_video)
        return True
    except subprocess.CalledProcessError as e:
        print(f"✘ Error al convertir: {ruta_video}")
        print(f"Código de retorno: {e.returncode}")
        print(f"Salida: {e.stdout}")
        print(f"Error: {e.stderr}")
        return False
    except FileNotFoundError:
        print("Error: FFmpeg no se encontró. Asegúrate de que esté en el PATH o en la misma carpeta del ejecutable.")
        return False

def es_titulo_similar(titulo1, titulo2, umbral=0.85):
    """
    Compara dos títulos y determina si son similares según un umbral.
    """
    return SequenceMatcher(None, titulo1.lower(), titulo2.lower()).ratio() > umbral

def progress_hook(d, callback, video_actual, total_videos):
    """
    Función de gancho de progreso para yt-dlp en descargas múltiples.
    """
    if d['status'] == 'downloading':
        total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate')
        downloaded_bytes = d.get('downloaded_bytes')
        if total_bytes and downloaded_bytes:
            # Progreso del video actual
            percent_video = (downloaded_bytes / total_bytes) * 100
            # Progreso global considerando todos los videos
            percent_global = ((video_actual - 1) / total_videos) * 100 + (percent_video / total_videos)
            callback(percent_global)

def buscar_y_descargar(cantante, ruta_pendrive, max_videos, progress_callback=None):
    try:
        if not os.path.exists(ruta_pendrive):
            raise FileNotFoundError(f"La ruta del pendrive '{ruta_pendrive}' no existe.")
        
        carpeta_cantante = os.path.join(ruta_pendrive, cantante)
        if not os.path.exists(carpeta_cantante):
            print(f"\nCreando nueva carpeta para '{cantante}'...\n")
            os.makedirs(carpeta_cantante)
        else:
            print(f"\nLa carpeta para '{cantante}' ya existe. Usando la carpeta: {carpeta_cantante}\n")

        titulos_existentes = {os.path.splitext(f)[0].lower() for f in os.listdir(carpeta_cantante)}
        print(f"Buscando canciones de '{cantante}' en YouTube...\n")

        ydl_opts = {
            'format': 'bv*+ba/bestvideo+bestaudio/best',
            'outtmpl': os.path.join(carpeta_cantante, '%(title)s.%(ext)s'),
            'quiet': True,
            'extract_flat': True,
            'force_generic_extractor': True,
            'noplaylist': True,
            'playlist_items': '1-' + str(max_videos),
        }
        
        videos_a_descargar = []
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            busqueda = f"ytsearch{max_videos}:{cantante} musica"
            info = ydl.extract_info(busqueda, download=False)
            
            if 'entries' in info:
                for video in info['entries']:
                    if video and 'title' in video and 'url' in video:
                        titulo = video['title']
                        url = video['url']
                        duracion_segundos = video.get('duration')
                        
                        # Excluir videos de menos de 60 segundos o sin duración (posiblemente shorts o anuncios)
                        if duracion_segundos is None or duracion_segundos < 60:
                            print(f"Excluido: '{titulo}' (duración muy corta o sin duración).")
                            continue
                            print(f"Excluido: '{titulo}' (duración muy corta).")
                            continue
                        
                        # Comprobar si el video ya existe o si es similar a uno existente
                        es_duplicado_o_similar = False
                        for titulo_existente in titulos_existentes:
                            if es_titulo_similar(titulo, titulo_existente):
                                es_duplicado_o_similar = True
                                break
                        
                        if not es_duplicado_o_similar:
                            videos_a_descargar.append(url)
                            titulos_existentes.add(titulo.lower())
                            print(f"✓ Encontrado: '{titulo}'")
                        else:
                            print(f"Excluido: '{titulo}' (ya existe o es similar).")
                    else:
                        print(f"Advertencia: Video sin URL válida o título, se saltará la descarga.")

        if videos_a_descargar:
            print(f"\nDescargando {len(videos_a_descargar)} video(s)...")
            ydl_opts['extract_flat'] = False
            ydl_opts['quiet'] = False
            ydl_opts['ffmpeg_location'] = get_ffmpeg_path()
            
            # Agregar progress_hooks si hay callback
            if progress_callback:
                total_videos = len(videos_a_descargar)
                video_actual = [1]  # Usar lista para poder modificar en la función interna
                
                def hook(d):
                    progress_hook(d, progress_callback, video_actual[0], total_videos)
                    if d['status'] == 'finished':
                        video_actual[0] += 1
                
                ydl_opts['progress_hooks'] = [hook]
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl_download:
                ydl_download.download(videos_a_descargar)
                
            print("\nIniciando conversión a MP4 de los nuevos archivos...")
            for archivo in os.listdir(carpeta_cantante):
                ruta_completa = os.path.join(carpeta_cantante, archivo)
                if os.path.isfile(ruta_completa) and (archivo.endswith(('.webm', '.mkv')) or not archivo.endswith('.mp4')):
                    convertir_a_mp4_compatible(ruta_completa)
        else:
            print("No se encontraron videos nuevos que cumplan con los criterios.")

        print(f"\nDescargas completadas. Videos guardados en: {carpeta_cantante}")
    except FileNotFoundError as fnf_error:
        print(f"Error de archivo: {fnf_error}")
    except yt_dlp.utils.DownloadError as dl_error:
        print(f"Error de descarga: {dl_error}")
    except Exception as e:
        print(f"Error general: {e}")

def main_musica(cantantes_input, ruta_pendrive, max_videos, progress_callback=None):
    cantantes = [cantante.strip() for cantante in cantantes_input.split(',')]
    total_cantantes = len(cantantes)
    
    for idx, cantante in enumerate(cantantes, 1):
        print(f"\n{'='*50}")
        print(f"Procesando cantante {idx}/{total_cantantes}: {cantante}")
        print(f"{'='*50}\n")
        
        # Crear un callback que ajuste el progreso considerando múltiples cantantes
        if progress_callback:
            def adjusted_callback(percent):
                # Progreso global considerando todos los cantantes
                global_percent = ((idx - 1) / total_cantantes) * 100 + (percent / total_cantantes)
                progress_callback(global_percent)
            
            buscar_y_descargar(cantante, ruta_pendrive, max_videos, adjusted_callback)
        else:
            buscar_y_descargar(cantante, ruta_pendrive, max_videos)