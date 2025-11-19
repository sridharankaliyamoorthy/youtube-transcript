import textwrap
from yt_transcript_tools import extractors


def test_looks_like_question():
    assert extractors.looks_like_question("What is Python")
    assert extractors.looks_like_question("how do I test this")
    assert extractors.looks_like_question("Is this right?")
    assert not extractors.looks_like_question("This is a statement")


def test_extract_questions_from_lines():
    lines = [
        "what is a module",
        "it is a single python file",
        "how to install python",
        "use the official installer",
        "this is not a question",
    ]
    qs = extractors.extract_questions_from_lines(lines)
    assert any("what is a module" in q.lower() for q in qs)
    assert any("how to install python" in q.lower() for q in qs)


def test_extract_qa_roundtrip(tmp_path):
    sample = textwrap.dedent(
        """
        What is X
        X is a thing that does Y

        How do you run it
        You run it with a command
        """
    )
    p = tmp_path / "transcript.txt"
    p.write_text(sample)
    out = tmp_path / "qa.txt"
    count = extractors.extract_qa(p, out)
    assert count >= 1
    s = out.read_text()
    assert "What is X" in s or "How do you run it" in s
