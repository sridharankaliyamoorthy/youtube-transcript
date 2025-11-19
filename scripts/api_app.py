from fastapi import FastAPI, HTTPException, Query
from pathlib import Path
import re

from yt_transcript_tools.fetcher import fetch_transcript
from yt_transcript_tools.extractors import extract_questions, extract_qa
from yt_transcript_tools.downloader import get_transcript_from_video_id
from yt_transcript_tools.question_extractor import extract_questions as extract_questions_from_text

app = FastAPI(title="YouTube Transcript Tools API")


@app.get("/")
def root():
    return {"message": "YouTube Transcript API is up and running!"}


@app.post("/fetch")
def fetch(video_id: str, output: str = "transcript.txt"):
    """Fetch transcript for `video_id` and write to `output` file.

    Example: POST /fetch?video_id=abcd1234&output=transcript.txt
    """
    try:
        out_path = fetch_transcript(video_id, output)
        return {"status": "ok", "path": str(out_path)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/questions")
def questions(input: str = "transcript.txt", output: str = "questions.txt"):
    """Extract questions from `input` and save to `output`.

    Returns the number of detected questions and the output path.
    """
    in_path = Path(input)
    if not in_path.exists():
        raise HTTPException(status_code=404, detail=f"Input file not found: {input}")
    try:
        count = extract_questions(in_path, Path(output))
        return {"status": "ok", "questions": count, "path": str(Path(output))}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/qa")
def qa(input: str = "transcript.txt", output: str = "qa.txt"):
    """Extract Q/A pairs from `input` and save to `output`.

    Returns the number of Q/A pairs and the output path.
    """
    in_path = Path(input)
    if not in_path.exists():
        raise HTTPException(status_code=404, detail=f"Input file not found: {input}")
    try:
        count = extract_qa(in_path, Path(output))
        return {"status": "ok", "qa_pairs": count, "path": str(Path(output))}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def extract_video_id(youtube_url: str) -> str:
    """Extract a YouTube video id (11 chars) from a URL or accept an ID directly."""
    if not youtube_url:
        raise ValueError("youtube_url is empty")
    # Accept raw ID
    if re.fullmatch(r"[0-9A-Za-z_-]{11}", youtube_url):
        return youtube_url
    # common patterns
    m = re.search(r"(?:v=|/)([0-9A-Za-z_-]{11})", youtube_url)
    if m:
        return m.group(1)
    raise ValueError("Invalid YouTube URL or video id")


@app.get("/extract/")
def extract(youtube_url: str = Query(..., description="Full YouTube video URL or video id")):
    """Fetch transcript for a full YouTube URL (or ID) and return transcript + detected questions.

    This endpoint uses `yt_transcript_tools.downloader.get_transcript_from_video_id`
    and `yt_transcript_tools.question_extractor.extract_questions`.
    """
    try:
        video_id = extract_video_id(youtube_url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    try:
        transcript_lines = get_transcript_from_video_id(video_id)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Failed to fetch transcript: {e}")

    # join and extract questions
    joined = "\n".join(transcript_lines)
    questions = extract_questions_from_text(joined)

    return {"video_id": video_id, "transcript": transcript_lines, "questions": questions}
