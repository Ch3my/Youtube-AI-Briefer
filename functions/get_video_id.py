import re

def get_video_id(url):
    # Regular expression pattern to find the video ID
    # pattern = r'v=(\w+)'
    pattern = r'v=(-?\w+)' # include "-" in the video ID

    # Search for the pattern in the URL
    match = re.search(pattern, url)

    if match:
        video_id = match.group(1)
        # If the first character is a "-", ignore or delete it
        # YouTubeTranscriptApi does not like "-" at the beggining 
        if video_id.startswith('-'):
            video_id = video_id[1:]
        return video_id
    else:
        return None
