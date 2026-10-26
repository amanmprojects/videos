"""Render the explainer. Run from the video folder (the parent of src/).

  python3 src/render.py preview [scene ...]   # PNG at the end of every beat -> build/preview/
  python3 src/render.py                       # full video -> <folder-name>.mp4 + .srt
"""
import json
import math
import multiprocessing as mp
import os
import re
import subprocess
import sys
import wave

import cairo

sys.path.insert(0, os.path.dirname(__file__))
import gfx  # noqa: E402
from gfx import (AMBER, BG, FPS, H, MONO, MUTED, SANS, STROKE, W, color, eo, prog,  # noqa: E402
                 text)
from scenes import DRAW, Timing  # noqa: E402
from script import SCENES, layout  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUILD = os.path.join(ROOT, "build")
OUT = os.path.join(ROOT, os.path.basename(ROOT) + ".mp4")
FADE = 0.35


def load_plan():
    timing = json.load(open(os.path.join(BUILD, "timing.json")))
    lay = layout({k: v["dur"] for k, v in timing.items()})
    plan, g = [], 0
    for idx, (sid, title, beats) in enumerate(SCENES):
        starts, ends, total = lay[sid]
        n = math.ceil(total * FPS)
        plan.append(dict(idx=idx, sid=sid, title=title, starts=starts, ends=ends, n=n, g0=g,
                         beats=beats))
        g += n
    return plan, g, timing


_texture = None


def texture():
    """Faint dot grid, rendered once per process."""
    global _texture
    if _texture is None:
        surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
        c = cairo.Context(surf)
        c.set_source_rgb(*BG)
        c.paint()
        for x in range(20, W, 40):
            for y in range(20, H, 40):
                c.arc(x, y, 1.3, 0, 2 * math.pi)
                c.new_sub_path()
        c.set_source_rgba(1, 1, 1, 0.035)
        c.fill()
        _texture = surf
    return _texture


def draw_frame(ctx, sc, f, total_frames):
    t = f / FPS
    dur = sc["n"] / FPS
    T = Timing(sc["starts"], sc["ends"], dur)
    ctx.set_source_surface(texture(), 0, 0)
    ctx.paint()
    if sc["title"]:
        a = eo(prog(t, 0.0, 0.5))
        text(ctx, f"{sc['idx']:02d}", 110, 92, 22, AMBER, MONO, True, a)
        text(ctx, sc["title"], 160, 92, 24, MUTED, SANS, True, a)
    DRAW[sc["sid"]](ctx, t, T)
    # fade through background at scene edges
    fade = 0.0
    if sc["idx"] > 0:
        fade = max(fade, 1 - prog(t, 0, FADE))
    fade = max(fade, prog(t, dur - FADE, FADE))
    if fade > 0:
        ctx.rectangle(0, 0, W, H)
        color(ctx, BG, fade)
        ctx.fill()
    # global progress bar
    p = (sc["g0"] + f) / total_frames
    ctx.rectangle(0, H - 5, W, 5)
    color(ctx, STROKE, 0.6)
    ctx.fill()
    ctx.rectangle(0, H - 5, W * p, 5)
    color(ctx, AMBER, 0.75)
    ctx.fill()


def render_scene(args):
    sc, total_frames = args
    path = os.path.join(BUILD, f"seg_{sc['idx']:02d}.mp4")
    ff = subprocess.Popen(
        ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "bgra",
         "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium",
         "-crf", "17", "-pix_fmt", "yuv420p", "-threads", "3", "-g", "60", path],
        stdin=subprocess.PIPE)
    surf, ctx = gfx.new_surface()
    for f in range(sc["n"]):
        ctx.save()
        draw_frame(ctx, sc, f, total_frames)
        ctx.restore()
        surf.flush()
        ff.stdin.write(bytes(surf.get_data()))
    ff.stdin.close()
    if ff.wait() != 0:
        raise RuntimeError(f"ffmpeg failed for scene {sc['sid']}")
    return path


def preview(plan, total, only=None):
    out = os.path.join(BUILD, "preview")
    os.makedirs(out, exist_ok=True)
    surf, ctx = gfx.new_surface()
    for sc in plan:
        if only and sc["sid"] not in only:
            continue
        times = [e + 0.3 for e in sc["ends"]] + [sc["n"] / FPS - FADE - 0.05]
        for i, tt in enumerate(times):
            ctx.save()
            draw_frame(ctx, sc, min(int(tt * FPS), sc["n"] - 1), total)
            ctx.restore()
            surf.write_to_png(os.path.join(out, f"{sc['idx']:02d}_{sc['sid']}_{i}.png"))
    print("previews in", out)


def build_audio(plan, timing):
    sr = next(iter(timing.values()))["sr"]
    pcm = bytearray()
    for sc in plan:
        buf = bytearray(round(sc["n"] / FPS * sr) * 2)
        for i, st in enumerate(sc["starts"]):
            with wave.open(os.path.join(BUILD, "audio", f"{sc['sid']}_{i}.wav")) as wf:
                data = wf.readframes(wf.getnframes())
            off = round(st * sr) * 2
            buf[off:off + len(data)] = data[:len(buf) - off]
        pcm += buf
    path = os.path.join(BUILD, "narration.wav")
    with wave.open(path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(bytes(pcm))
    return path


def srt_time(s):
    ms = int(round(s * 1000))
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


def build_srt(plan):
    cues = []
    for sc in plan:
        base = sc["g0"] / FPS
        for b, st, en in zip(sc["beats"], sc["starts"], sc["ends"]):
            pieces = []
            for sent in re.split(r"(?<=[.:])\s+", b["cap"]):
                if len(sent) > 84:
                    pieces += [p for p in re.split(r"(?<=,)\s+", sent) if p]
                else:
                    pieces.append(sent)
            # merge tiny fragments into their neighbour
            merged = []
            for p in pieces:
                if merged and (len(p) < 28 or len(merged[-1]) < 28) and \
                        len(merged[-1]) + len(p) < 90:
                    merged[-1] += " " + p
                else:
                    merged.append(p)
            total = sum(len(p) for p in merged)
            t0 = st
            for j, p in enumerate(merged):
                t1 = t0 + (en - st) * len(p) / total
                tail = 0.3 if j == len(merged) - 1 else 0.0
                cues.append((base + t0, base + t1 + tail, p))
                t0 = t1
    path = os.path.join(BUILD, "captions.srt")
    with open(path, "w") as f:
        for i, (a, b, s) in enumerate(cues, 1):
            f.write(f"{i}\n{srt_time(a)} --> {srt_time(b)}\n{s}\n\n")
    return path


def main():
    plan, total, timing = load_plan()
    if len(sys.argv) > 1 and sys.argv[1] == "preview":
        preview(plan, total, set(sys.argv[2:]) or None)
        return
    print(f"{total} frames, {total / FPS:.1f}s")
    with mp.Pool(min(len(plan), 6)) as pool:
        segs = pool.map(render_scene, [(sc, total) for sc in plan])
    lst = os.path.join(BUILD, "segments.txt")
    with open(lst, "w") as f:
        for s in segs:
            f.write(f"file '{s}'\n")
    wav = build_audio(plan, timing)
    srt = build_srt(plan)
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst,
         "-i", wav, "-i", srt, "-map", "0:v", "-map", "1:a", "-map", "2:s",
         "-c:v", "copy", "-af", "highpass=f=70,loudnorm=I=-16:TP=-1.5:LRA=11",
         "-c:a", "aac", "-b:a", "160k", "-ar", "48000", "-c:s", "mov_text",
         "-metadata:s:s:0", "language=eng", "-movflags", "+faststart", OUT], check=True)
    srt_out = os.path.splitext(OUT)[0] + ".srt"
    with open(srt) as a, open(srt_out, "w") as b:
        b.write(a.read())
    print("wrote", OUT)


if __name__ == "__main__":
    main()
