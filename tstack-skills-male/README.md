# tstack, explained (male voice)

A 4-minute narrated explainer: [`tstack-skills-male.mp4`](tstack-skills-male.mp4) (1920×1080, 30 fps). English captions are embedded as a subtitle track and also provided as [`tstack-skills-male.srt`](tstack-skills-male.srt).

The same video as [`tstack-skills`](../tstack-skills/), narrated by Piper's male `en_US-mike-medium` voice instead of `en_US-lessac-high`. Mike had the fewest transcription errors of eight male Piper voices tested on this script. A few sentences are reworded from the original because this voice blurred them (for example "Never a homemade sleep loop" instead of "polling loop", and "The council skill stands alone").

Covers the nine agent skills in Theo Browne's [tstack](https://github.com/t3dotgg/tstack): how most of them chain into one pull request pipeline, then each skill in pipeline order (`sol-loop`, `file-pr`, `babysit-pr`, `leaving-pr-comments`, `full-send`, `full-stop`, `council`, `modernize`, `takeover`), how they depend on each other, and how to install them.

Every claim comes from the repo's README and the skills' `SKILL.md` files at commit `7de017b`. The bad and good PR titles and descriptions in the `file-pr` scene are quoted from `file-pr/SKILL.md`, and the `pr-wait` lines follow the output format in `babysit-pr/scripts/pr-wait`. The PRs, file names, commit hashes, and people in the examples are made up. The install terminal shows real output from `git clone`, `gh auth status` (account name replaced with `you`), and `python3 --version`.

## How it's made

No video framework. Each frame is drawn with pycairo and piped to ffmpeg.

| File | Role |
| --- | --- |
| `src/script.py` | Narration, one caption per visual beat. The spoken text is derived from the caption (`PR` → "P R", `GPT` → "G P T", `CLAUDE.md` → "Claude M D", etc.) so the two never drift apart. |
| `src/tts.py` | Synthesizes each beat with [Piper](https://github.com/OHF-Voice/piper1-gpl) and records durations in `build/timing.json`. |
| `src/scenes.py` | One draw function per scene, with animations keyed to the word in the narration that introduces them. |
| `src/gfx.py` | Drawing primitives: text, panels, terminals, arrows, commit nodes. |
| `src/render.py` | Renders scenes in parallel, lays the narration on the timeline, writes captions, and muxes the final mp4. |

## Rebuilding

Needs `python3` with pycairo, `ffmpeg` with libx264, [uv](https://docs.astral.sh/uv/), and the fonts JetBrainsMono Nerd Font and Noto Sans.

```sh
# Narration environment and voice (en_US-mike-medium, ~63 MB)
C=~/.cache/explainer-video
uv venv $C/tts && uv pip install --python $C/tts/bin/python piper-tts
mkdir -p $C/voices
for f in en_US-mike-medium.onnx en_US-mike-medium.onnx.json; do
  curl -L -o $C/voices/$f "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/mike/medium/$f"
done

cd tstack-skills-male
$C/tts/bin/python src/tts.py      # narration -> build/audio/, build/timing.json
python3 src/render.py preview      # optional: PNG keyframes per beat -> build/preview/
python3 src/render.py              # full render -> tstack-skills-male.mp4, tstack-skills-male.srt
```

Piper adds random variation, so each rebuild's narration (and the video length) differs by fractions of a second.
