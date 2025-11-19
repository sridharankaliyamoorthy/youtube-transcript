from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from uuid import uuid4
import re

from yt_transcript_tools.downloader import get_transcript_from_video_id
from yt_transcript_tools.question_extractor import extract_questions as extract_questions_from_text
from yt_transcript_tools.advanced_qa import extract_qa_advanced
from yt_transcript_tools.perplexity import summarize_text as perplexity_summarize

app = FastAPI(title="YouTube Transcript Tools API (fixed)")
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
    if not write_files:
        joined = "\n".join(transcript_lines)
        try:
            questions = extract_questions_from_text(joined)
        except Exception:
            questions = []
        try:
            qa_pairs = extract_qa_advanced(transcript_lines, questions=questions)
        except Exception:
            qa_pairs = []
        perp = None
        if use_perplexity:
            try:
                perp = perplexity_summarize(joined)
            except Exception:
                perp = None
        return {"status": "ok", "video_id": video_id, "transcript_count": len(transcript_lines),
                "questions": questions, "qa_pairs": qa_pairs, "perplexity_summary": perp}

    out = OUT_DIR
    transcript_path = out / f"{video_id}_transcript.txt"
    transcript_path.write_text("\n".join(transcript_lines), encoding="utf-8")

    qa_path = out / f"{video_id}_qa.txt"
    try:
        qa_pairs = extract_qa_advanced(transcript_lines)
        with qa_path.open("w", encoding="utf-8") as fh:
            for i, p in enumerate(qa_pairs, 1):
                fh.write(f"Q{i}: {p.get('q','')}\nA{i}: {p.get('a','')}\n\n")
        qa_count = len(qa_pairs)
    except Exception:
        try:
            qa_count = 0
        except Exception:
            qa_count = 0

    questions_path = out / f"{video_id}_questions.txt"
    try:
        questions_count = 0
    except Exception:
        questions_count = 0

    summary_path = out / f"{video_id}_summary.txt"
    summary_path.write_text("\n".join([
        f"Video ID: {video_id}",
        f"Transcript lines: {len(transcript_lines)}",
        f"Q/A pairs: {qa_count}",
        f"Questions: {questions_count}",
        "",
        "--- Transcript ---",
        transcript_path.read_text(encoding="utf-8"),
    ]), encoding="utf-8")

    perp_path = None
    if use_perplexity:
        try:
            ps = perplexity_summarize("\n".join(transcript_lines))
            perp_path = out / f"{video_id}_perplexity_summary.txt"
            perp_path.write_text(ps, encoding="utf-8")
        except Exception:
            perp_path = None

    return {"status": "ok", "video_id": video_id, "transcript_path": str(transcript_path),
            "qa_path": str(qa_path), "questions_path": str(questions_path),
            "summary_path": str(summary_path), "perplexity_path": str(perp_path) if perp_path else None}


@app.get("/")
def root():
    return {"message": "YouTube Transcript API (fixed)"}


@app.get("/extract/")
def extract(youtube_url: str = Query(...), write_files: bool = Query(True), use_perplexity: bool = Query(False)):
    try:
        vid = extract_video_id(youtube_url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return _do_extraction(vid, write_files=write_files, use_perplexity=use_perplexity)


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
    <html><body>
    <h3>YouTube Transcript Extractor (fixed)</h3>
    <p>Paste a YouTube URL or video id and click Start (uses async endpoint).</p>
    <input id="url" style="width:60%" placeholder="video id or URL"/>
    <label><input id="wf" type="checkbox" checked/> write files</label>
    <button onclick="start()">Start</button>
    <div id="out"></div>
    <script>
    async function start(){
      const v=document.getElementById('url').value;
      const wf=document.getElementById('wf').checked;
      const r=await fetch('/extract_async?youtube_url='+encodeURIComponent(v)+'&write_files='+wf,{method:'POST'});
      const j=await r.json();
      document.getElementById('out').innerText='job: '+j.job_id;
      const id=j.job_id; setInterval(async ()=>{const s=await (await fetch('/status/'+id)).json(); if(s.status!=='running' && s.status!=='queued'){document.getElementById('out').innerText=JSON.stringify(s);}},700);
    }
    </script></body></html>
    """
    return HTMLResponse(html)
