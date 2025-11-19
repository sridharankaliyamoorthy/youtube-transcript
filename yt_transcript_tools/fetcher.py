from pathlib import Path
from typing import Iterable

from youtube_transcript_api import YouTubeTranscriptApi


def _entry_text(entry) -> str:
    """Return the text for a transcript entry, handling both attribute and dict styles."""
    # Some library versions return objects with `.text` attribute; others are dict-like.
    text = None
    if hasattr(entry, "text"):
        text = getattr(entry, "text")
    else:
        try:
            text = entry["text"]
        except Exception:
            text = str(entry)
    return text


def fetch_transcript(video_id: str, out_path: str | Path = "transcript.txt") -> Path:
    """Fetch transcript for `video_id` and write to `out_path` (UTF-8).

    Returns the path to the written file. Raises exceptions from the
    underlying `youtube_transcript_api` if retrieval fails.
    """
    transcript = YouTubeTranscriptApi().fetch(video_id)
    out_path = Path(out_path)
    with out_path.open("w", encoding="utf-8") as fh:
        for entry in transcript:
            fh.write(_entry_text(entry) + "\n")
    return out_path


def fetch_transcript_lines(video_id: str) -> Iterable[str]:
    """Yield transcript text lines (strings) for the video ID without writing a file."""
    transcript = YouTubeTranscriptApi().fetch(video_id)
    for entry in transcript:
        yield _entry_text(entry)
