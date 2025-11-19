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
OUT_DIR = Path("output")
OUT_DIR.mkdir(exist_ok=True)
app.mount("/output", StaticFiles(directory=str(OUT_DIR)), name="output")

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



import subprocess
def get_video_title(video_id: str) -> str:
    try:
        # yt-dlp --get-title https://www.youtube.com/watch?v=VIDEOID
        url = f"https://www.youtube.com/watch?v={video_id}"
        result = subprocess.run(["yt-dlp", "--get-title", url], capture_output=True, text=True, timeout=15)
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return "Unknown Title"

def _do_extraction(video_id: str, write_files: bool = True, use_perplexity: bool = False):
    transcript_lines = get_transcript_from_video_id(video_id)
    joined = "\n".join(transcript_lines)
    title = get_video_title(video_id)
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
        with transcript_path.open("w", encoding="utf-8") as fh:
            fh.write(f"Title: {title}\nVideo ID: {video_id}\n\n")
            fh.write(joined)
        summary_path = out / f"{video_id}_summary.txt"
        summary_path.write_text(f"Title: {title}\nVideo ID: {video_id}\nLines: {len(transcript_lines)}\n", encoding="utf-8")
        return {"status": "ok", "video_id": video_id, "title": title, "transcript_path": str(transcript_path), "summary_path": str(summary_path), "transcript": joined}

    return {"status": "ok", "video_id": video_id, "title": title, "transcript_count": len(transcript_lines), "questions": questions, "qa_pairs": qa_pairs, "transcript": joined}


@app.get("/")
def root():
    return {"message": "YouTube Transcript API (repaired)"}


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
        <html>
        <head><title>YouTube Transcript Extractor (repaired)</title></head>
        <body>
        <h2>YouTube Transcript Extractor (repaired)</h2>
        <input id='url' style='width:600px' value='https://www.youtube.com/watch?v=VKgOh0KjSM'>
        <button onclick='go()'>Extract</button>
        <div id='result'></div>
        <p>Use the /status/{job_id} endpoint to poll results.</p>
        <script>
        function extractVideoId(url) {
            var m = url.match(/[?&]v=([\w-]{11})/);
            if (m) return m[1];
            m = url.match(/youtu\.be\/([\w-]{11})/);
            if (m) return m[1];
            m = url.match(/embed\/([\w-]{11})/);
            if (m) return m[1];
            if (/^[\w-]{11}$/.test(url)) return url;
            return null;
        }
        async function go() {
            var url = document.getElementById('url').value.trim();
            var vid = extractVideoId(url);
            if (!vid) {
            alert('Could not extract video id from URL!');
            return;
            }
            let resp = await fetch('/extract/', {
            method: 'GET',
            headers: {'Accept': 'application/json'},
            credentials: 'same-origin',
            cache: 'no-cache',
            redirect: 'follow',
            referrerPolicy: 'no-referrer',
            mode: 'cors',
            // params via URL
            } + '?youtube_url=' + encodeURIComponent(vid) + '&write_files=true');
            let data = await resp.json();
            let resultDiv = document.getElementById('result');
            resultDiv.innerHTML = `<h3>Title: ${data.title}</h3><pre>${data.transcript}</pre>
            <a href="/output/${vid}_transcript.txt" download>Download transcript file</a>`;
        }
        </script>
        </body>
        </html>
    """
    return HTMLResponse(content=html)
