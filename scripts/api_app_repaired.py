from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from uuid import uuid4
import re


try:
    from yt_transcript_tools.downloader import get_transcript_from_video_id
except Exception:
    def get_transcript_from_video_id(video_id):
        raise RuntimeError("downloader not available")


try:
    from yt_transcript_tools.question_extractor import extract_questions as extract_questions_from_text
except Exception:
    def extract_questions_from_text(text):
        return []


try:
    from yt_transcript_tools.advanced_qa import extract_qa_advanced
except Exception:
    def extract_qa_advanced(lines, questions=None):
        return []


try:
    from yt_transcript_tools.perplexity import summarize_text as perplexity_summarize
except Exception:
    def perplexity_summarize(text):
        return None


app = FastAPI(title="YouTube Transcript Tools API (repaired)")
OUT_DIR = Path("outputs")
OUT_DIR.mkdir(exist_ok=True)
app.mount("/outputs", StaticFiles(directory=str(OUT_DIR)), name="outputs")

JOBS = {}


def extract_video_id(youtube_url: str) -> str:
    if not youtube_url:
        raise ValueError("youtube_url is empty")
    if re.fullmatch(r"[0-9A-Za-z_-]{11}", youtube_url):
        return youtube_url
    m = re.search(r"(?:v=|/)([0-9A-Za-z_-]{11})", youtube_url)
    if m:
        return m.group(1)
    raise ValueError("Invalid YouTube URL or video id")


def _do_extraction(video_id: str, write_files: bool = True, use_perplexity: bool = False):
    transcript_lines = get_transcript_from_video_id(video_id)
    joined = "\n".join(transcript_lines)
    questions = []
    qa_pairs = []
    try:
        questions = extract_questions_from_text(joined)
    except Exception:
        questions = []
    try:
        qa_pairs = extract_qa_advanced(transcript_lines, questions=questions)
    except Exception:
        qa_pairs = []

    if write_files:
        out = OUT_DIR
        transcript_path = out / f"{video_id}_transcript.txt"
        transcript_path.write_text(joined, encoding="utf-8")
        summary_path = out / f"{video_id}_summary.txt"
        summary_path.write_text(f"Video ID: {video_id}\nLines: {len(transcript_lines)}\n", encoding="utf-8")
        return {"status": "ok", "video_id": video_id, "transcript_path": str(transcript_path), "summary_path": str(summary_path)}

    return {"status": "ok", "video_id": video_id, "transcript_count": len(transcript_lines), "questions": questions, "qa_pairs": qa_pairs}


@app.get("/")
def root():
    return {"message": "YouTube Transcript API (repaired)"}


@app.post('/extract_async')
def extract_async(youtube_url: str = Query(...), write_files: bool = Query(True), use_perplexity: bool = Query(False), background_tasks: BackgroundTasks = None):
    try:
        vid = extract_video_id(youtube_url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    job_id = str(uuid4())
    JOBS[job_id] = {"status": "queued", "result": None}

    def _run():
        JOBS[job_id]["status"] = "running"
        try:
            res = _do_extraction(vid, write_files=write_files, use_perplexity=use_perplexity)
            JOBS[job_id]["status"] = "done"
            JOBS[job_id]["result"] = res
        except Exception as e:
            JOBS[job_id]["status"] = "error"
            JOBS[job_id]["result"] = {"error": str(e)}

    if background_tasks is not None:
        background_tasks.add_task(_run)
    else:
        _run()
    return {"job_id": job_id}


@app.get('/status/{job_id}')
def job_status(job_id: str):
    job = JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job id not found")
    return job


@app.get('/ui', response_class=HTMLResponse)
def ui():
    html = """
    <html>
      <body>
        <h3>YouTube Transcript Extractor (repaired)</h3>
        <form onsubmit="fetch('/extract_async?youtube_url='+encodeURIComponent(document.getElementById('url').value),{method:'POST'}).then(r=>r.json()).then(j=>alert('job: '+j.job_id)); return false;">
          <input id="url" placeholder="video id or URL" style="width:60%" />
          <button type="submit">Start</button>
        </form>
        <p>Use the <code>/status/{job_id}</code> endpoint to poll results.</p>
      </body>
    </html>
    """
    return HTMLResponse(content=html)
