# git worktrees, explained

A 4-minute narrated explainer: [`git-worktrees-explained.mp4`](git-worktrees-explained.mp4) (1920×1080, 30 fps). English captions are embedded as a subtitle track and also provided as [`git-worktrees-explained.srt`](git-worktrees-explained.srt).

Covers why stash-and-switch and re-cloning are awkward, what a repository is made of, `git worktree add`, the `.git` file and `.git/worktrees/<name>/` admin folder, how commits are shared across worktrees, the one-branch-per-worktree rule and `--detach`, `list`/`remove`/`prune`, and when to use a worktree.

All terminal output shown on screen is real output from git 2.56, with paths rewritten to `/home/you`.

## How it's made

No video framework. Each frame is drawn with pycairo and piped to ffmpeg.

| File | Role |
| --- | --- |
| `src/script.py` | Narration, one caption per visual beat. The spoken text is derived from the caption (`.git` → "dot git", etc.) so the two never drift apart. |
| `src/tts.py` | Synthesizes each beat with [Piper](https://github.com/OHF-Voice/piper1-gpl) and records durations in `build/timing.json`. |
| `src/scenes.py` | One draw function per scene, with animations keyed to when each narrated beat starts. |
| `src/gfx.py` | Drawing primitives: text, panels, terminals, arrows, commit nodes. |
| `src/render.py` | Renders scenes in parallel, lays the narration on the timeline, writes captions, and muxes the final mp4. |

## Rebuilding

Needs `python3` with pycairo, `ffmpeg` with libx264, [uv](https://docs.astral.sh/uv/), and the fonts JetBrainsMono Nerd Font and Noto Sans.

```sh
cd git-worktrees

# TTS environment and voice (en_US-lessac-high, ~114 MB)
uv venv .venv-tts && uv pip install --python .venv-tts/bin/python piper-tts
mkdir -p voices
for f in en_US-lessac-high.onnx en_US-lessac-high.onnx.json; do
  curl -L -o voices/$f "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/high/$f"
done

.venv-tts/bin/python src/tts.py      # narration -> build/audio/, build/timing.json
python3 src/render.py preview        # optional: PNG keyframes per beat -> build/preview/
python3 src/render.py                # full render, about 35 s on 16 cores
```

Piper adds random variation, so each rebuild's narration (and the video length) differs by fractions of a second.
