from typing import List
from youtube_transcript_api import YouTubeTranscriptApi


def get_transcript_from_video_id(video_id: str) -> List[str]:
    """Return transcript lines (text) for a given YouTube `video_id`.

    Uses the installed `youtube_transcript_api` and returns a list of
    strings (one per transcript snippet). Exceptions from the underlying
    library are propagated.
    """
    # Use instance `fetch` for compatibility with newer library versions
    transcript = YouTubeTranscriptApi().fetch(video_id)
    lines = []
    for entry in transcript:
        # entry can be an object with .text or a dict
        if hasattr(entry, "text"):
            lines.append(entry.text)
        else:
            lines.append(entry.get("text") if isinstance(entry, dict) else str(entry))
    return lines
