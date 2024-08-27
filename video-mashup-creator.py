import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pytube import YouTube
import subprocess
import random
import os
import logging
from tqdm import tqdm
import threading

# Configurar el registro
logging.basicConfig(filename='video_mashup.log', level=logging.DEBUG, format='%(asctime)s %(message)s')

ffmpeg_path = r'C:\ffmpeg\bin\ffmpeg.exe'  # Cambia esto a la ruta completa donde está ubicado ffmpeg.exe

def download_video(url, output_path):
    try:
        yt = YouTube(url)
        stream = yt.streams.filter(file_extension='mp4').get_highest_resolution()
        downloaded_file = stream.download(output_path=output_path)
        logging.info(f"Video descargado en: {downloaded_file}")
        return downloaded_file
    except Exception as e:
        logging.error(f"Error al descargar el video: {e}")
        messagebox.showerror("Error", f"Error al descargar el video: {e}")
        return None

def get_video_duration(input_file):
    ffprobe_command = f'{ffmpeg_path.replace("ffmpeg.exe", "ffprobe.exe")} -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "{input_file}"'
    result = subprocess.run(ffprobe_command, shell=True, capture_output=True, text=True)
    return float(result.stdout.strip())

def analyze_video():
    url = entry_url.get()
    video_path = entry_video_file.get()

    if not url and not video_path:
        messagebox.showerror("Error", "Debe proporcionar una URL de YouTube o seleccionar un archivo de video.")
        return

    if url:
        directory = os.path.dirname(video_path) if video_path else os.getcwd()
        downloaded_file = download_video(url, directory)
        if downloaded_file:
            input_file = downloaded_file
        else:
            logging.error("Error al descargar el video")
            return
    else:
        input_file = video_path

    video_duration = get_video_duration(input_file)
    entry_video_duration.delete(0, tk.END)
    entry_video_duration.insert(0, str(int(video_duration // 60)))  # Duración en minutos
    logging.info(f"Duración del video: {video_duration} segundos")

    button_create_mashup.config(state=tk.NORMAL)

def generate_random_clips(input_file, num_clips, clip_duration, progress_bar, effects, transition_duration):
    clips = []
    selected_times = []
    max_duration = get_video_duration(input_file)

    try:
        if not os.path.exists(input_file):
            raise FileNotFoundError(f"El archivo {input_file} no existe.")
        
        for i in range(num_clips):
            while True:
                start_time = random.uniform(0, max_duration - clip_duration)
                if not any(abs(start_time - t) < clip_duration for t in selected_times):
                    selected_times.append(start_time)
                    break

            start_time_str = f"{int(start_time // 3600):02}:{int((start_time % 3600) // 60):02}:{int(start_time % 60):02}"
            output_clip = os.path.join(os.path.dirname(input_file), f"clip_{os.path.basename(input_file).split('.')[0]}_{i}.mp4")
            
            # Comando ffmpeg básico con opciones de efectos
            filters = []
            if 'vhs' in effects:
                filters.append('curves=vintage')
            if 'interpolate' in effects:
                filters.append('minterpolate=fps=60')
            filter_str = ",".join(filters)

            ffmpeg_command = (
                f'{ffmpeg_path} -i "{input_file}" -ss {start_time_str} -t {clip_duration} '
                f'-vf "{filter_str}" -c:v libx264 -crf 18 -preset veryslow -c:a aac -b:a 192k "{output_clip}"'
                if filter_str else
                f'{ffmpeg_path} -i "{input_file}" -ss {start_time_str} -t {clip_duration} '
                f'-c:v libx264 -crf 18 -preset veryslow -c:a aac -b:a 192k "{output_clip}"'
            )
            
            logging.info(f"Ejecutando comando: {ffmpeg_command}")
            result = subprocess.run(ffmpeg_command, shell=True, capture_output=True, text=True)
            if result.returncode != 0:
                logging.error(f"Error al generar los clips: {result.stderr}")
                messagebox.showerror("Error", f"Error al generar los clips: {result.stderr}")
                return None
            clips.append(output_clip)
            progress_bar.update(1)
        return clips
    except Exception as e:
        logging.error(f"Error al generar los clips: {e}")
        messagebox.showerror("Error", f"Error al generar los clips: {e}")
        return None

def concatenate_clips(clips, output_file, transition_duration):
    try:
        if not clips:
            raise ValueError("No hay clips para concatenar.")
        
        with open("file_list.txt", "w") as file:
            for clip in clips:
                file.write(f"file '{clip}'\n")
        
        transition_filter = f'xfade=transition=fade:duration={transition_duration}:offset=1'
        ffmpeg_command = f'{ffmpeg_path} -f concat -safe 0 -i file_list.txt -vf "{transition_filter}" -c:v libx264 -crf 18 -preset veryslow -c:a aac -b:a 192k "{output_file}"'
        
        logging.info(f"Ejecutando comando: {ffmpeg_command}")
        result = subprocess.run(ffmpeg_command, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            logging.error(f"Error al concatenar los clips: {result.stderr}")
            messagebox.showerror("Error", f"Error al concatenar los clips: {result.stderr}")
        os.remove("file_list.txt")
    except Exception as e:
        logging.error(f"Error al concatenar los clips: {e}")
        messagebox.showerror("Error", f"Error al concatenar los clips: {e}")

def select_video_file():
    file_path = filedialog.askopenfilename(filetypes=[("Video Files", "*.mp4")])
    entry_video_file.delete(0, tk.END)
    entry_video_file.insert(0, file_path)

def create_mashup():
    url = entry_url.get()
    video_path = entry_video_file.get()

    if not url and not video_path:
        messagebox.showerror("Error", "Debe proporcionar una URL de YouTube o seleccionar un archivo de video.")
        return

    if url:
        directory = os.path.dirname(video_path) if video_path else os.getcwd()
        downloaded_file = download_video(url, directory)
        if downloaded_file:
            input_file = downloaded_file
        else:
            logging.error("Error al descargar el video")
            return
    else:
        input_file = video_path

    number_of_clips = int(entry_num_clips.get())
    clip_length = int(entry_clip_length.get())
    transition_duration = float(entry_transition_duration.get())

    all_clips = []

    progress_bar = tqdm(total=number_of_clips, desc="Generando clips")
    effects = []
    if vhs_var.get():
        effects.append('vhs')
    if interpolate_var.get():
        effects.append('interpolate')

    def generate_clips():
        nonlocal all_clips
        clips = generate_random_clips(input_file, number_of_clips, clip_length, progress_bar, effects, transition_duration)
        if clips:
            all_clips.extend(clips)

        output_video = os.path.join(os.path.dirname(input_file), entry_output_file.get())
        if all_clips:
            concatenate_clips(all_clips, output_video, transition_duration)
            logging.info(f"Mashup creado en: {output_video}")
            label_status.config(text="Mashup creado exitosamente!")

            for clip in all_clips:
                os.remove(clip)
        else:
            label_status.config(text="No se generaron clips.")
        progress_bar.close()

    thread = threading.Thread(target=generate_clips)
    thread.start()

root = tk.Tk()
root.title("Creador de Mashup de Video")

tk.Label(root, text="URL de YouTube:").grid(row=0, column=0, padx=10, pady=10)
entry_url = tk.Entry(root, width=50)
entry_url.grid(row=0, column=1, padx=10, pady=10)

tk.Label(root, text="o Archivo de video:").grid(row=1, column=0, padx=10, pady=10)
entry_video_file = tk.Entry(root, width=50)
entry_video_file.grid(row=1, column=1, padx=10, pady=10)
tk.Button(root, text="Seleccionar", command=select_video_file).grid(row=1, column=2, padx=10, pady=10)

tk.Button(root, text="Analizar Video", command=analyze_video).grid(row=2, column=1, padx=10, pady=10)

tk.Label(root, text="Duración del video (minutos):").grid(row=3, column=0, padx=10, pady=10)
entry_video_duration = tk.Entry(root)
entry_video_duration.grid(row=3, column=1, padx=10, pady=10)

tk.Label(root, text="Número de clips por video:").grid(row=4, column=0, padx=10, pady=10)
entry_num_clips = tk.Entry(root)
entry_num_clips.grid(row=4, column=1, padx=10, pady=10)

tk.Label(root, text="Duración de cada clip (segundos):").grid(row=5, column=0, padx=10, pady=10)
entry_clip_length = tk.Entry(root)
entry_clip_length.grid(row=5, column=1, padx=10, pady=10)

tk.Label(root, text="Duración de la transición (segundos):").grid(row=6, column=0, padx=10, pady=10)
entry_transition_duration = tk.Entry(root)
entry_transition_duration.grid(row=6, column=1, padx=10, pady=10)

tk.Label(root, text="Nombre del archivo de salida:").grid(row=7, column=0, padx=10, pady=10)
entry_output_file = tk.Entry(root)
entry_output_file.grid(row=7, column=1, padx=10, pady=10)

vhs_var = tk.BooleanVar()
tk.Checkbutton(root, text="Efecto VHS", variable=vhs_var).grid(row=8, column=0, padx=10, pady=10)

interpolate_var = tk.BooleanVar()
tk.Checkbutton(root, text="Interpolación de imagen", variable=interpolate_var).grid(row=8, column=1, padx=10, pady=10)

button_create_mashup = tk.Button(root, text="Crear Mashup", command=create_mashup, state=tk.DISABLED)
button_create_mashup.grid(row=9, column=1, padx=10, pady=10)

label_status = tk.Label(root, text="")
label_status.grid(row=10, column=0, columnspan=3, padx=10, pady=10)

root.mainloop()
