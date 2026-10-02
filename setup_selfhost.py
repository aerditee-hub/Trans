#!/usr/bin/env python3
"""
Download Transformers.js + translation models so the site is fully self-hosted.
No pip packages needed (standard library only).

Usage (run in the same folder as translator-transformers.html):
    python setup_selfhost.py                 # default pairs: en-fr fr-en
    python setup_selfhost.py en-fr fr-en en-hi en-es es-en

Then set  SELF_HOST = true  at the top of translator-transformers.html
and serve the folder with any static host (or: python -m http.server).
"""
import json, os, sys, urllib.request

VERSION = "3.8.1"
CDN = f"https://cdn.jsdelivr.net/npm/@huggingface/transformers@{VERSION}/dist/"
LIB_FILES = ["transformers.min.js", "ort-wasm-simd-threaded.jsep.mjs", "ort-wasm-simd-threaded.jsep.wasm"]
HF = "https://huggingface.co/"
ROOT_EXT = (".json", ".spm", ".txt", ".model")
ONNX_WANTED = {"onnx/encoder_model_quantized.onnx", "onnx/decoder_model_merged_quantized.onnx"}

def fetch(url, dest):
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    if os.path.exists(dest) and os.path.getsize(dest) > 0:
        print(f"  have  {dest}")
        return
    print(f"  get   {dest}")
    req = urllib.request.Request(url, headers={"User-Agent": "setup_selfhost"})
    with urllib.request.urlopen(req) as r, open(dest, "wb") as f:
        while chunk := r.read(1 << 20):
            f.write(chunk)

def main():
    pairs = sys.argv[1:] or ["en-fr", "fr-en"]
    print("Library files -> lib/")
    for name in LIB_FILES:
        fetch(CDN + name, os.path.join("lib", name))

    for pair in pairs:
        repo = f"Xenova/opus-mt-{pair}"
        print(f"\nModel {repo} -> models/{repo}/")
        try:
            with urllib.request.urlopen(f"{HF}api/models/{repo}") as r:
                files = [s["rfilename"] for s in json.load(r)["siblings"]]
        except Exception as e:
            print(f"  !! couldn't list {repo} ({e}) - that pair may not exist, skipping")
            continue
        wanted = [f for f in files if ("/" not in f and f.endswith(ROOT_EXT)) or f in ONNX_WANTED]
        if not any(f.startswith("onnx/") for f in wanted):
            print("  !! quantized ONNX files not found, skipping")
            continue
        for f in wanted:
            fetch(f"{HF}{repo}/resolve/main/{f}", os.path.join("models", repo, f))

    print("\nDone. Now set SELF_HOST = true in translator-transformers.html and serve this folder.")

if __name__ == "__main__":
    main()
