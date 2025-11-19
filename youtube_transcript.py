from yt_transcript_tools.fetcher import fetch_transcript

video_id = "WH_ieAsb4AI"  # Replace with actual YouTube video ID

if __name__ == "__main__":
    try:
        out = fetch_transcript(video_id, "transcript.txt")
        print(f"Wrote transcript to {out}")
    except Exception as e:
        print(f"Failed to fetch transcript: {e}")
        raise
