#!/usr/bin/env python3
"""CLI wrapper to extract questions from a transcript file."""
import argparse
from pathlib import Path
from yt_transcript_tools.extractors import extract_questions


def main():
    p = argparse.ArgumentParser(description="Extract questions from transcript.txt")
    p.add_argument("input", nargs="?", default="transcript.txt", help="Transcript input file")
    p.add_argument("-o", "--output", default="questions.txt", help="Output file for questions")
    args = p.parse_args()
    count = extract_questions(Path(args.input), Path(args.output))
    print(f"Wrote {args.output} ({count} questions)")


if __name__ == "__main__":
    main()
