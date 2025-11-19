from pathlib import Path
import re
from typing import List, Tuple

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
    if "?" in s:
        return True
    s_low = s.lower()
    for q in QUESTION_STARTS:
        if s_low.startswith(q + " ") or s_low.startswith(q + "'"):
            return True
    first_words = s_low.split()[:6]
    for w in first_words:
        if w in ("who", "what", "when", "where", "why", "how", "which"):
            return True
    return False


def extract_questions_from_lines(lines: List[str]) -> List[str]:
    """Return a list of detected question strings from `lines` (no file I/O)."""
    n = len(lines)
    i = 0
    questions: List[str] = []
    while i < n:
        if not lines[i]:
            i += 1
            continue

        if looks_like_question(lines[i]):
            combined = lines[i]
            j = i + 1
            while j < n and j < i + 3 and len(combined) < 120 and not looks_like_question(lines[j]):
                if lines[j]:
                    combined = combined + " " + lines[j]
                j += 1
            candidate = combined.strip()
            if not candidate.endswith("?"):
                candidate = candidate + "?"
            questions.append(candidate)
            i = j
            continue

        combined2 = (lines[i] + " " + lines[i + 1]).strip() if i + 1 < n else ""
        combined3 = (combined2 + " " + lines[i + 2]).strip() if i + 2 < n else ""
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
    return deduped


def extract_questions(input_path: Path, output_path: Path) -> int:
    lines = [ln.strip() for ln in input_path.read_text(encoding="utf-8").splitlines()]
    questions = extract_questions_from_lines(lines)
    output_path.write_text("\n".join(questions) + ("\n" if questions else ""), encoding="utf-8")
    return len(questions)


def extract_qa(input_path: Path, output_path: Path) -> int:
    text = input_path.read_text(encoding="utf-8")
    lines = [ln.strip() for ln in text.splitlines()]
    qa_pairs: List[Tuple[str, str]] = []
    i = 0
    n = len(lines)
    while i < n:
        if not lines[i]:
            i += 1
            continue

        if looks_like_question(lines[i]):
            q = lines[i]
            j = i + 1
            while j < n and j < i + 3 and not looks_like_question(lines[j]) and len(q) < 120:
                if lines[j]:
                    q = q + " " + lines[j]
                j += 1

            ans_parts = []
            k = j
            while k < n and len(ans_parts) < 6 and not looks_like_question(lines[k]):
                if lines[k]:
                    ans_parts.append(lines[k])
                k += 1

            answer = " ".join(ans_parts).strip()
            if not answer:
                m = j
                while m < n and not lines[m]:
                    m += 1
                if m < n:
                    answer = lines[m]

            qa_pairs.append((re.sub(r"\s+", " ", q.rstrip("?") + "?"), re.sub(r"\s+", " ", answer)))
            i = k
            continue

        combined2 = (lines[i] + " " + lines[i + 1]).strip() if i + 1 < n else ""
        combined3 = (combined2 + " " + lines[i + 2]).strip() if i + 2 < n else ""
        if looks_like_question(combined2):
            q = combined2
            j = i + 2
            ans_parts = []
            k = j
            while k < n and len(ans_parts) < 6 and not looks_like_question(lines[k]):
                if lines[k]:
                    ans_parts.append(lines[k])
                k += 1
            answer = " ".join(ans_parts).strip()
            qa_pairs.append((re.sub(r"\s+", " ", q.rstrip("?") + "?"), re.sub(r"\s+", " ", answer)))
            i = k
            continue
        if looks_like_question(combined3):
            q = combined3
            j = i + 3
            ans_parts = []
            k = j
            while k < n and len(ans_parts) < 6 and not looks_like_question(lines[k]):
                if lines[k]:
                    ans_parts.append(lines[k])
                k += 1
            answer = " ".join(ans_parts).strip()
            qa_pairs.append((re.sub(r"\s+", " ", q.rstrip("?") + "?"), re.sub(r"\s+", " ", answer)))
            i = k
            continue

        i += 1

    out_lines: List[str] = []
    for idx, (q, a) in enumerate(qa_pairs, start=1):
        out_lines.append(f"Q{idx}: {q}")
        out_lines.append(f"A{idx}: {a if a else '[No answer found]'}")
        out_lines.append("")

    output_path.write_text("\n".join(out_lines), encoding="utf-8")
    return len(qa_pairs)
