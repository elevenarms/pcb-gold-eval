#!/usr/bin/env python3
"""Assemble the explainer: stills + 3D clips + caption overlays + narration -> site/assets/video/explainer.mp4 (+ poster.jpg).

Timing: scene = 0.5 s lead + narration + 0.8 s tail (end card holds 2 s more); chapter cards 2.5 s, no narration.
Segments inside a scene split its duration by `share` (equal by default). 0.3 s cross-fades between all segments.
Narration: one adelay per line, amix, two-pass loudnorm to -16 LUFS / -1.5 dBTP.
Usage: python3 -I video/assemble.py      (needs ffmpeg; run tts.py, capture3d.mjs, stills.mjs first)"""
import json, os, re, shutil, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
S = json.load(open(os.path.join(HERE, "script.json")))
LEAD, TAIL, CHAPTER, END_HOLD, XF, FPS = 0.5, 0.8, 2.5, 2.0, 0.3, 30
OUT = os.path.join(ROOT, "site/assets/video/explainer.mp4")
BUILD = os.path.join(HERE, "build")
shutil.rmtree(BUILD, ignore_errors=True)
os.makedirs(BUILD)
os.makedirs(os.path.dirname(OUT), exist_ok=True)


def dur(p):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p], capture_output=True, text=True).stdout)


def ff(*a):
    subprocess.run(["ffmpeg", "-v", "error", "-y", *a], check=True)


vo = lambda i: os.path.join(HERE, "vo", i + ".wav")
still = lambda f: os.path.join(HERE, "stills", f + ".png")
ENC = ["-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", "-r", str(FPS)]

# 1. timeline
t, segs, audio = 0.0, [], []
for sc in S["scenes"]:
    if "chapter" in sc:
        segs.append(dict(visual="still", frame=f"chapter{sc['chapter']}", d=CHAPTER))
        t += CHAPTER
        continue
    a = t + LEAD
    if "vo_parts" in sc:
        for k, p in enumerate(sc["vo_parts"]):
            a += p.get("gap", 0) if k else 0
            audio.append((p["id"], a)); a += dur(vo(p["id"]))
    else:
        audio.append((sc["id"], a)); a += dur(vo(sc["id"]))
    d = a - t + TAIL + (END_HOLD if sc.get("end") else 0)
    shares = [g.get("share", 1 / len(sc["segments"])) for g in sc["segments"]]
    for g, sh in zip(sc["segments"], shares):
        segs.append(dict(g, d=round(d * sh, 3)))
    t += d
total = round(sum(s["d"] for s in segs), 3)

# 2. render each segment (+XF so cross-fades don't eat the timeline)
for i, s in enumerate(segs):
    L = s["d"] + (XF if i < len(segs) - 1 else 0)
    o = os.path.join(BUILD, f"seg{i:02d}.mp4")
    if s["visual"] == "still" and L > 6:   # long holds get a gentle push-in so the frame stays alive
        n = int(L * FPS)
        ff("-loop", "1", "-framerate", str(FPS), "-t", f"{L:.3f}", "-i", still(s["frame"]),
           "-vf", f"scale=3840:2160,zoompan=z='1+0.025*on/{n}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=1920x1080:fps={FPS},format=yuv420p", *ENC, o)
    elif s["visual"] == "still":
        ff("-loop", "1", "-framerate", str(FPS), "-t", f"{L:.3f}", "-i", still(s["frame"]), "-vf", "scale=1920:1080,format=yuv420p", *ENC, o)
    elif s["visual"] == "zoom":
        n = int(L * FPS)
        ff("-loop", "1", "-framerate", str(FPS), "-t", f"{L:.3f}", "-i", still(s["frame"]),
           "-vf", f"scale=3840:2160,zoompan=z='1+0.07*on/{n}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=1920x1080:fps={FPS},format=yuv420p", *ENC, o)
    else:  # 3D clip + transparent caption overlay
        clip = os.path.join(HERE, "clips", s["clip"] + ".mp4")
        assert dur(clip) >= L - 0.05, f"clip {s['clip']} ({dur(clip):.1f}s) shorter than segment ({L:.1f}s)"
        ff("-i", clip, "-loop", "1", "-i", still(s["frame"]), "-filter_complex",
           f"[1:v]format=rgba,fade=t=in:st=0.4:d=0.5:alpha=1[c];[0:v][c]overlay=0:0:shortest=1,format=yuv420p", "-t", f"{L:.3f}", *ENC, o)

# 3. cross-fade chain
inputs, fc, prev, off = [], "", "0:v", 0.0
for i in range(len(segs)):
    inputs += ["-i", os.path.join(BUILD, f"seg{i:02d}.mp4")]
for i in range(1, len(segs)):
    off += segs[i - 1]["d"]
    lab = f"x{i}"
    fc += f"[{prev}][{i}:v]xfade=transition=fade:duration={XF}:offset={off:.3f}[{lab}];"
    prev = lab
video = os.path.join(BUILD, "video.mp4")
FINAL = ["-c:v", "libx264", "-preset", "slow", "-crf", "24", "-pix_fmt", "yuv420p", "-r", str(FPS)]   # size target < 40 MB
ff(*inputs, "-filter_complex", fc.rstrip(";"), "-map", f"[{prev}]", *FINAL, "-t", f"{total:.3f}", video)

# 4. narration mix + two-pass loudnorm
args, fc = [], ""
for k, (i, a) in enumerate(audio):
    args += ["-i", vo(i)]
    fc += f"[{k}:a]aformat=sample_rates=48000:channel_layouts=mono,adelay={int(a * 1000)}:all=1[a{k}];"
fc += "".join(f"[a{k}]" for k in range(len(audio))) + f"amix=inputs={len(audio)}:normalize=0:dropout_transition=0,apad=whole_dur={total},atrim=0:{total}[m]"
mix = os.path.join(BUILD, "mix.wav")
ff(*args, "-filter_complex", fc, "-map", "[m]", "-ac", "2", "-ar", "48000", mix)
LN = "loudnorm=I=-16:TP=-1.5:LRA=7"
r = subprocess.run(["ffmpeg", "-hide_banner", "-i", mix, "-af", LN + ":print_format=json", "-f", "null", "-"], capture_output=True, text=True).stderr
m = json.loads(re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", r, re.S).group(0))
ln2 = f"{LN}:measured_I={m['input_i']}:measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true"

# 5. mux
ff("-i", video, "-i", mix, "-filter_complex", f"[1:a]{ln2},aresample=48000[a]", "-map", "0:v", "-map", "[a]", "-c:v", "copy",
   "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", "-t", f"{total:.3f}", OUT)
ff("-ss", "1.5", "-i", os.path.join(BUILD, "seg01.mp4"), "-frames:v", "1", "-q:v", "3", os.path.join(os.path.dirname(OUT), "poster.jpg"))
json.dump(dict(total=total, segments=segs, audio=audio), open(os.path.join(HERE, "timeline.json"), "w"), indent=1)
print(f"wrote {OUT}  {total:.1f}s  {os.path.getsize(OUT) / 1e6:.1f} MB")
