from functions.get_video_id import get_video_id
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
from globals import set_feedback_msg

def get_transcript(url):
    YT_VIDEO_ID = get_video_id(url)
    if YT_VIDEO_ID is None:
        return None

    # Nos aseguramos traer el modelo, ayuda a no tener que
    # El transcript llega un JSON con cada dialogo como subtitulos, lo juntamos todo en un solo string
    chunks = []
    try:
        # Your code that might raise the TranscriptsDisabled exception
        chunks = YouTubeTranscriptApi.get_transcript(YT_VIDEO_ID, languages=["es", "en", "en-GB"])
    except TranscriptsDisabled as e:
        print("Caught TranscriptsDisabled exception:", e)
        set_feedback_msg("La transcripcion esta desactivada para este video :(")
        return None
    except NoTranscriptFound as e:
        print("Caught NoTranscriptFound exception:", e)
        set_feedback_msg("No existe un transcript en los idiomas aceptados :(")


    transcript = []
    for i in chunks:
        transcript.append(i["text"])

    transcript = " ".join(transcript)
    return transcript