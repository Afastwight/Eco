import customtkinter
from tkinter import filedialog, messagebox
import threading
import sys
from io import StringIO

# Importar las funciones de los archivos de lógica
from musica import main_musica
from video import descargar_por_url

# Configuración de la apariencia y tema de CustomTkinter
customtkinter.set_appearance_mode("Dark")
customtkinter.set_default_color_theme("blue")

class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        self.title("🎶 Eco - Mira el mundo desde eco")
        self.geometry("650x800")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Contenedor de las pestañas
        self.tab_view = customtkinter.CTkTabview(self)
        self.tab_view.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        self.tab_view.add("Música (por Cantante)")
        self.tab_view.add("Videos (por URL)")

        # Contenedor para el registro de eventos unificado
        self.log_frame = customtkinter.CTkFrame(self)
        self.log_frame.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="nsew")
        self.log_frame.grid_columnconfigure(0, weight=1)
        self.log_frame.grid_rowconfigure(1, weight=1)
        
        self.log_label = customtkinter.CTkLabel(self.log_frame, text="Estado del Proceso:", font=customtkinter.CTkFont(weight="bold"))
        self.log_label.grid(row=0, column=0, padx=10, pady=(10, 0), sticky="w")
        
        self.textbox_log = customtkinter.CTkTextbox(self.log_frame, height=200)
        self.textbox_log.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        self.textbox_log.configure(state="disabled")

        # Configurar la interfaz de cada pestaña
        self.setup_musica_tab()
        self.setup_video_tab()

        # Capturar la salida de la consola (stdout)
        self.output_buffer = StringIO()
        sys.stdout = self.output_buffer
        self.after(100, self.update_log_from_stdout)
        
    def setup_musica_tab(self):
        """Configura la pestaña de Música con barra de progreso"""
        musica_tab = self.tab_view.tab("Música (por Cantante)")
        musica_tab.grid_columnconfigure(0, weight=1)
        musica_tab.grid_rowconfigure(0, weight=1)
        
        # Crear un frame scrollable para el contenido
        scrollable_frame = customtkinter.CTkScrollableFrame(musica_tab)
        scrollable_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        scrollable_frame.grid_columnconfigure(0, weight=1)

        self.label_cantante = customtkinter.CTkLabel(scrollable_frame, text="Nombres de Cantantes (separados por comas):")
        self.label_cantante.grid(row=0, column=0, padx=20, pady=(10, 0), sticky="w")
        
        self.entry_cantante = customtkinter.CTkEntry(scrollable_frame, placeholder_text="Ej. Bad Bunny, Rosalía")
        self.entry_cantante.grid(row=1, column=0, padx=20, pady=5, sticky="ew")

        self.label_ruta_musica = customtkinter.CTkLabel(scrollable_frame, text="Ruta de Destino:")
        self.label_ruta_musica.grid(row=2, column=0, padx=20, pady=(10, 0), sticky="w")
        
        self.frame_ruta_musica = customtkinter.CTkFrame(scrollable_frame)
        self.frame_ruta_musica.grid(row=3, column=0, padx=20, pady=5, sticky="ew")
        self.frame_ruta_musica.grid_columnconfigure(0, weight=1)
        
        self.entry_ruta_musica = customtkinter.CTkEntry(self.frame_ruta_musica, placeholder_text="Ej. C:/Users/tu_usuario/Música")
        self.entry_ruta_musica.grid(row=0, column=0, sticky="ew")
        
        self.button_browse_musica = customtkinter.CTkButton(self.frame_ruta_musica, text="Seleccionar", width=100, command=lambda: self.browse_folder(self.entry_ruta_musica))
        self.button_browse_musica.grid(row=0, column=1, padx=(5, 0))

        self.label_videos = customtkinter.CTkLabel(scrollable_frame, text="Cantidad de videos a descargar por cantante:")
        self.label_videos.grid(row=4, column=0, padx=20, pady=(10, 0), sticky="w")
        
        self.entry_videos = customtkinter.CTkEntry(scrollable_frame, placeholder_text="5", width=100)
        self.entry_videos.grid(row=5, column=0, padx=20, pady=5, sticky="w")

        # ⭐ BARRA DE PROGRESO PARA MÚSICA ⭐
        self.progress_label_musica = customtkinter.CTkLabel(scrollable_frame, text="Progreso de descarga:")
        self.progress_label_musica.grid(row=6, column=0, padx=20, pady=(10, 0), sticky="w")
        
        self.progress_bar_musica = customtkinter.CTkProgressBar(scrollable_frame)
        self.progress_bar_musica.grid(row=7, column=0, padx=20, pady=5, sticky="ew")
        self.progress_bar_musica.set(0)
        
        self.progress_percentage_musica = customtkinter.CTkLabel(scrollable_frame, text="0%")
        self.progress_percentage_musica.grid(row=8, column=0, padx=20, pady=(0, 5), sticky="w")

        self.button_start_musica = customtkinter.CTkButton(scrollable_frame, text="Iniciar Descarga", command=self.start_musica_thread, height=30, width=150)
        self.button_start_musica.grid(row=9, column=0, padx=20, pady=20)

    def setup_video_tab(self):
        """Configura la pestaña de Videos con barra de progreso"""
        video_tab = self.tab_view.tab("Videos (por URL)")
        video_tab.grid_columnconfigure(0, weight=1)
        video_tab.grid_rowconfigure(5, weight=1)
        
        # Campo URL
        self.label_url = customtkinter.CTkLabel(video_tab, text="URL del video de YouTube:")
        self.label_url.grid(row=0, column=0, padx=20, pady=(20, 0), sticky="w")
        
        self.entry_url = customtkinter.CTkEntry(video_tab, placeholder_text="Ej. https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        self.entry_url.grid(row=1, column=0, padx=20, pady=5, sticky="ew")

        # Campo Ruta
        self.label_ruta_video = customtkinter.CTkLabel(video_tab, text="Ruta de Destino:")
        self.label_ruta_video.grid(row=2, column=0, padx=20, pady=(15, 0), sticky="w")
        
        self.frame_ruta_video = customtkinter.CTkFrame(video_tab)
        self.frame_ruta_video.grid(row=3, column=0, padx=20, pady=5, sticky="ew")
        self.frame_ruta_video.grid_columnconfigure(0, weight=1)
        
        self.entry_ruta_video = customtkinter.CTkEntry(self.frame_ruta_video, placeholder_text="Ej. C:/Users/tu_usuario/Videos")
        self.entry_ruta_video.grid(row=0, column=0, sticky="ew")
        
        self.button_browse_video = customtkinter.CTkButton(self.frame_ruta_video, text="Seleccionar", width=100, command=lambda: self.browse_folder(self.entry_ruta_video))
        self.button_browse_video.grid(row=0, column=1, padx=(5, 0))

        # ⭐ BARRA DE PROGRESO PARA VIDEOS ⭐
        self.progress_label = customtkinter.CTkLabel(video_tab, text="Progreso de descarga:")
        self.progress_label.grid(row=4, column=0, padx=20, pady=(15, 0), sticky="w")
        
        self.progress_bar = customtkinter.CTkProgressBar(video_tab)
        self.progress_bar.grid(row=5, column=0, padx=20, pady=5, sticky="ew")
        self.progress_bar.set(0)
        
        self.progress_percentage = customtkinter.CTkLabel(video_tab, text="0%")
        self.progress_percentage.grid(row=6, column=0, padx=20, pady=(0, 10), sticky="w")

        self.button_start_video = customtkinter.CTkButton(video_tab, text="Iniciar Descarga", command=self.start_video_thread)
        self.button_start_video.grid(row=7, column=0, padx=20, pady=(20, 10), sticky="n")

    def browse_folder(self, entry_widget):
        """Abre el diálogo para seleccionar carpeta"""
        folder_path = filedialog.askdirectory()
        if folder_path:
            entry_widget.delete(0, customtkinter.END)
            entry_widget.insert(0, folder_path)

    def update_log_from_stdout(self):
        """Lee la salida del buffer y la muestra en el log en la GUI"""
        output = self.output_buffer.getvalue()
        if output:
            self.textbox_log.configure(state="normal")
            self.textbox_log.insert("end", output)
            self.textbox_log.see("end")
            self.textbox_log.configure(state="disabled")
            self.output_buffer.truncate(0)
            self.output_buffer.seek(0)
        self.after(100, self.update_log_from_stdout)

    def update_progress(self, percent):
        """Actualiza la barra de progreso de VIDEOS"""
        self.progress_bar.set(percent / 100.0)
        self.progress_percentage.configure(text=f"{int(percent)}%")

    def update_progress_musica(self, percent):
        """⭐ Actualiza la barra de progreso de MÚSICA ⭐"""
        self.progress_bar_musica.set(percent / 100.0)
        self.progress_percentage_musica.configure(text=f"{int(percent)}%")

    def start_musica_thread(self):
        """Inicia el proceso de descarga de música en un hilo separado"""
        cantantes_input = self.entry_cantante.get()
        ruta_musica_input = self.entry_ruta_musica.get()
        videos_input = self.entry_videos.get()
        
        if not cantantes_input or not ruta_musica_input or not videos_input:
            messagebox.showerror("Error de Entrada", "Por favor, completa todos los campos.")
            return

        try:
            videos_input = int(videos_input)
            if videos_input <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Error de Entrada", "La cantidad de videos debe ser un número válido mayor a 0.")
            return

        # ⭐ Resetear la barra de progreso ⭐
        self.progress_bar_musica.set(0)
        self.progress_percentage_musica.configure(text="0%")

        self.button_start_musica.configure(state="disabled", text="Procesando...")
        self.textbox_log.configure(state="normal")
        self.textbox_log.delete("1.0", "end")
        self.textbox_log.insert("end", "🚀 Iniciando proceso de descarga de música...\n")
        self.textbox_log.see("end")
        self.textbox_log.configure(state="disabled")

        thread = threading.Thread(target=self.run_musica_logic, args=(cantantes_input, ruta_musica_input, videos_input))
        thread.start()

    def run_musica_logic(self, cantantes, ruta, videos):
        """⭐ Ejecuta la lógica de descarga de música CON CALLBACK DE PROGRESO ⭐"""
        try:
            # ⭐ Crear callback para actualizar progreso ⭐
            def progress_callback(percent):
                self.after(0, lambda: self.update_progress_musica(percent))
            
            # ⭐ Pasar el callback a main_musica ⭐
            main_musica(cantantes, ruta, videos, progress_callback)
            
            self.textbox_log.configure(state="normal")
            self.textbox_log.insert("end", "\n✅ Proceso de descarga de música completado.\n")
            self.textbox_log.see("end")
            self.textbox_log.configure(state="disabled")
            
            # ⭐ Establecer progreso al 100% al finalizar ⭐
            self.after(0, lambda: self.update_progress_musica(100))
            
        except Exception as e:
            self.textbox_log.configure(state="normal")
            self.textbox_log.insert("end", f"\n🛑 Ocurrió un error inesperado: {e}\n")
            self.textbox_log.see("end")
            self.textbox_log.configure(state="disabled")
            messagebox.showerror("Error", f"Ocurrió un error inesperado: {e}")
        finally:
            self.button_start_musica.configure(state="normal", text="Iniciar Descarga")

    def start_video_thread(self):
        """Inicia el proceso de descarga de video en un hilo separado"""
        url_input = self.entry_url.get()
        ruta_video = self.entry_ruta_video.get()
        
        if not url_input or not ruta_video:
            messagebox.showerror("Error de Entrada", "Por favor, completa todos los campos.")
            return
        
        # Resetear la barra de progreso
        self.progress_bar.set(0)
        self.progress_percentage.configure(text="0%")
        
        self.button_start_video.configure(state="disabled", text="Procesando...")
        self.textbox_log.configure(state="normal")
        self.textbox_log.delete("1.0", "end")
        self.textbox_log.insert("end", "🚀 Iniciando descarga de video por URL...\n")
        self.textbox_log.see("end")
        self.textbox_log.configure(state="disabled")

        thread = threading.Thread(target=self.run_video_logic, args=(url_input, ruta_video))
        thread.start()

    def run_video_logic(self, url, ruta):
        """Ejecuta la lógica de descarga de video CON CALLBACK DE PROGRESO"""
        try:
            def progress_callback(percent):
                self.after(0, lambda: self.update_progress(percent))
            
            descargar_por_url(url, ruta, progress_callback)
            
            self.textbox_log.configure(state="normal")
            self.textbox_log.insert("end", "\n✅ Descarga del video por URL completada.\n")
            self.textbox_log.see("end")
            self.textbox_log.configure(state="disabled")
            
            self.after(0, lambda: self.update_progress(100))
            
        except Exception as e:
            self.textbox_log.configure(state="normal")
            self.textbox_log.insert("end", f"\n🛑 Ocurrió un error inesperado: {e}\n")
            self.textbox_log.see("end")
            self.textbox_log.configure(state="disabled")
            messagebox.showerror("Error", f"Ocurrió un error inesperado: {e}")
        finally:
            self.button_start_video.configure(state="normal", text="Iniciar Descarga")

if __name__ == "__main__":
    app = App()
    app.mainloop()