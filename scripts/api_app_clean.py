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

app = FastAPI(title="YouTube Transcript Tools (clean)")

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
    lines = get_transcript_from_video_id(video_id)
    if not write_files:
        joined = "\n".join(lines)
        try:
            questions = extract_questions_from_text(joined)
        except Exception:
            questions = []
        try:
            qa_pairs = extract_qa_advanced(lines, questions=questions)
        except Exception:
            qa_pairs = []
        p = None
        if use_perplexity:
            try:
                p = perplexity_summarize(joined)
            except Exception:
                p = None
        return {"status":"ok","video_id":video_id,"transcript":lines,"questions":questions,"qa_pairs":qa_pairs,"perplexity_summary":p}

    out = OUT_DIR
    transcript_path = out / f"{video_id}_transcript.txt"
    transcript_path.write_text("\n".join(lines), encoding="utf-8")

    qa_path = out / f"{video_id}_qa.txt"
    try:
        qa_pairs = extract_qa_advanced(lines)
        with qa_path.open('w', encoding='utf-8') as fh:
            for i, p in enumerate(qa_pairs, 1):
                fh.write(f"Q{i}: {p.get('q','')}\nA{i}: {p.get('a','')}\n\n")
        qa_count = len(qa_pairs)
    except Exception:
        qa_count = 0

    questions_path = out / f"{video_id}_questions.txt"
    try:
        questions_count = 0
        # fallback simple extractor
        qlist = extract_questions_from_text("\n".join(lines))
        questions_path.write_text("\n".join(qlist), encoding='utf-8')
        questions_count = len(qlist)
    except Exception:
        questions_count = 0

    summary_path = out / f"{video_id}_summary.txt"
    summary_path.write_text(f"Video: {video_id}\nLines: {len(lines)}\nQA: {qa_count}\nQuestions: {questions_count}\n", encoding='utf-8')

    per_path = None
    if use_perplexity:
        try:
            per = perplexity_summarize("\n".join(lines))
            per_path = out / f"{video_id}_perplexity_summary.txt"
            per_path.write_text(per or "", encoding='utf-8')
        except Exception:
            per_path = None

    return {"status":"ok","video_id":video_id,"transcript_path":str(transcript_path),"qa_path":str(qa_path),"questions_path":str(questions_path),"summary_path":str(summary_path),"perplexity_path":str(per_path) if per_path else None}


@app.get('/ui', response_class=HTMLResponse)
def ui():
        html = """
        <!doctype html>
        <html>
        <head>
            <meta charset="utf-8" />
            <title>YouTube Transcript Extractor (Clean UI)</title>
            <style>
                body{font-family:system-ui,Segoe UI,Roboto,Arial;margin:24px}
                input[type=text]{width:60%;padding:8px}
                button{padding:8px 12px;margin-left:8px}
                pre{background:#f6f8fa;padding:12px;border-radius:6px;white-space:pre-wrap}
                .links a{display:block;margin:6px 0}
                .small{font-size:0.9em;color:#555}
            </style>
        </head>
        <body>
            <h2>YouTube Transcript Extractor</h2>
            <p>Paste a YouTube URL or video ID below, choose options, then click <b>Start</b>.</p>

            <div>
                <input id="url" type="text" placeholder="https://youtu.be/ORrELERGIHs or ORrELERGIHs" />
                <label style="margin-left:8px"><input id="write_files" type="checkbox" checked /> Write files</label>
                <label style="margin-left:8px"><input id="use_perplexity" type="checkbox" /> Use Perplexity</label>
                <button id="start">Start</button>
            </div>

            <p class="small">Sync endpoint: <code>/extract/</code> — Async endpoint: <code>/extract_async</code></p>

            <h3>Progress</h3>
            <div id="status"><em>Idle</em></div>

            <h3>Result / Preview</h3>
            <div id="result"><em>No extraction yet.</em></div>

            <script>
                const startBtn = document.getElementById('start');
                const input = document.getElementById('url');
                const statusEl = document.getElementById('status');
                const result = document.getElementById('result');

                async function pollJob(jobId){
                    statusEl.textContent = 'Queued... polling status...';
                    while(true){
                        const r = await fetch('/status/'+jobId);
                        if(!r.ok){ statusEl.innerHTML = '<pre>Error polling job</pre>'; return }
                        const j = await r.json();
                        statusEl.textContent = 'Status: '+j.status;
                        if(j.status === 'done'){
                            const res = j.result || {};
                            const links = [];
                            if(res.transcript_path) links.push('<a href="/outputs/'+res.transcript_path.split('/').pop()+'" target="_blank">Transcript</a>');
                            if(res.qa_path) links.push('<a href="/outputs/'+res.qa_path.split('/').pop()+'" target="_blank">Q/A</a>');
                            if(res.questions_path) links.push('<a href="/outputs/'+res.questions_path.split('/').pop()+'" target="_blank">Questions</a>');
                            if(res.perplexity_path) links.push('<a href="/outputs/'+res.perplexity_path.split('/').pop()+'" target="_blank">Perplexity summary</a>');
                            if(res.summary_path) links.push('<a href="/outputs/'+res.summary_path.split('/').pop()+'" target="_blank">Summary</a>');
                            result.innerHTML = '<div>'+links.join(' | ')+'</div><hr/>'; 
                            // show preview of summary or transcript if available
                            if(res.perplexity_path){
                                const txt = await fetch('/outputs/'+res.perplexity_path.split('/').pop());
                                if(txt.ok){ result.innerHTML += '<pre>'+ (await txt.text()).slice(0, 8000) +'</pre>' }
                            } else if(res.summary_path){
                                const txt = await fetch('/outputs/'+res.summary_path.split('/').pop());
                                if(txt.ok){ result.innerHTML += '<pre>'+ (await txt.text()).slice(0, 8000) +'</pre>' }
                            }
                            return;
                        }
                        if(j.status === 'error'){
                            result.innerHTML = '<pre>Error: '+JSON.stringify(j.result)+ '</pre>';
                            return;
                        }
                        await new Promise(r => setTimeout(r, 700));
                    }
                }

                startBtn.addEventListener('click', async ()=>{
                    const v = input.value.trim();
                    const writeFiles = document.getElementById('write_files').checked;
                    const usePerp = document.getElementById('use_perplexity').checked;
                    if(!v){ result.innerHTML = '<em>Please paste a URL or video id.</em>'; return }
                    statusEl.textContent = 'Submitting job...';
                    result.innerHTML = '<em>Waiting for job to start...</em>';
                    try{
                        const url = '/extract_async?youtube_url='+encodeURIComponent(v)+'&write_files='+encodeURIComponent(writeFiles)+'&use_perplexity='+encodeURIComponent(usePerp);
                        const r = await fetch(url, {method: 'POST'});
                        if(!r.ok){ result.innerHTML = '<pre>Submission failed: '+(await r.text())+'</pre>'; return }
                        const j = await r.json();
                        statusEl.textContent = 'Job submitted: '+j.job_id;
                        pollJob(j.job_id);
                    }catch(err){ result.innerHTML = '<pre>'+err.toString()+'</pre>' }
                })
            </script>
        </body>
        </html>
        """
        return HTMLResponse(content=html)


@app.get('/extract/')
def extract(youtube_url: str = Query(...), write_files: bool = Query(True), use_perplexity: bool = Query(False)):
    try:
        vid = extract_video_id(youtube_url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    try:
        return _do_extraction(vid, write_files=write_files, use_perplexity=use_perplexity)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post('/extract_async')
def extract_async(youtube_url: str = Query(...), write_files: bool = Query(True), use_perplexity: bool = Query(False), background_tasks: BackgroundTasks = None):
    try:
        vid = extract_video_id(youtube_url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    job_id = str(uuid4())
    JOBS[job_id] = {"status":"queued","result":None}

    def _run():
        JOBS[job_id]['status'] = 'running'
        try:
            res = _do_extraction(vid, write_files=write_files, use_perplexity=use_perplexity)
            JOBS[job_id]['status'] = 'done'
            JOBS[job_id]['result'] = res
        except Exception as e:
            JOBS[job_id]['status'] = 'error'
            JOBS[job_id]['result'] = {'error': str(e)}

    if background_tasks is not None:
        background_tasks.add_task(_run)
    else:
        _run()
    return {"job_id": job_id}


@app.get('/status/{job_id}')
def status(job_id: str):
    j = JOBS.get(job_id)
    if not j:
        raise HTTPException(status_code=404, detail='not found')
    return j
