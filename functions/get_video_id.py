import re

# Function to extract video ID from YouTube URL
def get_video_id(url):
    # Regular expression pattern to find the video ID
    pattern = r'v=(\w+)'

    # Search for the pattern in the URL
    match = re.search(pattern, url)

    if match:
        video_id = match.group(1)
        return video_id
    else:
        return None