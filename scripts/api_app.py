from fastapi import FastAPI, HTTPException
from pathlib import Path

from yt_transcript_tools.fetcher import fetch_transcript
from yt_transcript_tools.extractors import extract_questions, extract_qa

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
