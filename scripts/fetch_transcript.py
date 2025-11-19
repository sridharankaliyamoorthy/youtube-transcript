#!/usr/bin/env python3
"""CLI wrapper to fetch a YouTube transcript and save to a file."""
import argparse
from pathlib import Path
from yt_transcript_tools.fetcher import fetch_transcript


def main():
    p = argparse.ArgumentParser(description="Fetch YouTube transcript to a text file")
    p.add_argument("video_id", help="YouTube video ID (not full URL)")
    p.add_argument("-o", "--output", default="transcript.txt", help="Output path")
    args = p.parse_args()
    out = fetch_transcript(args.video_id, args.output)
    print(f"Wrote transcript to {out}")


if __name__ == "__main__":
    main()
