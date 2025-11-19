from youtube_transcript_api import YouTubeTranscriptApi

video_id = "WH_ieAsb4AI"  # Replace with actual YouTube video ID

try:
    # current installed library exposes `fetch` / `list` instead of `get_transcript`
    # create an instance and call `fetch`
    transcript = YouTubeTranscriptApi().fetch(video_id)
except Exception as e:
    # print a helpful error and re-raise so exit code indicates failure
    print(f"Failed to retrieve transcript for video '{video_id}': {e}")
    raise

# Save to text file
with open("transcript.txt", "w", encoding="utf-8") as f:
    for entry in transcript:
        # `transcript` yields `FetchedTranscriptSnippet` objects
        # which expose attributes (`text`, `start`, `duration`)
        f.write(entry.text + "\n")
