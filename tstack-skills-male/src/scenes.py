"""One draw function per scene: draw(ctx, t, T) where t is seconds into the scene
and T holds the narration beat timings (T.b[i] start, T.e[i] end, T.at(i, frac)).
Key every entrance to a beat so it appears when the narration mentions it."""
import math

import cairo

from gfx import (
    AMBER, BG, BLUE, CYAN, DIM, GREEN, I_BRANCH, I_CHECK, I_EYE, I_FILE, I_FLASK, I_PR,
    I_ROBOT, I_X, MONO, MUTED, PANEL, PANEL2, PURPLE, RED, SANS, STROKE, TEXT, W, appear,
    arrow, box, color, commit, eio, eo, font, glow, hexc, lerp, line, mark, mix, para, prog,
    route, rrect, spans, terminal, text, tw,
)
from script import word_frac

PINK = hexc("#f472b6")
ORANGE = hexc("#ff9e64")
INDIGO = hexc("#8b93f8")
GH_BLUE = hexc("#4493f8")
ANTHROPIC = hexc("#d97757")
OPENAI = hexc("#10b981")
GOOGLE = hexc("#4285f4")
I_INFO = ""

SK = {
    "full-send": PINK, "full-stop": RED, "council": PURPLE, "sol-loop": CYAN,
    "file-pr": BLUE, "takeover": ORANGE, "babysit-pr": AMBER, "modernize": GREEN,
    "leaving-pr-comments": INDIGO,
}


class Timing:
    def __init__(self, starts, ends, dur):
        self.b, self.e, self.dur = starts, ends, dur

    def at(self, i, f=0.0):
        return self.b[i] + f * (self.e[i] - self.b[i])


def wd(T, sid, i, word):
    """Time the narration reaches `word` in beat i."""
    return T.at(i, word_frac(sid, i, word))


def pulse(t, start, dur=1.2):
    """0 -> 1 -> settles at 0.45; use as a highlight/glow strength."""
    if t < start:
        return 0.0
    p = (t - start) / dur
    return 0.45 + 0.55 * math.exp(-3 * p) * (1 if p > 0.15 else p / 0.15)


# ---------------------------------------------------------------- helpers

def _pw(ctx, p, size):
    return tw(ctx, p[0], size, p[3] if len(p) > 3 else MONO, p[2] if len(p) > 2 else False)


def tag_w(ctx, parts, size):
    return sum(_pw(ctx, p, size) for p in parts) + size * 1.4


def tag(ctx, x, y, parts, c, size=24, a=1.0, align="l", solid=False):
    """Rounded pill around a run of spans. y is the vertical center. Returns width."""
    if a <= 0:
        return tag_w(ctx, parts, size)
    w = tag_w(ctx, parts, size)
    h = size * 1.75
    if align == "r":
        x -= w
    elif align == "c":
        x -= w / 2
    rrect(ctx, x, y - h / 2, w, h, h / 2)
    color(ctx, c, (0.92 if solid else 0.14) * a)
    ctx.fill_preserve()
    color(ctx, c, 0.6 * a)
    ctx.set_line_width(2)
    ctx.stroke()
    spans(ctx, parts, x + size * 0.7, y, size, MONO, a)
    return w


def grad_text(ctx, s, full, x, y, size, c1, c2, a=1.0):
    """Left part `s` of `full`, drawn so that `full` would be centered on x."""
    font(ctx, size, MONO, True)
    fw = ctx.text_extents(full).x_advance
    x0 = x - fw / 2
    asc, desc = ctx.font_extents()[:2]
    g = cairo.LinearGradient(x0, 0, x0 + fw, 0)
    g.add_color_stop_rgba(0, *c1, a)
    g.add_color_stop_rgba(1, *c2, a)
    ctx.move_to(x0, y + (asc - desc) / 2)
    ctx.text_path(s)
    ctx.set_source(g)
    ctx.fill()
    return x0 + ctx.text_extents(s).x_advance if s else x0


def header(ctx, t, name, n, trigger, tagline, c):
    a, dy = appear(t, 0.05, 0.5)
    w = text(ctx, name, 110, 180 + dy, 68, c, MONO, True, a)
    text(ctx, f"skill {n} of 9", 110 + w + 30, 188 + dy, 24, DIM, MONO, False, a)
    a2 = eo(prog(t, 0.35, 0.5))
    if trigger:
        tag(ctx, 1810, 180, [("say ", MUTED, False, SANS), (f'"{trigger}"', c, True, MONO)], c, 26,
            a2, "r")
    else:
        tag(ctx, 1810, 180, [("loads automatically", c, True, SANS)], c, 26, a2, "r")
    a3, dy3 = appear(t, 0.25, 0.5)
    text(ctx, tagline, 110, 250 + dy3, 30, MUTED, SANS, False, a3)


def strike(ctx, x, y, w, p, c=RED, a=1.0, lw=3):
    if p > 0:
        line(ctx, x, y, x + w * p, y, c, lw, a)


def card(ctx, x, y, w, h, c, a=1.0, g=0.0, fill=PANEL, r=18):
    if a <= 0:
        return
    if g > 0:
        glow(ctx, x, y, w, h, c, a * g, r, 14)
    box(ctx, x, y, w, h, r, fill, a, mix(STROKE, c, 0.35 + 0.65 * g), 2.5)


# ---------------------------------------------------------------- title

GRID = ["full-send", "full-stop", "council", "sol-loop", "file-pr", "takeover",
        "babysit-pr", "modernize", "leaving-pr-comments"]


def s_title(ctx, t, T):
    up = eio(prog(t, T.b[1] - 0.2, 0.8))
    n = min(6, int(max(0.0, t - 0.15) / 0.08))
    size = lerp(220, 100, up)
    y = lerp(440, 240, up)
    end = grad_text(ctx, "tstack"[:n], "tstack", W / 2, y, size, PINK, PURPLE)
    if n < 6 or (up < 0.05 and int(t * 2.2) % 2 == 0):
        ctx.rectangle(end + 6, y - size * 0.42, size * 0.09, size * 0.84)
        color(ctx, PURPLE, 0.8)
        ctx.fill()

    a, dy = appear(t, 0.9, 0.6)
    text(ctx, "The agent skills I use every day.", W / 2, 590 + dy, 50, TEXT, SANS, True,
         a * (1 - up), "c")
    a, dy = appear(t, 1.5, 0.6)
    spans(ctx, [("Theo Browne", MUTED, False, SANS), ("   ·   ", DIM, False, SANS),
                ("github.com/t3dotgg/tstack", MUTED, False, MONO)], W / 2, 665 + dy, 30, SANS,
          a * (1 - up), align="c")

    # Claude Code + Codex
    p1 = [("Claude Code", ANTHROPIC, True, SANS)]
    p2 = [("Codex", OPENAI, True, SANS)]
    w1, w2 = tag_w(ctx, p1, 26), tag_w(ctx, p2, 26)
    x0 = W / 2 - (w1 + 20 + w2) / 2
    tag(ctx, x0, 352, p1, ANTHROPIC, 26, eo(prog(t, wd(T, "title", 1, "Claude Code"), 0.4)))
    tag(ctx, x0 + w1 + 20, 352, p2, OPENAI, 26, eo(prog(t, wd(T, "title", 1, "Codex"), 0.4)))

    t_grid = wd(T, "title", 1, "each one")
    t_dim = wd(T, "title", 2, "full send")
    spoken = {"full-send": ('"full send"', t_dim), "babysit-pr": ('"babysit"', wd(T, "title", 2, "babysit"))}
    dim = eo(prog(t, t_dim, 0.4))
    for i, name in enumerate(GRID):
        c = SK[name]
        x = 156 + (i % 3) * 544
        yy = 440 + (i // 3) * 140
        a, dy = appear(t, t_grid + i * 0.07, 0.45)
        hot = eo(prog(t, spoken[name][1], 0.4)) if name in spoken else 0.0
        a *= 1 - dim * 0.6 + hot * 0.6
        card(ctx, x, yy + dy, 520, 116, c, a, hot)
        text(ctx, name, x + 28, yy + dy + 44, 31, c, MONO, True, a)
        text(ctx, "SKILL.md", x + 28, yy + dy + 84, 20, DIM, MONO, False, a)
        if hot > 0:
            tag(ctx, x + 500, yy + 58, [(spoken[name][0], BG, True, MONO)], c, 24, hot, "r",
                solid=True)


# ---------------------------------------------------------------- pipeline

def s_pipeline(ctx, t, T):
    a, dy = appear(t, 0.1, 0.5)
    text(ctx, "One pipeline", 110, 210 + dy, 64, TEXT, SANS, True, a)
    nodes = [("your change", "edit, commit", MUTED), ("sol-loop", "review in rounds", SK["sol-loop"]),
             ("file-pr", "open the PR", SK["file-pr"]), ("babysit-pr", "CI and review bots", SK["babysit-pr"]),
             ("merged", "into main", GREEN)]
    words = ["Make the change", "Review it", "File the PR", "Babysit it", "Then merge"]
    nw, gap, y, h = 280, 70, 560, 150
    x0 = (W - (5 * nw + 4 * gap)) / 2
    t_box = T.b[2]
    t_pieces = wd(T, "pipeline", 2, "First")
    for i, (label, sub, c) in enumerate(nodes):
        st = wd(T, "pipeline", 1, words[i])
        x = x0 + i * (nw + gap)
        a, dy = appear(t, st, 0.45)
        g = pulse(t, t_pieces + (i - 1) * 0.15) if 1 <= i <= 3 else 0.0
        card(ctx, x, y + dy, nw, h, c, a, g)
        text(ctx, label, x + nw / 2, y + dy + 62, 32, c, MONO, True, a, "c")
        text(ctx, sub, x + nw / 2, y + dy + 106, 22, MUTED, SANS, False, a, "c")
        if i:
            arrow(ctx, (x - gap + 10, y + h / 2), (x - 12, y + h / 2), MUTED,
                  eo(prog(t, st, 0.35)), 3)
    a = eo(prog(t, t_box, 0.5))
    if a > 0:
        box(ctx, x0 - 36, y - 74, 5 * nw + 4 * gap + 72, h + 148, 28, None, a, PINK, 3,
            dash=[14, 10])
        tag(ctx, x0 - 36, y - 74, [("full-send", BG, True, MONO)], PINK, 26, a, solid=True)


# ---------------------------------------------------------------- sol-loop

def s_sol(ctx, t, T):
    c = SK["sol-loop"]
    header(ctx, t, "sol-loop", 1, "sol loop", "Review your diff with GPT Sol in rounds, until you both agree.", c)

    t_approve = wd(T, "sol", 3, "It stops") + 0.9
    for x, title, sub, cc, st in [(110, "Agent", "writes the smallest fix", PINK, 0.3),
                                  (1410, "GPT Sol", "reviews only, no edits", c, 0.45)]:
        a, dy = appear(t, st, 0.5)
        card(ctx, x, 320 + dy, 400, 160, cc, a, pulse(t, t_approve) if cc == c else 0)
        text(ctx, title, x + 30, 370 + dy, 40, cc, SANS, True, a)
        text(ctx, sub, x + 30, 430 + dy, 24, MUTED, SANS, False, a)

    t_diff = wd(T, "sol", 0, "sends your diff")
    arrow(ctx, (530, 375), (1390, 375), c, eo(prog(t, t_diff, 0.6)), 3)
    text(ctx, "git diff <base>", 960, 348, 22, c, MONO, False, eo(prog(t, t_diff + 0.3, 0.4)), "c")
    t_find = T.b[1]
    arrow(ctx, (1390, 430), (530, 430), AMBER, eo(prog(t, t_find, 0.6)), 3)
    text(ctx, "findings", 960, 458, 22, AMBER, MONO, False, eo(prog(t, t_find + 0.3, 0.4)), "c")

    rnd = 2 if t >= t_approve - 0.5 else 1
    a = eo(prog(t, wd(T, "sol", 0, "in rounds"), 0.4))
    tag(ctx, 950, 528, [(f"round {rnd} / 3", c, True, MONO)], c, 22, a, "r")
    a = eo(prog(t, wd(T, "sol", 3, "up to five"), 0.4))
    tag(ctx, 970, 528, [("up to 5 for risky code", RED, True, MONO)], RED, 22, a)

    a = eo(prog(t, wd(T, "sol", 3, "It stops") + 0.9, 0.35))
    if a > 0:
        tag(ctx, 1790, 345, [("APPROVE", BG, True, MONO)], GREEN, 20, a, "r", solid=True)

    # ledger
    t_tab = T.b[1] + 0.2
    a = eo(prog(t, t_tab, 0.5))
    g = pulse(t, wd(T, "sol", 2, "ledger"))
    card(ctx, 110, 585, 1700, 330, c, a, g * 0.8)
    for x, s in [(140, "id"), (240, "severity"), (440, "finding"), (1120, "outcome in the ledger")]:
        text(ctx, s, x, 622, 20, DIM, MONO, False, a)
    line(ctx, 130, 648, 1790, 648, STROKE, 1.5, a)
    rows = [("S1", "blocker", RED, "reconnect drops queued messages", "fixed: flush queue on open", GREEN, "fixes the real"),
            ("S2", "should", AMBER, "timer not cleared on close()", "disagree: cleared at ws.ts:120", AMBER, "pushes back"),
            ("S3", "nit", MUTED, "rename buf to pending", "declined, listed as follow-up", MUTED, "with evidence")]
    for i, (rid, sev, sc, finding, outcome, oc, word) in enumerate(rows):
        yy = 700 + i * 75
        ra, rdy = appear(t, wd(T, "sol", 1, sev), 0.4)
        text(ctx, rid, 140, yy + rdy, 26, MUTED, MONO, True, ra)
        tag(ctx, 240, yy + rdy, [(sev, sc, True, MONO)], sc, 20, ra)
        text(ctx, finding, 440, yy + rdy, 28, TEXT, SANS, False, ra)
        oa, ody = appear(t, wd(T, "sol", 2, word) + 0.2, 0.4)
        text(ctx, outcome, 1120, yy + ody, 24, oc, MONO, False, oa)

    a = eo(prog(t, wd(T, "sol", 3, "or hands"), 0.4))
    spans(ctx, [("still disputed?  ", MUTED, False, SANS), ("you decide.", TEXT, True, SANS)],
          1810 - tw(ctx, "still disputed?  ", 26, SANS) - tw(ctx, "you decide.", 26, SANS, True),
          960, 26, SANS, a)


# ---------------------------------------------------------------- file-pr

def s_filepr(ctx, t, T):
    c = SK["file-pr"]
    header(ctx, t, "file-pr", 2, "file a PR", "A short PR that leads with the problem, not an inventory of changes.", c)
    lx, rx, cw = 110, 980, 830

    def verdict_card(x, y, h, good, a, dim):
        cc = GREEN if good else RED
        a *= 1 - dim * 0.5
        card(ctx, x, y, cw, h, cc, a, 0.25 if good else 0.0)
        spans(ctx, [((I_CHECK if good else I_X) + "  ", cc, False, MONO),
                    ("GOOD" if good else "BAD", cc, True, SANS)], x + 28, y + 30, 20, SANS, a)
        return a

    slot_a = eo(prog(t, wd(T, "filepr", 0, "pull request"), 0.5))
    for sx in (lx, rx):
        for sy, sh, st in ((352, 150, wd(T, "filepr", 1, "why the change")),
                           (568, 262, wd(T, "filepr", 2, "opens with"))):
            box(ctx, sx, sy, cw, sh, 18, None, slot_a * (1 - eo(prog(t, st, 0.4))), STROKE, 2,
                dash=[10, 8])

    # title row
    t_good = wd(T, "filepr", 1, "why the change")
    t_bad = wd(T, "filepr", 1, "not how")
    text(ctx, "TITLE", 110, 330, 20, DIM, MONO, True, eo(prog(t, T.b[1], 0.4)))
    a = verdict_card(rx, 352, 150, True, eo(prog(t, t_good, 0.45)), 0)
    para(ctx, "perf(server): cut websocket frame size by 70%+ with gzipping", rx + 28, 424, 25,
         cw - 56, TEXT, MONO, False, a, 1.4)
    a = verdict_card(lx, 352, 150, False, eo(prog(t, t_bad, 0.45)), eo(prog(t, t_bad + 1.0, 0.5)))
    para(ctx, "perf(server): negotiate permessage-deflate on the websocket", lx + 28, 424, 25,
         cw - 56, TEXT, MONO, False, a, 1.4)

    # description row
    t_good = wd(T, "filepr", 2, "opens with")
    t_bad = wd(T, "filepr", 2, "not a list")
    text(ctx, "DESCRIPTION", 110, 546, 20, DIM, MONO, True, eo(prog(t, T.b[2], 0.4)))
    a = verdict_card(rx, 568, 262, True, eo(prog(t, t_good, 0.45)), 0)
    para(ctx, 'My "new worktree" default was ignored when starting new threads on existing '
              'worktrees. Super unintuitive. Now your preferences always apply.',
         rx + 28, 640, 28, cw - 56, TEXT, SANS, False, a, 1.45)
    a = verdict_card(lx, 568, 262, False, eo(prog(t, t_bad, 0.45)), eo(prog(t, t_bad + 1.6, 0.5)))
    para(ctx, 'Removed implicit workspace carry-over from every "new thread" entry point '
              '(cmd+n / cmd+shift+o, sidebar v1/v2 buttons, command palette). New threads inherit '
              'only the project from context; branch, worktree, and env mode always come from the '
              'configured defaults. Deleted buildContextualThreadOptions, ...',
         lx + 28, 636, 21, cw - 56, MUTED, SANS, False, a, 1.42)

    # filing
    y = 900
    x = 110
    x += tag(ctx, x, y, [(I_CHECK + " ", GREEN, False, MONO), ("checked for secrets", GREEN, True, SANS)],
             GREEN, 26, eo(prog(t, wd(T, "filepr", 3, "secrets"), 0.4))) + 24
    a = eo(prog(t, wd(T, "filepr", 3, "real PR"), 0.4))
    x += tag(ctx, x, y, [(I_PR + " ", BG, False, MONO), ("Open", BG, True, SANS)], GREEN, 26, a,
             solid=True) + 22
    a2 = eo(prog(t, wd(T, "filepr", 3, "not a draft"), 0.4))
    dw = text(ctx, "Draft", x, y, 26, MUTED, SANS, True, a2)
    strike(ctx, x - 4, y + 1, dw + 8, eo(prog(t, wd(T, "filepr", 3, "not a draft") + 0.3, 0.3)),
           RED, a2)
    x += dw + 30
    tag(ctx, x, y, [("review bots run", c, True, SANS)], c, 26,
        eo(prog(t, wd(T, "filepr", 3, "review bots"), 0.4)))


# ---------------------------------------------------------------- babysit-pr

def s_babysit(ctx, t, T):
    c = SK["babysit-pr"]
    header(ctx, t, "babysit-pr", 3, "babysit", "Watch a PR through CI and review bots, and fix what is real.", c)

    t_fail = T.b[2]
    t_fix = wd(T, "babysit", 2, "fixes the real")
    t_fp = wd(T, "babysit", 2, "answers false")
    t_rebase = T.b[3] + 0.2
    t_rerun = wd(T, "babysit", 3, "and only") - 0.4
    run1 = {"cmd": "pr-wait 412 --until ready", "t": wd(T, "babysit", 1, "pr-wait") - 0.2,
            "cwd": "app", "br": "fix-reconnect"}
    run2 = {"cmd": "pr-wait 412 --until ready", "t": t_rerun, "cwd": "app", "br": "fix-reconnect"}
    entries = [
        {"out": "# in T3 Code: watch_pull_request", "c": DIM, "t": wd(T, "babysit", 1, "T3 Code")},
        {"out": "# everywhere else:", "c": DIM, "t": wd(T, "babysit", 1, "or the bundled")},
        run1,
        {"out": [("#412 ", DIM), ("new thread from greptile-apps on src/ws.ts:88: null deref?", AMBER)],
         "t": t_fail},
        {"out": [("#412 ", DIM), ("new thread from greptile-apps on src/ws.ts:40: cap retries?", AMBER)],
         "t": t_fail + 0.3},
        {"out": [("#412 ", DIM), ("required check failed: test", RED)], "t": t_fail + 0.6},
        {"gap": True, "t": t_rerun - 0.05},
        run2,
        {"out": [("#412 ", DIM), ("ready on e4f5a6b: 4 pass; ...; merge state CLEAN", GREEN)],
         "t": t_rerun + 1.2},
    ]
    terminal(ctx, 110, 320, 1000, 590, "~/app", entries, t, 22, eo(prog(t, T.b[1] - 0.3, 0.45)))

    a = eo(prog(t, wd(T, "babysit", 1, "Never"), 0.4))
    if a > 0:
        tag(ctx, 110, 962, [("never", RED, True, SANS)], RED, 22, a)
        lw = text(ctx, "while sleep 30; do gh pr checks 412; done", 230, 962, 22, DIM, MONO, False, a)
        strike(ctx, 226, 963, lw + 8, eo(prog(t, wd(T, "babysit", 1, "Never") + 0.3, 0.4)), RED, a)

    # PR panel
    px, py, pw = 1150, 320, 660
    a = eo(prog(t, 0.4, 0.5))
    card(ctx, px, py, pw, 590, c, a)
    spans(ctx, [(I_PR + "  ", GREEN, False, MONO), ("#412", TEXT, True, MONO),
                ("   fix(ws): flush queue on reconnect", MUTED, False, SANS)], px + 30, py + 42, 24,
          MONO, a)
    line(ctx, px, py + 76, px + pw, py + 76, STROKE, 1.5, a)
    text(ctx, "CHECKS", px + 30, py + 110, 18, DIM, MONO, True, a)

    def state(name):
        if name == "typecheck":
            return "pass" if t >= T.at(1, 0.45) else "pending"
        if name == "lint":
            return "pass" if t >= T.at(1, 0.65) else "pending"
        if name == "test":
            if t >= t_rerun + 1.0:
                return "pass"
            if t >= t_fix + 0.4:
                return "pending"
            return "fail" if t >= t_fail + 0.6 else "pending"
        if t >= t_rerun + 1.0:
            return "pass"
        return "2 threads" if t >= t_fail else "pending"

    for i, name in enumerate(["typecheck", "lint", "test", "greptile-apps"]):
        yy = py + 155 + i * 46
        st = state(name)
        if st == "pass":
            mark(ctx, px + 44, yy, True, 20, a)
        elif st == "fail":
            mark(ctx, px + 44, yy, False, 20, a)
        else:
            ctx.new_path()
            ctx.arc(px + 44, yy, 7 + 2 * math.sin(t * 6), 0, 2 * math.pi)
            color(ctx, AMBER, a)
            ctx.fill()
        text(ctx, name, px + 80, yy, 24, TEXT, MONO, False, a)
        sc = {"pass": GREEN, "fail": RED}.get(st, AMBER)
        text(ctx, st, px + pw - 30, yy, 22, sc, MONO, False, a, "r")

    ta = eo(prog(t, t_fail + 0.2, 0.4))
    text(ctx, "REVIEW THREADS", px + 30, py + 355, 18, DIM, MONO, True, ta)
    for i, (where, what, out, oc, st) in enumerate([
            ("ws.ts:88", "null deref?", "fixed", GREEN, t_fix),
            ("ws.ts:40", "cap retries?", "reason given, resolved", MUTED, t_fp)]):
        yy = py + 400 + i * 46
        ra = eo(prog(t, t_fail + 0.3 * i, 0.4))
        spans(ctx, [(where + "  ", CYAN, False, MONO), (what, TEXT, False, SANS)], px + 30, yy, 23,
              MONO, ra)
        oa = eo(prog(t, st, 0.4))
        if oa > 0:
            tag(ctx, px + pw - 26, yy, [(out, oc, True, SANS)], oc, 19, oa, "r")

    ra = eo(prog(t, t_rebase, 0.4))
    spans(ctx, [(I_BRANCH + "  ", BLUE, False, MONO), ("main moved: ", MUTED, False, SANS),
                ("rebased, pushed", BLUE, True, SANS)], px + 30, py + 500, 23, MONO, ra)
    ma = eo(prog(t, wd(T, "babysit", 3, "merges if"), 0.4))
    if ma > 0:
        box(ctx, px + 30, py + 528, pw - 60, 46, 10, PANEL2, ma, STROKE, 2)
        spans(ctx, [("Merge", DIM, True, SANS), ("   only if you asked", MUTED, False, SANS)],
              px + 50, py + 551, 22, SANS, ma)


# ---------------------------------------------------------------- leaving-pr-comments

def s_comments(ctx, t, T):
    c = SK["leaving-pr-comments"]
    header(ctx, t, "leaving-pr-comments", 4, None, "The format for every comment an agent posts on your behalf.", c)
    x, y, w = 260, 330, 1400
    a = eo(prog(t, wd(T, "comments", 0, "whenever"), 0.5))
    note_a = eo(prog(t, T.b[1] + 0.1, 0.45))
    body_a = eo(prog(t, T.b[2] + 0.1, 0.45))
    h = lerp(lerp(150, 260, note_a), 400, body_a)
    card(ctx, x, y, w, h, c, a)
    rrect(ctx, x, y, w, 70, 18)
    color(ctx, PANEL2, a)
    ctx.fill()
    ctx.new_path()
    ctx.arc(x + 44, y + 35, 18, 0, 2 * math.pi)
    color(ctx, c, 0.35 * a)
    ctx.fill()
    text(ctx, "o", x + 44, y + 33, 22, TEXT, SANS, True, a, "c")
    spans(ctx, [("octocat", TEXT, True, SANS), (" commented now", MUTED, False, SANS)], x + 80, y + 35,
          24, SANS, a)
    text(ctx, "posted by an agent", x + w - 30, y + 35, 20, DIM, MONO, False, a, "r")

    # GitHub note callout
    if note_a > 0:
        nx, ny = x + 40, y + 100
        ctx.rectangle(nx, ny, 5, 116)
        color(ctx, GH_BLUE, note_a)
        ctx.fill()
        spans(ctx, [(I_INFO + " ", GH_BLUE, False, MONO), ("Note", GH_BLUE, True, SANS)], nx + 28,
              ny + 30, 24, SANS, note_a)
        spans(ctx, [(I_ROBOT + "  ", TEXT, False, MONO),
                    ("Claude Opus 5.5 responding on behalf of octocat", TEXT, True, SANS)],
              nx + 28, ny + 80, 28, SANS, note_a)
        ga = pulse(t, wd(T, "comments", 1, "naming the model"))
        if ga > 0.01:
            tx0 = nx + 28 + tw(ctx, I_ROBOT + "  ", 28, MONO)
            mw = tw(ctx, "Claude Opus 5.5", 28, SANS, True)
            line(ctx, tx0, ny + 102, tx0 + mw, ny + 102, c, 3, note_a * ga)
            ow = tw(ctx, "Claude Opus 5.5 responding on behalf of ", 28, SANS, True)
            ga2 = pulse(t, wd(T, "comments", 1, "who it speaks"))
            line(ctx, tx0 + ow, ny + 102, tx0 + ow + tw(ctx, "octocat", 28, SANS, True),
                 ny + 102, c, 3, note_a * ga2)

    # reply body
    if body_a > 0:
        bx, by = x + 40, y + 268
        l1 = [("Not a bug: ", TEXT, True, SANS), ("token", CYAN, False, MONO),
              (" is validated in ", TEXT, False, SANS), ("auth.ts:42", CYAN, False, MONO),
              (" before this handler runs, and", TEXT, False, SANS)]
        l2 = [("auth.spec.ts", CYAN, False, MONO), (" covers the empty case. Resolving.", TEXT, False, SANS)]
        spans(ctx, l1, bx, by, 28, SANS, body_a)
        spans(ctx, l2, bx, by + 46, 28, SANS, body_a)

        def under(parts, upto, y):
            x0 = bx + sum(_pw(ctx, p, 28) for p in parts[:upto])
            return x0, x0 + _pw(ctx, parts[upto], 28), y + 22

        t_lead = wd(T, "comments", 2, "leads with")
        t_cite = wd(T, "comments", 2, "cites the code")
        for (x0, x1, uy), st in [(under(l1, 0, by), t_lead), (under(l1, 3, by), t_cite),
                                 (under(l2, 0, by + 46), t_cite + 0.2)]:
            up_ = eo(prog(t, st + 0.2, 0.4))
            if up_ > 0:
                line(ctx, x0, uy, x0 + (x1 - x0) * up_, uy, c, 3, body_a)
        tx = 260
        for label, word in [("conclusion first", "leads with"), ("cites code and checks", "cites the code"),
                            ("no filler", "skips the filler")]:
            ta = eo(prog(t, wd(T, "comments", 2, word), 0.4))
            tx += tag(ctx, tx, 860, [(label, c, True, SANS)], c, 24, ta) + 30
        fa = eo(prog(t, wd(T, "comments", 2, "skips the filler") + 0.3, 0.4))
        fw = text(ctx, "Great catch, thanks so much! Happy to help!", tx, 860, 24, DIM, SANS, False, fa)
        strike(ctx, tx - 4, 861, fw + 8, eo(prog(t, wd(T, "comments", 2, "skips the filler") + 0.6, 0.3)),
               RED, fa)


# ---------------------------------------------------------------- full-send / full-stop

STEPS = [("finish", TEXT), ("prove", GREEN), ("sol-loop", CYAN), ("file-pr", BLUE),
         ("babysit-pr", AMBER), ("merge", PINK), ("report", MUTED)]
SW, SG, SY = 210, 38, 320


def step_x(i):
    return 111 + i * (SW + SG)


def steps(ctx, t, lit, a, labels=None, overrides=None):
    """lit[i]: time step i lights up. overrides: {i: (label, color, struck_p)}."""
    for i, (label, cc) in enumerate(STEPS):
        x = step_x(i)
        sa, dy = appear(t, 0.3 + i * 0.06, 0.4)
        sa *= a
        on = eo(prog(t, lit[i], 0.35))
        ov = (overrides or {}).get(i)
        if ov:
            label, cc, struck = ov
        else:
            struck = 0.0
        c2 = mix(DIM, cc, on)
        card(ctx, x, SY + dy, SW, 84, cc, sa, on * 0.5)
        text(ctx, label, x + SW / 2, SY + dy + 42, 26, c2, MONO, True, sa, "c")
        if struck > 0:
            lw = tw(ctx, label, 26, MONO, True)
            strike(ctx, x + SW / 2 - lw / 2 - 6, SY + dy + 43, lw + 12, struck, RED, sa, 4)
        if i:
            arrow(ctx, (x - SG + 8, SY + 42), (x - 8, SY + 42), mix(STROKE, MUTED, on), sa, 2.5,
                  head=9)


def s_fullsend(ctx, t, T):
    c = SK["full-send"]
    header(ctx, t, "full-send", 5, "full send", "From a change to a merged PR, with nobody watching.", c)
    words = ["finishes", "proves", "runs sol", "files", "babysits", "merges it"]
    lit = [wd(T, "fullsend", 1, w) for w in words] + [T.e[1]]
    steps(ctx, t, lit, 1.0)

    # proof
    t_proof = T.b[2]
    a = eo(prog(t, t_proof, 0.5))
    px = step_x(1) + SW / 2
    arrow(ctx, (px, SY + 92), (px, 470), GREEN, eo(prog(t, t_proof, 0.4)), 3)
    card(ctx, 110, 478, 820, 330, GREEN, a, 0.3)
    text(ctx, "Proof: evidence it saw itself", 140, 522, 30, TEXT, SANS, True, a)
    for i, (ic, s, w) in enumerate([(I_FLASK, "a reproduction that now passes", "a reproduction"),
                                    (I_CHECK, "the repo's checks: typecheck, lint, tests", "the repository's"),
                                    (I_EYE, "the running app: look at the change", "the running")]):
        ra, rdy = appear(t, wd(T, "fullsend", 2, w), 0.4)
        yy = 600 + i * 66 + rdy
        text(ctx, ic, 150, yy, 26, GREEN, MONO, False, ra * a)
        text(ctx, s, 200, yy, 26, TEXT, SANS, False, ra * a)

    # merge gate
    t_gate = T.b[3]
    a = eo(prog(t, t_gate, 0.5))
    mx = step_x(5) + SW / 2
    arrow(ctx, (mx, SY + 92), (mx, 470), PINK, eo(prog(t, t_gate, 0.4)), 3)
    card(ctx, 970, 478, 840, 420, PINK, a, 0.3)
    text(ctx, "Merge gate", 1000, 522, 30, TEXT, SANS, True, a)
    for i, (s, w) in enumerate([("proof covers every change", "proof covers"),
                                ("required checks are green", "checks are green"),
                                ("each finding fixed or dismissed", "findings are"),
                                ("up to date and mergeable", "the branch is current")]):
        on = prog(t, wd(T, "fullsend", 3, w) + 0.3, 0.3)
        yy = 600 + i * 64
        if on > 0:
            mark(ctx, 1022, yy, True, 22, a * eo(on))
        else:
            ctx.new_path()
            ctx.arc(1022, yy, 16, 0, 2 * math.pi)
            color(ctx, STROKE, a)
            ctx.set_line_width(2)
            ctx.stroke()
        text(ctx, s, 1060, yy, 26, mix(MUTED, TEXT, on), SANS, False, a)
    na = eo(prog(t, wd(T, "fullsend", 3, "No admin"), 0.4))
    if na > 0:
        tag(ctx, 1000, 858, [("never ", RED, False, SANS), ("gh pr merge --admin", RED, True, MONO)],
            RED, 22, na)

    # question tool
    qa = eo(prog(t, T.b[4] + 0.1, 0.45))
    if qa > 0:
        ctx.rectangle(0, 0, W, 1075)
        color(ctx, BG, 0.72 * qa)
        ctx.fill()
        dx, dy_, dw, dh = 500, 360 + (1 - qa) * 30, 920, 440
        card(ctx, dx, dy_, dw, dh, PINK, qa, 0.6)
        text(ctx, "AskUserQuestion", dx + 36, dy_ + 44, 20, DIM, MONO, True, qa)
        para(ctx, "PR #412: the crash only reproduces with production data. How should I prove "
                  "the fix?", dx + 36, dy_ + 100, 30, dw - 72, TEXT, SANS, True, qa, 1.35)
        for i, (s, rec) in enumerate([("Use the staging snapshot", True), ("Leave the PR open for you", False)]):
            oy = dy_ + 210 + i * 76
            box(ctx, dx + 36, oy, dw - 72, 60, 12, PANEL2, qa, PINK if rec else STROKE, 2)
            spans(ctx, [(f"{i + 1}  ", DIM, True, MONO), (s, TEXT, False, SANS)] +
                  ([("  (Recommended)", PINK, True, SANS)] if rec else []), dx + 60, oy + 30, 26,
                  SANS, qa)
        tag(ctx, dx + 36, dy_ + dh - 50, [("thread: waiting on you", AMBER, True, SANS)], AMBER, 22,
            eo(prog(t, wd(T, "fullsend", 4, "waiting"), 0.4)) * qa)


def s_fullstop(ctx, t, T):
    c = SK["full-stop"]
    header(ctx, t, "full-stop", 6, "full stop", "Everything full-send does, then it stops at the merge gate.", c)
    t_stop = wd(T, "fullstop", 0, "stops at")
    lit = [0.5 + i * 0.12 for i in range(5)] + [99, t_stop + 0.6]
    struck = eo(prog(t, t_stop, 0.4))
    steps(ctx, t, lit, 1.0, overrides={
        5: ("merge", mix(PINK, RED, struck), struck),
        6: ("hand off" if t >= t_stop + 0.5 else "report", GREEN if t >= t_stop + 0.5 else MUTED, 0.0),
    })

    # auto-merge off
    a = eo(prog(t, T.b[1], 0.45))
    card(ctx, 110, 470, 600, 300, c, a)
    text(ctx, "auto-merge", 140, 530, 30, TEXT, MONO, True, a)
    off = eio(prog(t, wd(T, "fullstop", 1, "turns off") + 0.2, 0.4))
    sx, sy = 560, 530
    rrect(ctx, sx, sy - 22, 90, 44, 22)
    color(ctx, mix(GREEN, STROKE, off), a)
    ctx.fill()
    ctx.new_path()
    ctx.arc(sx + lerp(68, 22, off), sy, 17, 0, 2 * math.pi)
    color(ctx, TEXT, a)
    ctx.fill()
    text(ctx, "merge queue: removed", 140, 600, 26, MUTED, SANS, False,
         a * eo(prog(t, wd(T, "fullstop", 1, "turns off") + 0.6, 0.4)))
    tag(ctx, 140, 690, [("never merges", RED, True, SANS)], RED, 26,
        eo(prog(t, wd(T, "fullstop", 1, "never merges"), 0.4)))

    for i, (label, sub, cc, w) in enumerate([
            ("Ready to merge", "the gate passes; the PR stays open and unmerged", GREEN, "ready"),
            ("Waiting on approval", "only a required human approval is left", AMBER, "waiting"),
            ("Blocked", "what stops it, what was tried, what is needed", RED, "blocked")]):
        ra, rdy = appear(t, wd(T, "fullstop", 1, w), 0.4)
        yy = 470 + i * 110 + rdy
        card(ctx, 760, yy, 1050, 92, cc, ra, 0.3)
        ctx.new_path()
        ctx.arc(800, yy + 46, 10, 0, 2 * math.pi)
        color(ctx, cc, ra)
        ctx.fill()
        text(ctx, label, 830, yy + 46, 30, cc, SANS, True, ra)
        text(ctx, sub, 1780, yy + 46, 23, MUTED, SANS, False, ra, "r")


# ---------------------------------------------------------------- council

def ring_score(ctx, cx, cy, r, score, c, a):
    ctx.new_path()
    ctx.arc(cx, cy, r, 0, 2 * math.pi)
    color(ctx, STROKE, a)
    ctx.set_line_width(12)
    ctx.stroke()
    if score > 0:
        ctx.new_path()
        ctx.arc(cx, cy, r, -math.pi / 2, -math.pi / 2 + 2 * math.pi * score / 10)
        color(ctx, c, a)
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        ctx.stroke()
    text(ctx, f"{round(score)}", cx, cy - 6, 52, TEXT, SANS, True, a, "c")
    text(ctx, "/ 10", cx, cy + 36, 20, MUTED, MONO, False, a, "c")


def s_council(ctx, t, T):
    c = SK["council"]
    header(ctx, t, "council", 7, "council", "Three reviewers from three providers, looping until they agree.", c)
    members = [("Claude Opus", "Anthropic", ANTHROPIC, 7, 9), ("GPT Sol", "OpenAI", OPENAI, 8, 10),
               ("Gemini Pro", "Google", GOOGLE, 7, 9)]
    t_r1 = T.b[1]
    t_r2 = wd(T, "council", 2, "runs fresh")
    for i, (name, prov, cc, s1, s2) in enumerate(members):
        x = 110 + i * 580
        slot_a = eo(prog(t, wd(T, "council", 0, "three reviewers") + i * 0.12, 0.4))
        fill_a = eo(prog(t, wd(T, "council", 0, name), 0.4))
        if fill_a < 1:
            box(ctx, x, 320, 540, 320, 18, None, slot_a * (1 - fill_a), STROKE, 2, dash=[10, 8])
        card(ctx, x, 320 + (1 - fill_a) * 16, 540, 320, cc, fill_a, 0.25)
        yo = (1 - fill_a) * 16
        text(ctx, name, x + 34, 370 + yo, 36, TEXT, SANS, True, fill_a)
        ctx.new_path()
        ctx.arc(x + 42, 418 + yo, 8, 0, 2 * math.pi)
        color(ctx, cc, fill_a)
        ctx.fill()
        text(ctx, prov, x + 60, 418 + yo, 24, MUTED, SANS, False, fill_a)
        sa = eo(prog(t, t_r1 + i * 0.15, 0.4))
        if sa > 0:
            sc = lerp(0, s1, eo(prog(t, t_r1 + i * 0.15, 0.8)))
            sc = lerp(sc, s2, eo(prog(t, t_r2 + i * 0.15, 0.8)))
            ring_score(ctx, x + 400, 540 + yo, 62, sc, cc, sa * fill_a)
            rl = "round 2" if t >= t_r2 else "round 1"
            text(ctx, rl, x + 34, 600 + yo, 22, DIM, MONO, True, sa * fill_a)

    fa = eo(prog(t, wd(T, "council", 2, "applies"), 0.4))
    x = 110
    x += tag(ctx, x, 685, [("fixes it agrees with: applied", c, True, SANS)], c, 22, fa) + 20
    tag(ctx, x, 685, [("scope held", GREEN, True, SANS)], GREEN, 22,
        eo(prog(t, wd(T, "council", 2, "without growing"), 0.4)))

    # PR description table
    ta = eo(prog(t, T.b[3], 0.5))
    if ta > 0:
        card(ctx, 110, 730, 1700, 260, c, ta, 0.2)
        text(ctx, "## Council review", 150, 782, 28, c, MONO, True, ta)
        text(ctx, "Rounds: 2", 150, 830, 24, TEXT, MONO, False, ta)
        text(ctx, "in the PR description", 150, 940, 22, DIM, SANS, False, ta)
        cols = [760, 1260, 1520]
        for j, h in enumerate(["Delegate", "Round 1", "Round 2"]):
            text(ctx, h, cols[j], 782, 24, MUTED, SANS, True, ta)
        line(ctx, 740, 808, 1780, 808, STROKE, 1.5, ta)
        for i, (name, _, cc, s1, s2) in enumerate(members):
            ra = ta * eo(prog(t, T.b[3] + 0.2 + i * 0.12, 0.35))
            yy = 846 + i * 44
            text(ctx, name, cols[0], yy, 24, TEXT, SANS, False, ra)
            text(ctx, f"{s1}/10", cols[1], yy, 24, TEXT, MONO, False, ra)
            text(ctx, f"{s2}/10", cols[2], yy, 24, GREEN, MONO, True, ra)


# ---------------------------------------------------------------- modernize

def s_modernize(ctx, t, T):
    c = SK["modernize"]
    header(ctx, t, "modernize", 8, "modernize", "Update an old PR, and decide whether it should still exist.", c)
    my, by = 480, 380
    fork = 300
    xs = [160 + 70 * k for k in range(18)]
    tip = xs[-1]
    a = eo(prog(t, 0.4, 0.5))
    t_new = T.b[1]
    hl = eo(prog(t, t_new, 0.5))
    rb = eio(prog(t, wd(T, "modernize", 3, "gets a rebase"), 1.2))
    base = lerp(fork, tip, rb)
    line(ctx, xs[0], my, tip, my, BLUE, 4, a)
    for k, x in enumerate(xs):
        if x <= fork:
            commit(ctx, x, my, BLUE, a, 0.8)
        else:
            commit(ctx, x, my, mix(DIM, BLUE, hl), a * eo(prog(t, 0.5 + k * 0.03, 0.3)), 0.8)
    text(ctx, "main", xs[0] - 10, my + 46, 22, BLUE, MONO, True, a)
    if hl > 0:
        box(ctx, fork + 30, my - 30, tip - fork - 10, 60, 30, None, hl * 0.9, BLUE, 2, dash=[8, 8])
        text(ctx, "everything that landed on main since the split", (fork + tip) / 2 + 10, my + 58, 24,
             BLUE, SANS, True, hl, "c")
    pr_x = [base + 100, base + 180, base + 260]
    arrow(ctx, (base, my), (pr_x[0], by), PURPLE, a, 4, c0=(base + 50, my), c1=(pr_x[0] - 50, by),
          head=0)
    line(ctx, pr_x[0], by, pr_x[-1], by, PURPLE, 4, a)
    for x in pr_x:
        commit(ctx, x, by, PURPLE, a, 0.8)
    tag(ctx, pr_x[0] - 20, by - 56, [("#212", PURPLE, True, MONO), ("  9 months old", MUTED, False, SANS)],
        PURPLE, 22, a)

    verdicts = [("MODERNIZE", "goal still useful, shape still right", "rebase, test, push", GREEN, "modernize,"),
                ("REWORK", "goal useful, implementation wrong", "explain the rewrite, stop", AMBER, "rework"),
                ("CLOSE", "superseded, or not worth the cost", "cite evidence, stop", RED, "close")]
    pick = eo(prog(t, T.b[3], 0.5))
    for i, (v, why, act, cc, w) in enumerate(verdicts):
        x = 110 + i * 580
        va, vdy = appear(t, wd(T, "modernize", 2, w), 0.4)
        va *= 1 - pick * 0.6 if i else 1
        card(ctx, x, 610 + vdy, 540, 220, cc, va, pick if i == 0 else 0.15)
        text(ctx, v, x + 34, 660 + vdy, 34, cc, MONO, True, va)
        text(ctx, why, x + 34, 720 + vdy, 24, TEXT, SANS, False, va)
        spans(ctx, [("→ ", MUTED, False, MONO), (act, MUTED, False, SANS)], x + 34, 774 + vdy, 24,
              SANS, va)

    x = 110
    x += tag(ctx, x, 910, [(I_CHECK + " ", GREEN, False, MONO), ("git range-diff", GREEN, True, MONO)], GREEN,
             24, eo(prog(t, wd(T, "modernize", 3, "range-diff"), 0.4))) + 20
    x += tag(ctx, x, 910, [("git push --force-with-lease", GREEN, True, MONO)], GREEN, 24,
             eo(prog(t, wd(T, "modernize", 3, "force-with-lease"), 0.4))) + 30
    text(ctx, "never merges or closes on its own", x, 910, 26, MUTED, SANS, False,
         eo(prog(t, wd(T, "modernize", 3, "never merges"), 0.4)))


# ---------------------------------------------------------------- takeover

def commit_row(ctx, x, y, sha, author, msg, ac, a, kept=0.0):
    if a <= 0:
        return
    commit(ctx, x + 20, y, ac, a, 0.6)
    text(ctx, sha, x + 50, y, 22, DIM, MONO, False, a)
    aw = text(ctx, author, x + 160, y, 22, ac, MONO, True, a)
    text(ctx, msg, x + 160 + aw + 18, y, 24, TEXT, SANS, False, a)
    if kept > 0:
        line(ctx, x + 160, y + 17, x + 160 + aw * kept, y + 17, GREEN, 3, a)


def s_takeover(ctx, t, T):
    c = SK["takeover"]
    header(ctx, t, "takeover", 9, "take over", "Finish someone else's PR, branch, or thread, and keep their credit.", c)
    alice = PURPLE
    a = eo(prog(t, 0.4, 0.5))
    card(ctx, 110, 320, 760, 380, alice, a)
    spans(ctx, [(I_PR + "  ", GREEN, False, MONO), ("#381", TEXT, True, MONO),
                ("  Fix reconnect storm", TEXT, False, SANS)], 140, 366, 28, MONO, a)
    spans(ctx, [("by ", MUTED, False, SANS), ("alice", alice, True, MONO), ("  ·  ", DIM, False, SANS),
                ("stalled for 3 weeks", AMBER, False, SANS)], 140, 410, 24, SANS, a)
    line(ctx, 110, 440, 870, 440, STROKE, 1.5, a)
    commit_row(ctx, 130, 485, "a1f3e2c", "alice", "retry with backoff", alice, a)
    commit_row(ctx, 130, 540, "7c9d0b1", "alice", "cap reconnect attempts", alice, a)
    text(ctx, 'agent thread: "almost done, tests are flaky"', 150, 610, 24, MUTED, SANS, False, a,
         italic=True)

    sa = eo(prog(t, wd(T, "takeover", 1, "context"), 0.35))
    if sa > 0:
        ctx.save()
        ctx.translate(690, 662)
        ctx.rotate(-0.12)
        ctx.scale(lerp(1.4, 1, sa), lerp(1.4, 1, sa))
        w = tw(ctx, "CONTEXT, NOT PROOF", 30, MONO, True) + 40
        box(ctx, -w / 2, -30, w, 60, 8, BG, sa * 0.85, ORANGE, 4)
        text(ctx, "CONTEXT, NOT PROOF", 0, 0, 30, ORANGE, MONO, True, sa, "c")
        ctx.restore()
    ra = eo(prog(t, wd(T, "takeover", 1, "checks the original"), 0.4))
    if ra > 0:
        mark(ctx, 140, 750, True, 24, ra)
        text(ctx, "reproduced the original failure itself", 176, 750, 26, TEXT, SANS, False, ra)

    t_new = T.b[2]
    na = eo(prog(t, t_new, 0.5))
    route(ctx, [(880, 510), (1000, 510)], c, eo(prog(t, t_new, 0.4)), 3, na)
    card(ctx, 1010, 320, 800, 380, c, na, 0.3)
    spans(ctx, [(I_BRANCH + "  ", c, False, MONO), ("takeover/reconnect-storm", c, True, MONO)], 1040,
          366, 26, MONO, na)
    line(ctx, 1010, 400, 1810, 400, STROKE, 1.5, na)
    kept = eo(prog(t, wd(T, "takeover", 2, "keep the"), 0.5))
    commit_row(ctx, 1030, 450, "5d2c9e1", "alice", "retry with backoff", alice,
               eo(prog(t, t_new + 0.3, 0.4)), kept)
    commit_row(ctx, 1030, 505, "b47a0f3", "alice", "cap reconnect attempts", alice,
               eo(prog(t, t_new + 0.5, 0.4)), kept)
    commit_row(ctx, 1030, 560, "e8b2a40", "agent", "fix flaky reconnect test", PINK,
               eo(prog(t, t_new + 0.9, 0.4)))
    ca = eo(prog(t, wd(T, "takeover", 2, "credit"), 0.4))
    text(ctx, "PR description: Continues #381 by @alice.", 1040, 640, 24, MUTED, MONO, False, ca * na)
    if kept > 0:
        tag(ctx, 1790, 477, [("authors kept", GREEN, True, SANS)], GREEN, 20, kept, "r")

    names = [("modernize", "modernizes"), ("file-pr", "files"), ("babysit-pr", "babysits")]
    widths = [tag_w(ctx, [(n, SK[n], True, MONO)], 28) for n, _ in names]
    total = sum(widths) + 2 * 90
    x = W / 2 - total / 2
    for i, (n, w) in enumerate(names):
        st = wd(T, "takeover", 3, w)
        tag(ctx, x, 880, [(n, SK[n], True, MONO)], SK[n], 28, eo(prog(t, st, 0.4)))
        if i:
            arrow(ctx, (x - 78, 880), (x - 12, 880), MUTED, eo(prog(t, st, 0.3)), 3)
        x += widths[i] + 90


# ---------------------------------------------------------------- graph

NODES = {
    "full-stop": (380, 250), "council": (1560, 250),
    "full-send": (380, 440), "takeover": (1400, 440),
    "sol-loop": (240, 640), "file-pr": (620, 640), "babysit-pr": (1000, 640), "modernize": (1400, 640),
    "leaving-pr-comments": (1000, 860),
}


def node_w(ctx, name):
    return tw(ctx, name, 30, MONO, True) + 56


def draw_node(ctx, name, a, g=0.0):
    cx, cy = NODES[name]
    w = node_w(ctx, name)
    c = SK[name]
    card(ctx, cx - w / 2, cy - 35, w, 70, c, a, g, r=35)
    text(ctx, name, cx, cy, 30, c, MONO, True, a, "c")


def s_graph(ctx, t, T):
    edges = [
        ("full-stop", "full-send", T.at(1, word_frac("graph", 1, "builds")), 0),
        ("full-send", "sol-loop", wd(T, "graph", 1, "sol loop"), 0),
        ("full-send", "file-pr", wd(T, "graph", 1, "file PR"), 0),
        ("full-send", "babysit-pr", wd(T, "graph", 1, "babysit PR"), 0),
        ("takeover", "modernize", wd(T, "graph", 2, "modernize"), 0),
        ("takeover", "file-pr", wd(T, "graph", 2, "file PR"), 0),
        ("takeover", "babysit-pr", wd(T, "graph", 2, "babysit PR"), 0),
        ("file-pr", "leaving-pr-comments", wd(T, "graph", 3, "goes through"), -90),
        ("babysit-pr", "leaving-pr-comments", wd(T, "graph", 3, "goes through") + 0.15, 0),
        ("modernize", "leaving-pr-comments", wd(T, "graph", 3, "goes through") + 0.3, 90),
    ]
    for src, dst, st, off in edges:
        (x0, y0), (x1, y1) = NODES[src], NODES[dst]
        c = SK[src]
        arrow(ctx, (x0, y0 + 36), (x1 + off, y1 - 40), c, eo(prog(t, st, 0.5)), 3, 0.85)
    # takeover -> leaving-pr-comments, routed around the right side
    st = wd(T, "graph", 3, "goes through") + 0.45
    tx, ty = NODES["takeover"]
    lx, ly = NODES["leaving-pr-comments"]
    route(ctx, [(tx + node_w(ctx, "takeover") / 2 + 4, ty), (1700, ty), (1700, ly),
                (lx + node_w(ctx, "leaving-pr-comments") / 2 + 8, ly)], SK["takeover"],
          eo(prog(t, st, 0.7)), 3, 0.85)
    t_alone = wd(T, "graph", 3, "council skill")
    for i, name in enumerate(NODES):
        a = eo(prog(t, 0.3 + i * 0.07, 0.4))
        g = pulse(t, t_alone) if name == "council" else 0.0
        draw_node(ctx, name, a, g)
    a = eo(prog(t, t_alone + 0.2, 0.4))
    text(ctx, "stands alone", NODES["council"][0], NODES["council"][1] + 64, 24, PURPLE, SANS, True, a, "c")


# ---------------------------------------------------------------- install

def s_install(ctx, t, T):
    t0 = T.at(0, 0.08)
    clone = {"cmd": "git clone https://github.com/t3dotgg/tstack", "t": t0, "cwd": "src", "br": None}
    cp1 = {"cmd": "cp -R tstack/skills/* ~/.claude/skills/", "t": wd(T, "install", 0, "copy"),
           "cwd": "src", "br": None}
    cp2 = {"cmd": "cp -R tstack/skills/* ~/.codex/skills/", "t": wd(T, "install", 0, "Codex"),
           "cwd": "src", "br": None}
    gh = {"cmd": "gh auth status", "t": T.b[1], "cwd": "src", "br": None}
    py = {"cmd": "python3 --version", "t": wd(T, "install", 1, "Python"), "cwd": "src", "br": None}
    entries = [clone, {"out": "Cloning into 'tstack'...", "c": MUTED}, cp1, cp2, gh,
               {"out": "github.com", "c": TEXT},
               {"out": [("  ✓ Logged in to github.com account you (keyring)", TEXT)]},
               py, {"out": "Python 3.14.8", "c": TEXT}]
    terminal(ctx, 110, 170, 1040, 480, "~/src", entries, t, 22, eo(prog(t, 0.2, 0.45)))

    a = eo(prog(t, T.b[2], 0.5))
    card(ctx, 1190, 170, 620, 330, PURPLE, a, 0.3)
    spans(ctx, [(I_FILE + "  ", PURPLE, False, MONO), ("CLAUDE.md", TEXT, True, MONO),
                ("  or AGENTS.md", MUTED, False, MONO)], 1220, 214, 24, MONO, a)
    line(ctx, 1190, 246, 1810, 246, STROKE, 1.5, a)
    for i, (s, cc) in enumerate([("## tstack", PURPLE), ("council members:", TEXT),
                                 ("  Claude Opus, GPT Sol,", TEXT), ("  Gemini Pro", TEXT)]):
        la = eo(prog(t, wd(T, "install", 2, "personal") + i * 0.12, 0.35))
        text(ctx, s, 1220, 294 + i * 44, 24, cc, MONO, i == 0, a * la)
    pa = eo(prog(t, wd(T, "install", 2, "so updates"), 0.4))
    para(ctx, "Your settings live here, so updating the skills keeps them.", 1190, 545, 26, 620,
         MUTED, SANS, False, pa)

    ea, edy = appear(t, T.e[2] + 0.4, 0.6)
    end = grad_text(ctx, "tstack", "tstack", W / 2, 790 + edy, 96, PINK, PURPLE, ea)
    del end
    text(ctx, "github.com/t3dotgg/tstack", W / 2, 885 + edy, 36, TEXT, MONO, True, ea, "c")
    text(ctx, "MIT license  ·  Claude Code  ·  Codex", W / 2, 945 + edy, 26, MUTED, SANS, False, ea, "c")


DRAW = {
    "title": s_title, "pipeline": s_pipeline, "sol": s_sol, "filepr": s_filepr,
    "babysit": s_babysit, "comments": s_comments, "fullsend": s_fullsend, "fullstop": s_fullstop,
    "council": s_council, "modernize": s_modernize, "takeover": s_takeover, "graph": s_graph,
    "install": s_install,
}
