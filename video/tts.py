#!/usr/bin/env python3
"""Render every narration line of video/script.json to video/vo/<id>.wav.

Provider: Kokoro-82M (open weights, Apache-2.0) via kokoro-onnx, run locally -- no API key, fully reproducible.
Model files are pinned by sha256 (see MODELS); `--provider elevenlabs` uses the voice block in script.json instead
(needs ELEVENLABS_API_KEY and credits).
Usage: uv run -q --python 3.12 --with kokoro-onnx==0.4.9 --with soundfile python video/tts.py [--force] [--provider elevenlabs]"""
import hashlib, json, os, subprocess, sys, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
S = json.load(open(os.path.join(HERE, "script.json")))
OUT = os.path.join(HERE, "vo")
os.makedirs(OUT, exist_ok=True)
force = "--force" in sys.argv
provider = sys.argv[sys.argv.index("--provider") + 1] if "--provider" in sys.argv else "kokoro"
K = S["kokoro"]
MODELS = {f: (f"{K['release']}/{f}", sha) for f, sha in K["files"].items()}


def lines():
    out = []
    for sc in S["scenes"]:
        for p in sc.get("vo_parts", []):
            out.append({"id": p["id"], "text": p["text"], "pron": p.get("pron", False)})
        if "vo" in sc:
            out.append({"id": sc["id"], "text": sc["vo"], "pron": False})
    return out


def tts_text(ln):
    # spoken spellings only (on screen the words are always written normally)
    t = ln["text"].replace(S["pronunciation_token"], K["rauchwerk"])
    for a, b in K.get("say", {}).items():
        t = t.replace(a, b)
    return t


def ensure_models():
    d = os.path.join(HERE, "models")
    os.makedirs(d, exist_ok=True)
    for f, (url, sha) in MODELS.items():
        p = os.path.join(d, f)
        if not os.path.exists(p) or hashlib.sha256(open(p, "rb").read()).hexdigest() != sha:
            urllib.request.urlretrieve(url, p)
            assert hashlib.sha256(open(p, "rb").read()).hexdigest() == sha, f"{f}: sha256 mismatch"
    return os.path.join(d, "kokoro-v1.0.onnx"), os.path.join(d, "voices-v1.0.bin")


def trim(src, wav):
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", src, "-af",
                    "silenceremove=start_periods=1:start_threshold=-45dB,areverse,silenceremove=start_periods=1:start_threshold=-45dB,areverse",
                    "-ar", "48000", "-ac", "1", wav], check=True)


L, chars = lines(), 0
kok = None
for ln in L:
    wav = os.path.join(OUT, ln["id"] + ".wav")
    if force or not os.path.exists(wav):
        text = tts_text(ln)
        chars += len(text)
        tmp = wav[:-4] + ".raw.wav"
        if provider == "kokoro":
            if kok is None:
                from kokoro_onnx import Kokoro
                import soundfile as sf
                kok = Kokoro(*ensure_models())
            a, sr = kok.create(text, voice=K["voice"], speed=K["speed"], lang="en-us")
            sf.write(tmp, a, sr)
        else:
            raise SystemExit("elevenlabs provider: see ~/Code/crusoe/video/rr/tts_rr.py (credits were exhausted on 2026-11-07)")
        trim(tmp, wav)
        os.remove(tmp)
    d = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", wav], capture_output=True, text=True).stdout)
    print(f"{ln['id']:5s} {d:5.2f}s  {ln['text'][:70]}")
print("characters synthesised:", chars)
