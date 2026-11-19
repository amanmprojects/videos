#!/usr/bin/env python3
"""The demo recording's script: Rune replays these events on its virtual clock.

Writes demo/script.json. Each step names a time in seconds; `key`, `type` and the rest are
Rune's headless script events (crates/rune/README.md, "Agent tooling").
"""

import json
import pathlib

events = []


def at(t, **ev):
    events.append({"t": round(t, 2), **ev})


def key(t, name, **mods):
    at(t, type="key", name=name, **mods)


def typed(t, text):
    at(t, type="type", text=text)


def swipe(t, dx, x=640, y=520):
    """A two-finger trackpad swipe: `dx` points spread over a third of a second."""
    at(t, type="wheel", dx=6, dy=0, phase="began", x=x, y=y)
    steps = 12
    for i in range(1, steps + 1):
        at(t + i * 0.028, type="wheel", dx=dx / steps, dy=0, phase="moved", x=x, y=y)
    at(t + steps * 0.028 + 0.05, type="wheel", dx=0, dy=0, phase="ended", x=x, y=y)


# Photos, with the preview pane.
typed(0.9, "pho")
key(1.6, "Enter")
key(2.5, "ArrowDown")
key(3.2, "p", alt=True)
key(4.4, "ArrowDown")
key(5.2, "ArrowDown")
key(6.0, "ArrowDown")
# Quick Look, stepping through the folder.
typed(7.0, " ")
key(8.4, "ArrowUp")
key(9.4, "ArrowUp")
typed(10.6, " ")
# Back home (the list comes back where it was), then into an archive as a folder.
key(11.4, "Left", alt=True)
typed(12.4, "web")
key(13.1, "Enter")
key(14.2, "ArrowDown")
key(14.8, "Enter")
key(15.9, "ArrowDown")
key(16.6, "ArrowDown")
key(17.3, "ArrowDown")
# Up and out, then a typed path with completion.
key(18.3, "Backspace")
key(18.9, "Backspace")
key(19.8, "l", cmd=True)
key(20.1, "End")
typed(20.3, "/Pro")
key(21.6, "Tab")
key(22.4, "Enter")
# A tab, and the terminal panel.
key(23.3, "n", cmd=True)
key(24.2, "Tab", cmd=True)
key(25.1, "t", cmd=True)
typed(26.3, "ls -1")
key(27.1, "Enter")
key(28.4, "t", cmd=True)
# Copy a file, open the pinned server, paste: an upload over scp.
key(29.0, "Home", alt=True)
typed(29.8, "no")
key(30.4, "c", cmd=True)
at(31.2, type="tap", key="host-web-prod")
key(34.0, "v", cmd=True)
# Swipe back to the local folder; a context menu; the right sidebar away.
swipe(36.4, 210)
at(38.2, type="secondary-click", key="todo.txt")
key(39.8, "Escape")
key(40.5, "b", cmd=True, alt=True)
at(41.8, type="mark", name="end")

out = pathlib.Path(__file__).with_name("script.json")
out.write_text(json.dumps({"events": events}, indent=1))
print(f"{out}: {len(events)} events, ends at {events[-1]['t']}s")
