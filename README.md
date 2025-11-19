# youtube-transcript

Small utilities for fetching YouTube transcripts and extracting questions
and question/answer pairs from the transcript text.

Usage examples:

1) Fetch a transcript into `transcript.txt`:

```bash
python3 scripts/fetch_transcript.py VIDEO_ID
```

2) Extract questions:

```bash
python3 scripts/extract_questions_cli.py transcript.txt -o questions.txt
```

3) Extract Q/A pairs:

```bash
python3 scripts/extract_qa_cli.py transcript.txt -o qa.txt
```

Notes:
- The extractors use simple heuristics to find questions in the auto-generated
  transcript. They are intentionally lightweight; for higher precision you can
  integrate `spacy` or an ML-based QA model.
- `requirements.txt` lists the runtime dependency: `youtube-transcript-api`.
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