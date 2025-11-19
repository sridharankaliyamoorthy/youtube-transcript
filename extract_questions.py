"""
Read `transcript.txt` and write detected questions to `questions.txt`.

This uses a heuristic because automatic transcripts are often split into
short fragments and may not include punctuation. The script looks for:
- any snippet containing a literal question mark `?`
- snippets that start with interrogative words (who/what/when/where/why/how/which)
- snippets that start with auxiliary verbs commonly used in questions (is/are/do/does/can/will/etc.)

When a question looks like it spans multiple transcript lines, the script will
combine up to 3 consecutive lines to form a single question candidate.
"""

from pathlib import Path
import re

QUESTION_STARTS = [
    "who",
    "what",
    "when",
    "where",
    "why",
    "how",
    "which",
    "whom",
    "whose",
    # auxiliaries
    "is",
    "are",
    "was",
    "were",
    "do",
    "does",
    "did",
    "can",
    "could",
    "would",
    "should",
    "will",
    "have",
    "has",
    "had",
]

def looks_like_question(text: str) -> bool:
    if not text:
        return False
    s = text.strip()
    # if there is an explicit question mark
    if "?" in s:
        return True
    # normalize for checking start words
    s_low = s.lower()
    # check if it starts with a question word or auxiliary
    for q in QUESTION_STARTS:
        if s_low.startswith(q + " ") or s_low.startswith(q + "'"):
            return True
    # check for short phrases that look like questions, e.g., "any idea" or "right?" is hard to catch
    # fallback: if the line contains a question word anywhere near the beginning (first 6 words)
    first_words = s_low.split()[:6]
    for w in first_words:
        if w in ("who","what","when","where","why","how","which"):
            return True
    return False


def extract_questions(input_path: Path, output_path: Path):
    lines = [ln.strip() for ln in input_path.read_text(encoding="utf-8").splitlines()]
    n = len(lines)
    i = 0
    questions = []
    while i < n:
        if not lines[i]:
            i += 1
            continue

        # Try single-line candidate
        if looks_like_question(lines[i]):
            # try to expand up to 3 lines if the question seems incomplete
            combined = lines[i]
            j = i + 1
            # expand while the combined text is short and next line doesn't look like a new question
            while j < n and j < i + 3 and len(combined) < 120 and not looks_like_question(lines[j]):
                if lines[j]:
                    combined = combined + " " + lines[j]
                j += 1
            # ensure it ends with a question mark for readability
            candidate = combined.strip()
            if not candidate.endswith("?"):
                candidate = candidate + "?"
            questions.append(candidate)
            # skip the lines we've consumed
            i = j
            continue

        # If the current line isn't clearly a question, but the next 2 lines together might form one,
        # check combined windows of 2 and 3 lines.
        combined2 = (lines[i] + " " + lines[i+1]).strip() if i+1 < n else ""
        combined3 = (combined2 + " " + lines[i+2]).strip() if i+2 < n else ""
        if looks_like_question(combined2):
            candidate = combined2
            if not candidate.endswith("?"):
                candidate = candidate + "?"
            questions.append(candidate)
            i += 2
            continue
        if looks_like_question(combined3):
            candidate = combined3
            if not candidate.endswith("?"):
                candidate = candidate + "?"
            questions.append(candidate)
            i += 3
            continue

        i += 1

    # dedupe while preserving order
    seen = set()
    deduped = []
    for q in questions:
        q_norm = re.sub(r"\s+", " ", q.strip().lower())
        if q_norm not in seen:
            seen.add(q_norm)
            deduped.append(q.strip())

    output_path.write_text("\n".join(deduped) + ("\n" if deduped else ""), encoding="utf-8")


if __name__ == "__main__":
    in_path = Path("transcript.txt")
    out_path = Path("questions.txt")
    if not in_path.exists():
        print(f"Input file {in_path} not found. Run the transcript fetcher first.")
    else:
        extract_questions(in_path, out_path)
        print(f"Wrote {out_path} ({out_path.stat().st_size} bytes)")
