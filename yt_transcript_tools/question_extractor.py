from typing import List
import re


def _load_spacy():
    try:
        import spacy

        # try to load the small English model
        try:
            nlp = spacy.load("en_core_web_sm")
        except Exception:
            # fallback: try spacy.blank
            nlp = spacy.blank("en")
        return nlp
    except Exception:
        return None


_NLP = _load_spacy()


def extract_questions(text: str) -> List[str]:
    """Extract question-like sentences from `text`.

    If spaCy with sentence segmentation is available it will be used, otherwise
    a simple regex-based sentence splitter and heuristics are used.
    """
    if not text:
        return []

    interrogatives = {"what", "why", "how", "when", "where", "who", "which", "whom", "whose"}

    def looks_like_question_sentence(s: str) -> bool:
        s = s.strip()
        if not s:
            return False
        if "?" in s:
            return True
        first = s.split()[0].lower() if s.split() else ""
        if first in interrogatives:
            return True
        # auxiliaries
        if first in {"is", "are", "do", "does", "did", "can", "could", "would", "should", "will", "have", "has", "had"}:
            return True
        return False

    sentences = []
    if _NLP is not None:
        doc = _NLP(text)
        for sent in doc.sents:
            sentences.append(sent.text.strip())
    else:
        # naive sentence split on punctuation followed by whitespace/newline
        parts = re.split(r"(?<=[\.\!\?])\s+", text)
        sentences = [p.strip() for p in parts if p.strip()]

    questions = [s for s in sentences if looks_like_question_sentence(s)]
    return questions
