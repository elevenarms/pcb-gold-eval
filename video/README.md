# Explainer video

`site/assets/video/explainer.mp4` is about 2:34, 1920×1080 at 30 fps, H.264 video with AAC audio, normalised to −16 LUFS. `poster.jpg` is its cover frame. The video follows the Rauchwerk Research house style.

## Rebuild

```sh
uv run -q --python 3.12 --with kokoro-onnx==0.4.9 --with soundfile python video/tts.py   # narration -> video/vo/*.wav
node video/capture3d.mjs                                                               # 3D clips from site/ -> video/clips/*.mp4
node video/stills.mjs                                                                  # frames.html -> video/stills/*.png
python3 -I video/assemble.py                                                           # -> site/assets/video/explainer.mp4 + poster.jpg
```

Suggested root `Makefile` target:

```make
video:            ## explainer video -> site/assets/video/explainer.mp4
	uv run -q --python 3.12 --with kokoro-onnx==0.4.9 --with soundfile python video/tts.py
	node video/capture3d.mjs && node video/stills.mjs && python3 -I video/assemble.py
```

## What is pinned

- **Script:** `script.json` holds the narration text, scene and segment layout, clip settings and the voice choice.
- **Voice:** Kokoro-82M v1.0 (open weights, Apache-2.0), run locally through `kokoro-onnx==0.4.9` with voice `am_michael` at speed 1.0.
  - The model files are downloaded from the kokoro-onnx `model-files-v1.0` release and checked against the sha256 values in `script.json`.
  - Spoken respellings, such as "Rowshwerk" and "D-D-R-five", are listed under `kokoro.say`. They affect the audio only; on screen the words are always written normally.
  - The ElevenLabs "Eric" voice block is kept for reference only. Its credits were exhausted on 2026-11-07.
- **3D footage:** recorded from the project page through its URL API (`?board=…&mode=…&autorotate=1&ui=0`). Playwright's fake clock drives `requestAnimationFrame`, so the frames come out the same on every run.
  - Frames are captured at 2880×1620, then centre-cropped and scaled to 1920×1080 using each clip's `zoom` setting.
- **Timing:** every scene is 0.5 s lead-in, then the narration, then a 0.8 s tail. Chapter cards last 2.5 s and the end card holds an extra 2 s. All cuts are 0.3 s cross-fades.
- **Encode:** the final pass uses CRF 24, preset slow, to keep the file under 40 MB. Audio gets a two-pass loudnorm to I=−16, TP=−1.5.

## Large local files

These are rebuilt by the scripts above and should not be committed:

- `models/` (342 MB)
- `clips/` (about 100 MB)
- `vo/` (12 MB)
- `stills/`
- `build/`
