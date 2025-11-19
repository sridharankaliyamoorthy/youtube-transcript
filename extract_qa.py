"""
Extract question-answer pairs from `transcript.txt`.

Heuristic:
- Detect question candidates (same rules as `extract_questions.py`).
- For each detected question, collect the following 1-6 non-empty lines as an answer
  until another question is detected or a reasonable max length is reached.

Output: `qa.txt` with Q/A pairs in plain text.
"""

from pathlib import Path
import re

QUESTION_STARTS = [
    "who","what","when","where","why","how","which","whom","whose",
    "is","are","was","were","do","does","did","can","could","would",
    "should","will","have","has","had",
]

def looks_like_question(text: str) -> bool:
    if not text:
        return False
    s = text.strip()
    if "?" in s:
        return True
    s_low = s.lower()
    for q in QUESTION_STARTS:
        if s_low.startswith(q + " ") or s_low.startswith(q + "'"):
            return True
    first_words = s_low.split()[:6]
    for w in first_words:
        if w in ("who","what","when","where","why","how","which"):
            return True
    return False


def normalize(s: str) -> str:
    return re.sub(r"\s+", " ", s.strip())


def extract_qa(transcript_path: Path, output_path: Path):
    text = transcript_path.read_text(encoding="utf-8")
    lines = [ln.strip() for ln in text.splitlines()]
    # collapse consecutive blank lines
    lines = [ln for ln in lines]

    qa_pairs = []
    i = 0
    n = len(lines)
    while i < n:
        if not lines[i]:
            i += 1
            continue

        # try to build a question candidate (up to 3 lines)
        if looks_like_question(lines[i]):
            q = lines[i]
            j = i + 1
            # try to expand question if following lines don't look like answer start
            while j < n and j < i + 3 and not looks_like_question(lines[j]) and len(q) < 120:
                if lines[j]:
                    q = q + " " + lines[j]
                j += 1

            # gather answer: take next up to 6 lines until next question or blank
            ans_parts = []
            k = j
            while k < n and len(ans_parts) < 6 and not looks_like_question(lines[k]):
                if lines[k]:
                    ans_parts.append(lines[k])
                k += 1

            answer = " ".join(ans_parts).strip()
            if not answer:
                # fallback: if there was nothing, take the next non-empty line (if any)
                m = j
                while m < n and not lines[m]:
                    m += 1
                if m < n:
                    answer = lines[m]

            qa_pairs.append((normalize(q.rstrip('?') + '?'), normalize(answer)))
            i = k
            continue

        # check 2-line combined question
        combined2 = (lines[i] + " " + lines[i+1]).strip() if i+1 < n else ""
        combined3 = (combined2 + " " + lines[i+2]).strip() if i+2 < n else ""
        if looks_like_question(combined2):
            q = combined2
            j = i+2
            ans_parts = []
            k = j
            while k < n and len(ans_parts) < 6 and not looks_like_question(lines[k]):
                if lines[k]:
                    ans_parts.append(lines[k])
                k += 1
            answer = " ".join(ans_parts).strip()
            qa_pairs.append((normalize(q.rstrip('?') + '?'), normalize(answer)))
            i = k
            continue
        if looks_like_question(combined3):
            q = combined3
            j = i+3
            ans_parts = []
            k = j
            while k < n and len(ans_parts) < 6 and not looks_like_question(lines[k]):
                if lines[k]:
                    ans_parts.append(lines[k])
                k += 1
            answer = " ".join(ans_parts).strip()
            qa_pairs.append((normalize(q.rstrip('?') + '?'), normalize(answer)))
            i = k
            continue

        i += 1

    # write to output
    out_lines = []
    for idx, (q, a) in enumerate(qa_pairs, start=1):
        out_lines.append(f"Q{idx}: {q}")
        out_lines.append(f"A{idx}: {a if a else '[No answer found]'}")
        out_lines.append("")

    output_path.write_text("\n".join(out_lines), encoding="utf-8")
    return len(qa_pairs)


if __name__ == "__main__":
    tpath = Path("transcript.txt")
    out = Path("qa.txt")
    if not tpath.exists():
        print("transcript.txt not found — run the transcript script first")
    else:
        count = extract_qa(tpath, out)
        print(f"Wrote {out} with {count} Q/A pairs ({out.stat().st_size} bytes)")
