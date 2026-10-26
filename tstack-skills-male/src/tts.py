"""Synthesize one WAV per beat with Piper; record durations in build/timing.json.
Beats whose text is unchanged are cached. Run from the video folder:
  ~/.cache/explainer-video/tts/bin/python -I src/tts.py
Voice: ~/.cache/explainer-video/voices/en_US-mike-medium.onnx, or set PIPER_VOICE."""
import hashlib
import json
import os
import sys
import wave

import numpy as np
from piper import PiperVoice, SynthesisConfig

sys.path.insert(0, os.path.dirname(__file__))
from script import SCENES, speech  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "build", "audio")
MODEL = os.environ.get("PIPER_VOICE", os.path.expanduser(
    "~/.cache/explainer-video/voices/en_US-mike-medium.onnx"))
SENTENCE_GAP = 0.32
CFG = SynthesisConfig(length_scale=1.0, noise_scale=0.6, noise_w_scale=0.75)


def trim(x, sr, thresh=0.01, pad=0.04):
    idx = np.where(np.abs(x) > thresh)[0]
    if len(idx) == 0:
        return x
    p = int(pad * sr)
    return x[max(0, idx[0] - p): idx[-1] + p]


def main():
    os.makedirs(OUT, exist_ok=True)
    timing_path = os.path.join(ROOT, "build", "timing.json")
    timing = json.load(open(timing_path)) if os.path.exists(timing_path) else {}
    voice = PiperVoice.load(MODEL)
    sr = voice.config.sample_rate
    for sid, _, beats in SCENES:
        for i, b in enumerate(beats):
            key = f"{sid}:{i}"
            say = speech(b["cap"])
            h = hashlib.sha1((say + MODEL + repr(CFG)).encode()).hexdigest()[:12]
            path = os.path.join(OUT, f"{sid}_{i}.wav")
            if timing.get(key, {}).get("hash") == h and os.path.exists(path):
                continue
            parts = []
            for chunk in voice.synthesize(say, syn_config=CFG):
                if parts:
                    parts.append(np.zeros(int(SENTENCE_GAP * sr), dtype=np.float32))
                parts.append(chunk.audio_float_array.astype(np.float32))
            audio = trim(np.concatenate(parts), sr)
            pcm = (np.clip(audio, -1, 1) * 32767).astype(np.int16)
            with wave.open(path, "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(sr)
                wf.writeframes(pcm.tobytes())
            timing[key] = {"hash": h, "dur": len(pcm) / sr, "sr": sr, "say": say}
            print(f"{key:12s} {len(pcm) / sr:5.2f}s  {say}")
    json.dump(timing, open(timing_path, "w"), indent=1)
    total = sum(v["dur"] for v in timing.values())
    print(f"speech total {total:.1f}s")


if __name__ == "__main__":
    main()
