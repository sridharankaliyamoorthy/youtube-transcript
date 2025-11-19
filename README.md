# YouTube Transcript Extractor

A FastAPI web app and Python script to extract YouTube video transcripts, save them with video titles, and provide a browser UI for easy use.

## Features
- Paste any YouTube URL or video ID in the browser UI or script
- Transcript saved in `output/` folder, with video title at the top
- Download transcript files from the UI
- Supports manual and async extraction

## Quick Start (Web UI)
1. Install dependencies:
  ```bash
  pip install -r requirements.txt
  pip install yt-dlp
  ```
2. Start the server:
  ```bash
  uvicorn scripts.api_app:app --reload --port 8000
  ```
3. Open [http://127.0.0.1:8000/ui](http://127.0.0.1:8000/ui) in your browser
4. Paste a YouTube URL and click Extract

## Quick Start (Script)
1. Run:
  ```bash
  python3 youtube_transcript.py
  ```
2. Paste a YouTube URL or video id when prompted

## Output
- All transcript files are saved in the `output/` folder
- Each transcript file starts with the video title and video id

## Requirements
- Python 3.8+
- `youtube-transcript-api`
- `yt-dlp` (for video title)
- `fastapi`, `uvicorn`

## Project Structure
```
output/                # All transcript and summary files
scripts/api_app.py     # FastAPI backend
youtube_transcript.py  # CLI script for transcript extraction
yt_transcript_tools/   # Extraction logic
requirements.txt       # Python dependencies
Dockerfile             # For container deployment
README.md              # This file
```

## License
MIT
Your repo is looking good for a first project—it has all key files!  
To make it look **more professional and inviting**, here are some quick improvements:

***

**1. Polish your README.md**
- Add a project description, features, setup instructions, and example usage.
- Use Markdown headers, code blocks, bulleted lists.

**Example README.md:**
```markdown
# YouTube Transcript Extractor

A Python project to download YouTube video transcripts and extract question sentences.

## Features
- Download subtitles/transcripts from any YouTube video (no API key required!)
- Extract questions from transcripts (lines containing “?” or starting with question words)

## Setup

1. Clone this repo:
   ```
   git clone https://github.com/sridharankaliyamoorthy/youtube-transcript.git
   cd youtube-transcript
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage

Fetch the transcript:
```
python test_transcript.py
```

Extract questions:
```
python extract_questions.py
```

## Requirements

See `requirements.txt`.

## License
MIT License
```

***

**2. Add a .gitignore**
- Create a file called `.gitignore` to avoid committing unwanted files:
  ```
  __pycache__/
  *.pyc
  .venv/
  ```

***

**3. Optional: Add comments and docstrings to your Python scripts**
- Make your code easier to understand for others (and future you).

**Example:**
```python
"""
Extracts questions from a transcript file.
"""

with open("transcript.txt", "r", encoding="utf-8") as infile, open("questions.txt", "w", encoding="utf-8") as outfile:
    for line in infile:
        if "?" in line.strip():
            outfile.write(line)
```

***

**Next steps:**
- Edit your README.md in VS Code and push the changes (`git add README.md; git commit -m "Improve docs"; git push`).
- Add `.gitignore` as above.

Let me know if you want even more pro tips (badges, screenshots, etc.) or if you want a template for larger open-source projects!

[1](https://github.com/jdepoix/youtube-transcript-api)