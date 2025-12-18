#!/usr/bin/env python3

import argparse
import base64
import sys
from pathlib import Path

import requests

DEFAULT_MODEL = "deepseek-ocr:latest"
OLLAMA_GENERATE_URL = "http://localhost:11434/api/generate"

PROMPT = """You are an OCR transcription agent.

Task:
Transcribe ALL visible text from the image into plain text.

Rules:
Do not summarize.
Do not rewrite.
Do not correct grammar.
Do not infer missing text.
Preserve paragraph breaks.
Preserve line breaks where they exist.
If a word is unreadable, write [unclear].
Output only the transcription text.
"""

def image_to_b64(path: Path) -> str:
    return base64.b64encode(path.read_bytes()).decode("utf-8")

def ollama_ocr(model: str, image_path: Path, timeout_s: int) -> str:
    payload = {
        "model": model,
        "prompt": PROMPT,
        "stream": False,
        "images": [image_to_b64(image_path)],
    }

    resp = requests.post(OLLAMA_GENERATE_URL, json=payload, timeout=timeout_s)
    if resp.status_code != 200:
        raise RuntimeError(f"Ollama returned HTTP {resp.status_code}: {resp.text}")

    data = resp.json()
    if "error" in data and data["error"]:
        raise RuntimeError(f"Ollama error: {data['error']}")

    text = data.get("response", "")
    return text.strip()

def main():
    parser = argparse.ArgumentParser(description="One off AI OCR CLI using Ollama vision models")
    parser.add_argument("images", nargs="+", help="Image files to OCR")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Ollama model name")
    parser.add_argument("--out", default="ai_ocr_output", help="Output directory")
    parser.add_argument("--timeout", type=int, default=900, help="Request timeout seconds")
    args = parser.parse_args()

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    for p in args.images:
        img = Path(p)
        if not img.exists():
            print(f"Missing file: {img}", file=sys.stderr)
            continue

        print(f"OCR AI: {img.name}  model: {args.model}")

        try:
            text = ollama_ocr(args.model, img, args.timeout)
        except Exception as e:
            print(f"ERROR: {img.name}: {e}", file=sys.stderr)
            continue

        out_path = out_dir / f"{img.stem}.txt"
        out_path.write_text(text, encoding="utf-8")
        print(f"Saved: {out_path}")

if __name__ == "__main__":
    main()
