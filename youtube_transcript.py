from yt_transcript_tools.fetcher import fetch_transcript
import re

def extract_video_id(url_or_id):
    m = re.search(r"[?&]v=([\w-]{11})", url_or_id)
    if m:
        return m.group(1)
    m = re.search(r"youtu\.be/([\w-]{11})", url_or_id)
    if m:
        return m.group(1)
    m = re.search(r"embed/([\w-]{11})", url_or_id)
    if m:
        return m.group(1)
    if re.match(r"^[\w-]{11}$", url_or_id):
        return url_or_id
    raise ValueError("Could not extract video id from input!")

if __name__ == "__main__":
    url_or_id = input("Paste YouTube URL or video id: ").strip()
    try:
        video_id = extract_video_id(url_or_id)
        out = fetch_transcript(video_id, "transcript.txt")
        print(f"Wrote transcript to {out}")
    except Exception as e:
        print(f"Failed to fetch transcript: {e}")
        raise
