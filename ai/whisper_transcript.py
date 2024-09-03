import os
import subprocess
import sys
import tempfile
from openai import OpenAI
import yt_dlp
from globals import set_feedback_msg
import tempfile

def split_audio(file_path, max_size_mb=25):
    # Determine the duration of the audio file in seconds
    command = [
        'ffmpeg',
        '-i', file_path,
        '-hide_banner',
        '-vn',  # No video
        '-f', 'null',
        '-'
    ]

    # Set creationflags to suppress the console window on Windows
    creationflags = 0
    if sys.platform == "win32":
        creationflags = subprocess.CREATE_NO_WINDOW

    result = subprocess.run(command, stderr=subprocess.PIPE, stdout=subprocess.PIPE, creationflags=creationflags)
    output = result.stderr.decode('utf-8')
    
    # Extract duration from FFmpeg output
    duration_line = [x for x in output.splitlines() if 'Duration' in x][0]
    duration = duration_line.split(",")[0].split()[1]
    h, m, s = duration.split(':')
    total_duration = int(h) * 3600 + int(m) * 60 + float(s)
    
    # Segment duration in seconds (10 minutes)
    segment_duration = 10 * 60
    segments = []
    
    for i in range(0, int(total_duration), segment_duration):
        start_time = i
        end_time = min(i + segment_duration, total_duration)
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
        
        command = [
            'ffmpeg',
            '-i', file_path,
            '-ss', str(start_time),
            '-t', str(end_time - start_time),
            '-c', 'copy',
            '-y',  # Overwrite output files without asking
            temp_file.name
        ]
        
        # Run the command, suppressing the console window and any output
        subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=creationflags)
        
        segments.append(temp_file.name)
    
    return segments

def detect_language_and_transcribe(video_url, output_dir=None):
    # Use SO temp location
    if output_dir is None:
        output_dir = tempfile.gettempdir()

    # Download the audio using yt-dlp
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": f"{output_dir}/%(id)s.%(ext)s",
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ],
    }
    set_feedback_msg("Descargando Video")
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(video_url, download=True)
        video_id = info_dict.get("id", None)
        audio_file = os.path.join(output_dir, f"{video_id}.mp3")

    set_feedback_msg("Cortando el Audio")
    # Split the audio file if necessary
    audio_segments = split_audio(audio_file)
    
    client = OpenAI()

    transcriptions = []
    for index, segment in enumerate(audio_segments):
        set_feedback_msg(f"Procesando segmento de Audio N° {index}/{len(audio_segments)}")
        with open(segment, "rb") as file_handle:
            transcription = client.audio.transcriptions.create(
                model="whisper-1", 
                file=file_handle, 
                response_format="text"
            )
            transcriptions.append(transcription)

        # Cleanup: delete the segment after processing
        os.remove(segment)

    # Cleanup: delete the original audio file
    os.remove(audio_file)

    # Combine all transcriptions into one
    full_transcription = " ".join(transcriptions)

    return full_transcription
