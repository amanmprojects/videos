# Files: a 40-second tour

A silent screen recording of [Files](https://github.com/amanmprojects/files), a native Linux file explorer built with [Rune](https://github.com/anomalyco/rune): [`files-demo.mp4`](files-demo.mp4) (2560×1600, 30 fps, 0:42). Captions saying what each part shows are embedded as a subtitle track and also provided as [`files-demo.srt`](files-demo.srt). The keys pressed appear in the bottom-right corner.

Shows type-to-select, the preview pane, Quick Look stepping through photos, Back returning to the same scroll position, a `.tar.gz` opened as a folder with code and Markdown previews from inside it, path completion, tabs, the terminal panel, copying a file to a pinned SSH server (an upload over `scp`), a two-finger swipe back, the context menu and the right sidebar.

All folders and files are fixtures; the "web-prod" server is a throwaway sshd on 127.0.0.1.

## How it's made

No screen capture. Rune can run any app headless on a virtual clock and replay scripted input; with `--realtime` each frame waits for the wall clock, so background work (previews, completions, the upload) lands when it would in a window. Every frame is the app's own rendering, piped to ffmpeg.

| File | Role |
| --- | --- |
| `src/fixtures.sh` | Builds the demo folders: photos (ImageMagick), a small website, a `.tar.gz` of it, a PDF, an MP3 with tags. |
| `src/storyboard.py` | The scripted session: each key, typed text, click and swipe, at its time. Writes `script.json`. |
| `src/record.sh` | Starts the throwaway sshd, builds Files with Rune's recording tooling, replays the script with `--realtime --video ... --keys --pointer`, and makes the README GIF. Run from the Files repo as `demo/record.sh`. |
