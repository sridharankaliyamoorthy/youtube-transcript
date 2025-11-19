"""Advanced QA helper: optional spaCy sentence segmentation and optional
sentence-transformers embeddings to select best answer sentences for
detected questions.

This module is optional — it falls back to simple heuristics when
dependencies are unavailable.
"""
from typing import List, Dict, Optional

try:
    import spacy
    from spacy.lang.en import English
    SPACY_AVAILABLE = True
except Exception:
    spacy = None
    SPACY_AVAILABLE = False

try:
    from sentence_transformers import SentenceTransformer, util
    EMBED_AVAILABLE = True
except Exception:
    SentenceTransformer = None
    util = None
    EMBED_AVAILABLE = False

# cache model instances to avoid re-loading on each call
_EMBED_MODEL = None
_SPACY_NLP = None

def _segment_sentences(text: str) -> List[str]:
    global _SPACY_NLP
    if SPACY_AVAILABLE:
        try:
            if _SPACY_NLP is None:
                try:
                    _SPACY_NLP = spacy.load("en_core_web_sm")
                except Exception:
                    _SPACY_NLP = English()
                    _SPACY_NLP.add_pipe("sentencizer")
            doc = _SPACY_NLP(text)
            return [sent.text.strip() for sent in doc.sents if sent.text.strip()]
        except Exception:
            pass
    # fallback: split on newlines and punctuation heuristically
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    # further split long lines at sentence enders
    out = []
    for l in lines:
        parts = [p.strip() for p in l.replace('?', '.?').split('.') if p.strip()]
        out.extend(parts)
    return out

def extract_qa_advanced(transcript_lines: List[str], questions: Optional[List[str]] = None, max_answer_sentences: int = 3) -> List[Dict[str, str]]:
    """Return list of {q, a, score} for provided transcript lines.

    If `questions` is None, the caller should have detected questions already
    (e.g., via yt_transcript_tools.question_extractor.extract_questions);
    otherwise we cannot reliably detect them here.
    """
    text = "\n".join(transcript_lines)
    sents = _segment_sentences(text)
    if not questions:
        # fallback: look for sentences containing question mark
        questions = [s for s in sents if s.endswith('?')][:100]

    # If embeddings are available, compute embeddings and pick best candidate
    if EMBED_AVAILABLE and SentenceTransformer is not None:
        try:
            global _EMBED_MODEL
            if _EMBED_MODEL is None:
                _EMBED_MODEL = SentenceTransformer('all-MiniLM-L6-v2')
            model = _EMBED_MODEL
            # embed questions and sentences
            q_emb = model.encode(questions, convert_to_tensor=True)
            s_emb = model.encode(sents, convert_to_tensor=True)
            results = []
            for qi, q in enumerate(questions):
                # compute cosine similarities
                sims = util.cos_sim(q_emb[qi], s_emb)[0].tolist()
                # consider only sentences after the question occurrence to prefer nearby answers
                # find first sentence index that matches the question text
                try:
                    q_idx = next(i for i, s in enumerate(sents) if q.strip().lower() in s.strip().lower())
                except StopIteration:
                    q_idx = None
                # candidate sentences: those within next max_answer_sentences*2 window
                candidates = list(range(len(sims)))
                if q_idx is not None:
                    candidates = [i for i in range(q_idx+1, min(len(sims), q_idx+1+max_answer_sentences*2))]
                    if not candidates:
                        candidates = list(range(len(sims)))
                # pick highest similarity among candidates
                best_i = max(candidates, key=lambda i: sims[i])
                best_score = sims[best_i]
                answer = sents[best_i]
                results.append({"q": q, "a": answer, "score": float(best_score)})
            return results
        except Exception:
            # fall through to heuristic fallback
            pass

    # fallback heuristic: for each question, find its index and take next N sentences
    results = []
    for q in questions:
        try:
            q_idx = next(i for i, s in enumerate(sents) if q.strip().lower() in s.strip().lower())
        except StopIteration:
            q_idx = None
        ans = ""
        if q_idx is not None:
            start = q_idx + 1
            end = min(len(sents), start + max_answer_sentences)
            ans = " ".join(sents[start:end])
        results.append({"q": q, "a": ans, "score": 0.0})
    return results
