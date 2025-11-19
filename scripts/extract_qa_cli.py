#!/usr/bin/env python3
"""CLI wrapper to extract Q/A pairs from a transcript file."""
import argparse
from pathlib import Path
from yt_transcript_tools.extractors import extract_qa


def main():
    p = argparse.ArgumentParser(description="Extract Q/A pairs from transcript.txt")
    p.add_argument("input", nargs="?", default="transcript.txt", help="Transcript input file")
    p.add_argument("-o", "--output", default="qa.txt", help="Output file for Q/A pairs")
    args = p.parse_args()
    count = extract_qa(Path(args.input), Path(args.output))
    print(f"Wrote {args.output} ({count} Q/A pairs)")


if __name__ == "__main__":
    main()
