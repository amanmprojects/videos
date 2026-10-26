"""One draw function per scene: draw(ctx, t, T) where t is seconds into the scene
and T holds the narration beat timings (T.b[i] start, T.e[i] end)."""
import math

from gfx import (
    AMBER, BG, BLUE, BRANCH, CYAN, DIM, GREEN, I_ARROW, I_BRANCH, I_CHECK, I_DB, I_FILE,
    I_FIRE, I_FLASK, I_FOLDER, I_LINK, I_PR, I_ROBOT, I_WARN, MONO, MUTED, PANEL, PURPLE,
    RED, SANS, STROKE, TERM_BG, TEXT, W, appear, arrow, back, box, chip, cmd_end, color,
    commit, eio, eo, folder_header, glow, lerp, line, mark, mix, para, pill, prog, row,
    route, rrect, spans, terminal, text, tw, wrap,
)


class Timing:
    def __init__(self, starts, ends, dur):
        self.b, self.e, self.dur = starts, ends, dur

    def at(self, i, f=0.0):
        return self.b[i] + f * (self.e[i] - self.b[i])


def fade_out(t, start, dur=0.4):
    return 1 - eo(prog(t, start, dur))


def pulse(t, start, dur=1.2):
    """0 -> 1 -> settles at 0.45; used for highlight glows."""
    if t < start:
        return 0.0
    p = (t - start) / dur
    return 0.45 + 0.55 * math.exp(-3 * p) * (1 if p > 0.15 else p / 0.15)


def ring(ctx, x, y, c, t, start, r=17):
    """Expanding ring that draws the eye to a commit."""
    if t < start:
        return
    p = (t - start) / 0.9
    if p > 1:
        return
    ctx.new_path()
    ctx.arc(x, y, r + 30 * eo(p), 0, 2 * math.pi)
    color(ctx, c, 0.7 * (1 - p))
    ctx.set_line_width(3)
    ctx.stroke()


def code_line(ctx, s, x, y, size, a=1.0):
    """Shell command with `git worktree <sub>` emphasised."""
    if s.startswith("git worktree "):
        rest = s[len("git worktree "):]
        sub, _, args = rest.partition(" ")
        parts = [("git worktree ", MUTED), (sub, AMBER, True), ((" " + args) if args else "", TEXT)]
    else:
        parts = [(s, TEXT)]
    return spans(ctx, parts, x, y, size, MONO, a)


# ---------------------------------------------------------------- 0 title

def s_title(ctx, t, T):
    a, dy = appear(t, 0.2, 0.7)
    spans(ctx, [("git ", MUTED, True), ("worktree", TEXT, True)], W / 2, 280 + dy, 124,
          MONO, a, align="c")
    a, dy = appear(t, 0.8, 0.6)
    text(ctx, "One repository. Many working directories.", W / 2, 400 + dy, 46, MUTED,
         SANS, False, a, "c")

    sa, sdy = appear(t, 1.6, 0.5)
    sw, sh = 440, 104
    sx, sy = W / 2 - sw / 2, 520 + sdy
    glow(ctx, sx, sy, sw, sh, AMBER, sa * 0.8, 18, 14)
    box(ctx, sx, sy, sw, sh, 18, PANEL, sa, AMBER, 2.5)
    text(ctx, I_DB, sx + 40, sy + sh / 2, 42, AMBER, MONO, False, sa)
    text(ctx, "app/.git", sx + 104, sy + 38, 32, TEXT, MONO, True, sa)
    text(ctx, "one copy of the history", sx + 104, sy + 74, 22, MUTED, SANS, False, sa)

    folders = [("app/", "feature", 500), ("app-hotfix/", "hotfix", 960),
               ("app-review/", "pr-482", 1420)]
    for i, (name, br, cx) in enumerate(folders):
        st = 2.3 + i * 0.35
        c = BRANCH[br]
        p = eio(prog(t, st, 0.7))
        y0, y1 = 520 + sh, 800
        arrow(ctx, (W / 2, y0), (cx, y1), c, p, 3, 0.75, c0=(W / 2, y0 + 90),
              c1=(cx, y1 - 90), head=0)
        fa, fdy = appear(t, st + 0.45, 0.5)
        fw, fh = 390, 132
        fx, fy = cx - fw / 2, y1 + fdy
        box(ctx, fx, fy, fw, fh, 16, PANEL, fa, mix(STROKE, c, 0.35), 2)
        text(ctx, I_FOLDER, fx + 30, fy + 44, 28, MUTED, MONO, False, fa)
        text(ctx, name, fx + 76, fy + 44, 28, TEXT, MONO, True, fa)
        pill(ctx, fx + 30, fy + 94, br, c, 20, fa)


# ---------------------------------------------------------------- 1 problem

def s_problem(ctx, t, T):
    a, dy = appear(t, 0.1)
    x, y, w, h = 110, 220 + dy, 720, 420
    box(ctx, x, y, w, h, 18, PANEL, a)
    folder_header(ctx, x, y, w, "app/", a, "feature")
    line(ctx, x, y + 76, x + w, y + 76, STROKE, 1.5, a)
    files = [(I_FILE, "api.py", None, ("M", AMBER)), (I_FILE, "app.py", None, ("M", AMBER)),
             (I_FILE, ".gitignore", None, None), (I_FOLDER, "node_modules/", "ignored", None),
             (I_FILE, ".env", "ignored", None)]
    for i, (ic, nm, note, badge) in enumerate(files):
        dim = note is not None
        row(ctx, x, y + 120 + i * 60, w, ic, nm, note, MUTED if dim else TEXT, a, 25,
            badge=badge, note_c=DIM)

    st = 0.7
    terminal(ctx, 110, 690, 720, 190, "~/app", [
        {"cmd": "git status --short", "t": st, "cwd": "app", "br": "feature"},
        {"out": [(" M", RED), (" api.py", TEXT)]},
        {"out": [(" M", RED), (" app.py", TEXT)]},
    ], t, 24, a)

    # incoming bug report
    ts = T.at(0, 0.62)
    ta, tdy = appear(t, ts, 0.45)
    shake = math.sin((t - ts) * 42) * 9 * max(0.0, 1 - (t - ts) / 0.55) if t > ts else 0
    tx, ty, tW, tH = 900 + shake, 220 + tdy, 910, 124
    box(ctx, tx, ty, tW, tH, 18, mix(PANEL, RED, 0.07), ta, RED, 2)
    text(ctx, I_FIRE, tx + 42, ty + tH / 2, 42, RED, MONO, False, ta)
    text(ctx, "Production is down", tx + 104, ty + 44, 32, TEXT, SANS, True, ta)
    text(ctx, "Crash on startup. The fix has to go on main.", tx + 104, ty + 86, 24, MUTED,
         SANS, False, ta)
    pill(ctx, tx + tW - 30, ty + 44, "main", BLUE, 20, ta, align="r")

    cards = [
        ("Stash and switch", "git stash && git switch main",
         "Files change under your editor. Undo it all afterwards.", False),
        ("Clone again", "git clone <url> app-2",
         "Second copy of history, second repository to sync.", False),
        ("Add a worktree", "git worktree add -b hotfix ../app-hotfix main",
         "Second directory, same repository.", True),
    ]
    for i, (title, code, note, ok) in enumerate(cards):
        st = T.b[i + 1] + 0.1
        ca, cdy = appear(t, st, 0.5)
        cx, cy, cw, ch = 900, 374 + i * 178 + cdy, 910, 160
        if ok:
            glow(ctx, cx, cy, cw, ch, AMBER, ca * eo(prog(t, st + 0.3, 0.6)), 18, 14)
        box(ctx, cx, cy, cw, ch, 18, PANEL, ca, AMBER if ok else STROKE, 2)
        text(ctx, title, cx + 34, cy + 40, 30, TEXT, SANS, True, ca)
        if ok:
            code_line(ctx, code, cx + 34, cy + 86, 23, ca)
        else:
            text(ctx, code, cx + 34, cy + 86, 23, MUTED, MONO, False, ca)
        text(ctx, note, cx + 34, cy + 128, 22, GREEN if ok else MUTED, SANS, False, ca)
        mark(ctx, cx + cw - 56, cy + ch / 2, ok, 32, eo(prog(t, st + 0.35, 0.4)))


# ---------------------------------------------------------------- 2 anatomy

def s_anatomy(ctx, t, T):
    a0 = eo(prog(t, 0.1, 0.5))
    sp = eio(prog(t, T.at(0, 0.55), 0.9))  # split progress

    # combined listing, before the split
    cx0, cy0, cw0 = 610, 330, 700
    ca = a0 * (1 - sp)
    box(ctx, cx0, cy0, cw0, 380, 18, PANEL, ca)
    folder_header(ctx, cx0, cy0, cw0, "app/", ca, "feature")
    line(ctx, cx0, cy0 + 76, cx0 + cw0, cy0 + 76, STROKE, 1.5, ca)

    # outer container that replaces it
    ox, oy, ow, oh = 110, 170, 1700, 800
    box(ctx, ox, oy, ow, oh, 22, None, sp, DIM, 2, dash=[10, 8])
    text(ctx, I_FOLDER + "  app/", ox + 30, oy + 36, 26, MUTED, MONO, True, sp)

    L = (150, 240, 780, 640)   # .git panel
    R = (990, 240, 780, 640)   # working tree panel
    pa = sp
    lx, ly, lw, lh = L
    rx, ry, rw, rh = R
    box(ctx, lx - (1 - sp) * 40, ly, lw, lh, 18, PANEL, pa, mix(STROKE, AMBER, 0.5), 2)
    box(ctx, rx + (1 - sp) * 40, ry, rw, rh, 18, PANEL, pa, mix(STROKE, PURPLE, 0.45), 2)
    chip(ctx, lx + lw - 24, ly + 38, "the repository", AMBER, 20, pa, "r")
    text(ctx, I_FOLDER, rx + 26, ry + 38, 28, MUTED, MONO, False, pa)
    text(ctx, "working tree", rx + 68, ry + 38, 28, TEXT, MONO, True, pa)
    pill(ctx, rx + rw - 24, ry + 38, "feature", PURPLE, 20, pa, align="r")
    line(ctx, lx, ly + 76, lx + lw, ly + 76, STROKE, 1.5, pa)
    line(ctx, rx, ry + 76, rx + rw, ry + 76, STROKE, 1.5, pa)

    # items that fly from the combined listing into the two panels
    fly = [
        (I_FOLDER, ".git/", AMBER, (cx0 + 26, cy0 + 120, 25), (lx + 26, ly + 38, 28), True),
        (I_FILE, "api.py", MUTED, (cx0 + 26, cy0 + 180, 25), (rx + 26, ry + 122, 25), False),
        (I_FILE, "app.py", MUTED, (cx0 + 26, cy0 + 240, 25), (rx + 26, ry + 180, 25), False),
        (I_FILE, ".gitignore", MUTED, (cx0 + 26, cy0 + 300, 25), (rx + 26, ry + 238, 25), False),
    ]
    for ic, nm, icol, (x0, y0, s0), (x1, y1, s1), bold in fly:
        fx, fy, fs = lerp(x0, x1, sp), lerp(y0, y1, sp), lerp(s0, s1, sp)
        text(ctx, ic, fx, fy, fs * 0.95, icol, MONO, False, a0)
        text(ctx, nm, fx + fs * 1.55, fy, fs, TEXT, MONO, bold and sp > 0.5, a0)
    if sp >= 1:
        text(ctx, "the files you edit", rx + rw - 30, ry + 180, 21, MUTED, SANS, False,
             eo(prog(t, T.at(2, 0.05), 0.5)), "r")

    # .git contents
    items = [("objects/", "every commit, tree, and file version"),
             ("refs/heads/", "branches: main, feature"),
             ("refs/tags/", "tags: v1.0"),
             ("config", "settings"),
             ("hooks/", "scripts git runs for you")]
    for i, (nm, note) in enumerate(items):
        ia, idy = appear(t, T.at(1, 0.22 + i * 0.13), 0.4)
        row(ctx, lx, ly + 132 + i * 66 + idy, lw, I_FOLDER if nm.endswith("/") else I_FILE,
            nm, note, TEXT, ia, 25, icolor=AMBER, note_x=lx + 300)

    # per-checkout state
    da = eo(prog(t, T.at(2, 0.28), 0.5))
    line(ctx, rx + 26, ry + 290, rx + rw - 26, ry + 290, STROKE, 1.5, da, dash=[6, 6])
    text(ctx, "STATE OF THIS CHECKOUT", rx + 26, ry + 328, 18, MUTED, SANS, True, da)
    ha, hdy = appear(t, T.at(2, 0.40), 0.45)
    row(ctx, rx, ry + 384 + hdy, rw, I_FILE, "HEAD", "ref: refs/heads/feature", TEXT, ha, 25,
        icolor=PURPLE, note_x=rx + 220, note_c=PURPLE, note_family=MONO)
    text(ctx, "what's checked out", rx + 220, ry + 418 + hdy, 20, MUTED, SANS, False, ha)
    xa, xdy = appear(t, T.at(2, 0.72), 0.45)
    row(ctx, rx, ry + 474 + xdy, rw, I_FILE, "index", "staging area", TEXT, xa, 25,
        icolor=PURPLE, note_x=rx + 220)
    fa = eo(prog(t, T.at(2, 0.9), 0.5))
    text(ctx, "Both live inside .git/, but there is one set per checkout.", rx + 26,
         ry + 580, 20, DIM, SANS, False, fa, italic=True)

    # 1 : 1
    ba, bdy = appear(t, T.b[3] + 0.2, 0.5)
    ctx.new_path()
    ctx.arc(960, ly + lh / 2, 26, 0, 2 * math.pi)
    color(ctx, BG, ba)
    ctx.fill_preserve()
    color(ctx, AMBER, ba)
    ctx.set_line_width(2)
    ctx.stroke()
    text(ctx, I_LINK, 960, ly + lh / 2, 22, AMBER, MONO, False, ba, "c")
    spans(ctx, [("1 repository", AMBER, True), ("  :  ", MUTED), ("1 working tree", PURPLE, True)],
          W / 2, 930 + bdy, 28, SANS, ba, align="c")


# ---------------------------------------------------------------- 3 add

def wt_box(ctx, x, y, w, name, branch, a, t, rows_spec, hl=0.0):
    """Worktree box: HEAD/index rows, then files."""
    h = 500
    c = BRANCH[branch]
    box(ctx, x, y, w, h, 18, PANEL, a, mix(STROKE, c, 0.45), 2)
    folder_header(ctx, x, y, w, name, a, branch)
    line(ctx, x, y + 76, x + w, y + 76, STROKE, 1.5, a)
    if hl > 0:
        for ry in (y + 118, y + 172):
            glow(ctx, x + 14, ry - 22, w - 28, 44, c, hl * a, 8, 8)
            rrect(ctx, x + 14, ry - 22, w - 28, 44, 8)
            color(ctx, c, 0.12 * hl * a)
            ctx.fill()
    row(ctx, x, y + 118, w, I_FILE, "HEAD", "→ " + branch, TEXT, a, 24, icolor=c,
        note_x=x + 170, note_c=c, note_family=MONO)
    row(ctx, x, y + 172, w, I_FILE, "index", "staging area", TEXT, a, 24, icolor=c,
        note_x=x + 170)
    line(ctx, x + 26, y + 206, x + w - 26, y + 206, STROKE, 1.5, a, dash=[6, 6])
    for i, spec in enumerate(rows_spec):
        spec = dict(spec)
        ra = a * spec.pop("a", 1.0)
        row(ctx, x, y + 240 + i * 52, w, a=ra, size=24, **spec)


def store_box(ctx, x, y, w, h, a, t, hotfix_a, hl=0.0):
    if hl > 0:
        glow(ctx, x, y, w, h, AMBER, hl * a, 18, 16)
    box(ctx, x, y, w, h, 18, mix(PANEL, AMBER, 0.04), a, AMBER, 2.5)
    text(ctx, I_DB, x + 28, y + 40, 30, AMBER, MONO, False, a)
    text(ctx, ".git", x + 76, y + 40, 30, TEXT, MONO, True, a)
    chip(ctx, x + w - 22, y + 40, "shared", AMBER, 19, a, "r")
    line(ctx, x, y + 78, x + w, y + 78, STROKE, 1.5, a)
    for i, (nm, note) in enumerate([("objects/", "history"), ("refs/", "branches"),
                                    ("config", "settings")]):
        row(ctx, x, y + 118 + i * 48, w, I_FOLDER if nm.endswith("/") else I_FILE, nm, note,
            TEXT, a, 22, icolor=AMBER, note_x=x + 210)
    px, py = x + 26, y + h - 40
    px += pill(ctx, px, py, "main", BLUE, 16, a) + 8
    px += pill(ctx, px, py, "feature", PURPLE, 16, a) + 8
    s = back(prog(t, hotfix_a, 0.5)) if t >= hotfix_a else 0
    if s > 0:
        ctx.save()
        ctx.translate(px, py)
        ctx.scale(s, s)
        pill(ctx, 0, 0, "hotfix", GREEN, 16, a)
        ctx.restore()


def s_add(ctx, t, T):
    a = eo(prog(t, 0.05, 0.4))
    cmd = {"cmd": "git worktree add -b hotfix ../app-hotfix main", "t": T.b[0] + 0.1,
           "cwd": "app", "br": "feature"}
    terminal(ctx, 110, 150, 1700, 200, "~/app", [
        cmd,
        {"out": "Preparing worktree (new branch 'hotfix')"},
        {"out": [("HEAD is now at ", MUTED), ("2709b36", AMBER), (" Initial commit", MUTED)]},
    ], t, 24, a)

    shared_hl = pulse(t, T.at(2, 0.3))
    own_hl = pulse(t, T.at(2, 0.68))
    by = 410

    left_rows = [
        dict(icon=I_FILE, name="api.py", badge=("M", AMBER)),
        dict(icon=I_FILE, name="app.py", badge=("M", AMBER)),
        dict(icon=I_FILE, name=".gitignore"),
        dict(icon=I_FOLDER, name="node_modules/", note="ignored", c=MUTED, note_c=DIM),
        dict(icon=I_FILE, name=".env", note="ignored", c=MUTED, note_c=DIM),
    ]
    wt_box(ctx, 110, by, 540, "app/", "feature", a, t, left_rows, own_hl)
    ua = eo(prog(t, T.at(2, 0.05), 0.5))
    text(ctx, I_CHECK + "  untouched: still on feature, edits intact", 110 + 270, by + 540, 21,
         GREEN, MONO, False, ua, "c")

    gone = eo(prog(t, T.at(3, 0.35), 0.5))
    right_rows = [
        dict(icon=I_FILE, name="api.py"),
        dict(icon=I_FILE, name="app.py"),
        dict(icon=I_FILE, name=".gitignore"),
        dict(icon=I_FOLDER, name="node_modules/", note="not copied", c=RED, note_c=RED,
             strike=True, icolor=RED, a=gone * 0.85),
        dict(icon=I_FILE, name=".env", note="not copied", c=RED, note_c=RED, strike=True,
             icolor=RED, a=gone * 0.85),
    ]
    st_r = T.at(1, 0.08)
    ra = eo(prog(t, st_r, 0.6))
    wt_box(ctx, 1270 + (1 - ra) * 80, by, 540, "app-hotfix/", "hotfix", ra, t, right_rows,
           own_hl)
    na = eo(prog(t, T.at(3, 0.72), 0.5))
    spans(ctx, [("then: ", MUTED), ("cd ../app-hotfix && npm install", AMBER)], 1270 + 270,
          by + 540, 21, MONO, na, align="c")

    sx, sy, sw, sh = 755, 530, 410, 300
    store_box(ctx, sx, sy, sw, sh, a, t, T.at(1, 0.5), shared_hl)
    mid = sy + sh / 2
    arrow(ctx, (650, mid), (sx - 6, mid), AMBER, a, 3, 0.8)
    arrow(ctx, (1270, mid), (sx + sw + 6, mid), AMBER, eo(prog(t, T.b[2] + 0.1, 0.5)), 3, 0.8)


# ---------------------------------------------------------------- 4 under the hood

def s_hood(ctx, t, T):
    a = eo(prog(t, 0.05, 0.4))
    # left: the linked worktree
    lx, ly, lw = 110, 170, 720
    box(ctx, lx, ly, lw, 330, 18, PANEL, a, mix(STROKE, GREEN, 0.45), 2)
    folder_header(ctx, lx, ly, lw, "~/app-hotfix/", a, "hotfix")
    line(ctx, lx, ly + 76, lx + lw, ly + 76, STROKE, 1.5, a)
    g = pulse(t, T.at(0, 0.5))
    if g > 0:
        glow(ctx, lx + 14, ly + 96, lw - 28, 44, AMBER, g * a, 8, 8)
        rrect(ctx, lx + 14, ly + 96, lw - 28, 44, 8)
        color(ctx, AMBER, 0.12 * g)
        ctx.fill()
    fa = eo(prog(t, T.at(0, 0.55), 0.4))
    row(ctx, lx, ly + 118, lw, I_FILE, ".git", "a file, not a folder" if fa > 0 else None,
        TEXT, a, 24, icolor=AMBER, note_c=mix(MUTED, AMBER, fa), note_x=lx + 170)
    for i, nm in enumerate(["api.py", "app.py", ".gitignore"]):
        row(ctx, lx, ly + 172 + i * 50, lw, I_FILE, nm, None, MUTED, a, 24)

    cat = {"cmd": "cat .git", "t": T.at(0, 0.62), "cwd": "app-hotfix", "br": "hotfix"}
    out_t = cmd_end(cat) + 0.3
    terminal(ctx, lx, 540, lw, 170, "~/app-hotfix", [
        cat,
        {"out": [("gitdir: ", MUTED), ("/home/you/app/.git/worktrees/app-hotfix", AMBER)],
         "t": out_t},
    ], t, 22, a)

    # right: the main repository's .git
    rx, ry, rw = 900, 170, 820
    rows = [
        (0, "objects/", None, I_FOLDER), (0, "refs/", None, I_FOLDER), (0, "config", None, I_FILE),
        (0, "hooks/", None, I_FOLDER), (0, "HEAD", "ref: refs/heads/feature", I_FILE),
        (0, "index", None, I_FILE), (0, "worktrees/", None, I_FOLDER),
        (1, "app-hotfix/", None, I_FOLDER), (2, "HEAD", "ref: refs/heads/hotfix", I_FILE),
        (2, "index", None, I_FILE), (2, "commondir", "../..", I_FILE),
        (2, "gitdir", "/home/you/app-hotfix/.git", I_FILE), (2, "logs/  refs/  ORIG_HEAD", None, None),
    ]
    rh = 54
    y_of = [ry + 116 + i * rh for i in range(len(rows))]
    box(ctx, rx, ry, rw, 116 + len(rows) * rh, 18, PANEL, a, mix(STROKE, AMBER, 0.5), 2)
    text(ctx, I_DB, rx + 28, ry + 38, 28, AMBER, MONO, False, a)
    text(ctx, "~/app/.git/", rx + 72, ry + 38, 28, TEXT, MONO, True, a)
    line(ctx, rx, ry + 76, rx + rw, ry + 76, STROKE, 1.5, a)

    shared_hl = [pulse(t, T.at(3, 0.08 + i * 0.1)) for i in range(4)]
    admin_hl = pulse(t, T.at(1, 0.55))
    own_hl = pulse(t, T.at(2, 0.12))
    common_hl = pulse(t, T.at(2, 0.48))
    hls = {0: (shared_hl[0], AMBER), 1: (shared_hl[1], AMBER), 2: (shared_hl[2], AMBER),
           3: (shared_hl[3], AMBER), 7: (admin_hl, AMBER), 8: (own_hl, GREEN),
           9: (own_hl, GREEN), 10: (common_hl, AMBER)}
    for i, (ind, nm, note, ic) in enumerate(rows):
        ra = a if i < 7 else eo(prog(t, T.at(1, 0.25 + (i - 7) * 0.06), 0.4))
        hv, hc = hls.get(i, (0, None))
        if hv > 0:
            rrect(ctx, rx + 14 + ind * 34, y_of[i] - 22, rw - 28 - ind * 34, 44, 8)
            color(ctx, hc, 0.14 * hv * ra)
            ctx.fill()
        tc = DIM if ic is None else (TEXT if i >= 7 else mix(MUTED, TEXT, 0.5))
        row(ctx, rx, y_of[i], rw, ic, nm, note, tc, ra, 22,
            icolor=AMBER if i < 4 or i == 7 else MUTED, indent=ind, note_x=rx + 440,
            note_c=GREEN if i == 8 else (AMBER if i == 10 else MUTED), note_family=MONO)
    sa = eo(prog(t, T.at(3, 0.45), 0.5))
    chip(ctx, rx + rw - 30, (y_of[1] + y_of[2]) / 2, "shared by every worktree", AMBER, 19, sa,
         "r", fill_a=0.22)

    # arrows
    fs = 22
    out_y = 540 + 48 + 22 + fs * 0.5 + fs * 1.62
    end_x = lx + 28 + tw(ctx, "gitdir: /home/you/app/.git/worktrees/app-hotfix", fs, MONO)
    p1 = eio(prog(t, T.at(1, 0.1), 0.9))
    arrow(ctx, (end_x + 8, out_y), (rx + 26 + 34 - 10, y_of[7]), AMBER, p1, 3,
          c0=(end_x + 150, out_y), c1=(rx - 60, y_of[7]))
    p2 = eio(prog(t, T.at(2, 0.55), 1.0))
    sx = rx + 440 + tw(ctx, "../..", 18, MONO) + 18
    ox = rx + rw + 56
    route(ctx, [(sx, y_of[10]), (ox, y_of[10]), (ox, ry + 38), (rx + 290, ry + 38)], AMBER, p2, 3)


# ---------------------------------------------------------------- 5 shared commits

def s_shared(ctx, t, T):
    a = eo(prog(t, 0.05, 0.4))
    commit_cmd = {"cmd": 'git commit -am "Fix crash on startup"', "t": T.b[0] + 0.2,
                  "cwd": "app-hotfix", "br": "hotfix"}
    tc = cmd_end(commit_cmd) + 0.25
    terminal(ctx, 110, 190, 940, 230, "~/app-hotfix", [
        commit_cmd,
        {"out": [("[hotfix ", TEXT), ("9df1d09", AMBER), ("] Fix crash on startup", TEXT)],
         "t": tc},
        {"out": " 1 file changed, 1 insertion(+)"},
    ], t, 23, a)

    log_cmd = {"cmd": "git log --oneline hotfix", "t": T.at(1, 0.45), "cwd": "app",
               "br": "feature"}
    tl = cmd_end(log_cmd) + 0.25
    br_cmd = {"cmd": "git branch", "t": T.b[2] + 0.3, "cwd": "app", "br": "feature"}
    tb = cmd_end(br_cmd) + 0.25
    terminal(ctx, 110, 460, 940, 460, "~/app", [
        log_cmd,
        {"out": [("9df1d09", AMBER), (" Fix crash on startup", TEXT)], "t": tl,
         "hl": (tl + 0.2, GREEN)},
        {"out": [("2709b36", AMBER), (" Initial commit", TEXT)]},
        {"gap": True, "t": br_cmd["t"]},
        br_cmd,
        {"out": [("* feature", GREEN)], "t": tb},
        {"out": [("+ hotfix", CYAN)], "hl": (T.at(2, 0.5), CYAN)},
        {"out": "  main", "c": TEXT},
    ], t, 23, a)

    # commit graph
    gx, gy, gw, gh = 1090, 190, 720, 730
    box(ctx, gx, gy, gw, gh, 18, PANEL, a)
    text(ctx, "commit graph", gx + 28, gy + 38, 24, MUTED, SANS, True, a)
    chip(ctx, gx + gw - 24, gy + 38, "one copy, in app/.git", AMBER, 18, a, "r")
    A, B, C = (1205, 600), (1450, 410), (1450, 790)
    arrow(ctx, A, B, PURPLE, a, 4, a, c0=(A[0] + 130, A[1]), c1=(B[0] - 130, B[1]), head=0)
    pc = eo(prog(t, tc, 0.5))
    arrow(ctx, A, C, GREEN, pc, 4, a, c0=(A[0] + 130, A[1]), c1=(C[0] - 130, C[1]), head=0)
    commit(ctx, *A, BLUE, a)
    commit(ctx, *B, PURPLE, a)
    commit(ctx, *C, GREEN, a, back(prog(t, tc + 0.25, 0.45)))
    for node, c, start in ((C, GREEN, tl), (A, BLUE, tl + 0.15)):
        ring(ctx, *node, c, t, start)
    text(ctx, "2709b36", A[0], A[1] + 46, 20, AMBER, MONO, False, a, "c")
    text(ctx, "Initial commit", A[0], A[1] + 74, 20, MUTED, SANS, False, a, "c")
    text(ctx, "250a572", B[0] + 36, B[1] - 14, 20, AMBER, MONO, False, a)
    text(ctx, "Start feature", B[0] + 36, B[1] + 14, 20, MUTED, SANS, False, a)
    ca = eo(prog(t, tc + 0.3, 0.4))
    text(ctx, "9df1d09", C[0] + 36, C[1] - 14, 20, AMBER, MONO, False, ca)
    text(ctx, "Fix crash on startup", C[0] + 36, C[1] + 14, 20, MUTED, SANS, False, ca)

    pill(ctx, A[0], A[1] - 58, "main", BLUE, 19, a, align="c")
    pill(ctx, B[0], B[1] - 58, "feature", PURPLE, 19, a, align="c")
    text(ctx, I_FOLDER + " app/", B[0] + 92, B[1] - 58, 18, MUTED, MONO, False, a)
    mp = eio(prog(t, tc + 0.1, 0.7))
    hx, hy = lerp(A[0], C[0], mp), lerp(A[1] - 104, C[1] - 58, mp)
    pill(ctx, hx, hy, "hotfix", GREEN, 19, a, align="c")
    text(ctx, I_FOLDER + " app-hotfix/", hx + 88, hy, 18, MUTED, MONO, False, a)


# ---------------------------------------------------------------- 6 one branch rule

def head_box(ctx, x, y, w, name, branch, a, lines):
    """lines: [(label, value_parts)]"""
    c = BRANCH.get(branch, CYAN)
    box(ctx, x, y, w, 300, 18, PANEL, a, mix(STROKE, c, 0.45), 2)
    folder_header(ctx, x, y, w, name, a, branch)
    line(ctx, x, y + 76, x + w, y + 76, STROKE, 1.5, a)
    for i, (label, parts) in enumerate(lines):
        text(ctx, label, x + 28, y + 112 + i * 96, 20, MUTED, SANS, True, a)
        spans(ctx, parts, x + 28, y + 148 + i * 96, 25, MONO, a)


def s_rule(ctx, t, T):
    ba, bdy = appear(t, T.b[0] + 0.2, 0.5)
    spans(ctx, [(I_BRANCH + "  ", AMBER, False, MONO), ("A branch can be checked out in ", TEXT, True),
                ("only one", AMBER, True), (" worktree at a time.", TEXT, True)],
          W / 2, 185 + bdy, 38, SANS, ba, align="c")

    a = eo(prog(t, T.b[1], 0.4))
    sw = {"cmd": "git switch hotfix", "t": T.b[1] + 0.25, "cwd": "app", "br": "feature"}
    det = {"cmd": "git worktree add --detach ../app-review hotfix", "t": T.at(3, 0.3),
           "cwd": "app", "br": "feature"}
    terminal(ctx, 110, 250, 1700, 330, "~/app", [
        sw,
        {"out": "fatal: 'hotfix' is already used by worktree at '/home/you/app-hotfix'",
         "c": RED, "t": cmd_end(sw) + 0.3, "hl": (cmd_end(sw) + 0.4, RED)},
        {"gap": True, "t": det["t"]},
        det,
        {"out": [("Preparing worktree (detached HEAD ", MUTED), ("9df1d09", AMBER), (")", MUTED)]},
        {"out": [("HEAD is now at ", MUTED), ("9df1d09", AMBER), (" Fix crash on startup", MUTED)]},
    ], t, 24, a)

    # why: what would happen if two worktrees shared a branch
    wa = eo(prog(t, T.b[2], 0.5)) * fade_out(t, T.b[3], 0.4)
    if wa > 0:
        text(ctx, "If git allowed it:", 110, 640, 24, MUTED, SANS, False, wa, italic=True)
        moved = eio(prog(t, T.at(2, 0.33), 0.7))
        stale = eo(prog(t, T.at(2, 0.62), 0.5))
        newv = "new commit" if moved > 0.5 else "9df1d09"
        head_box(ctx, 110, 680, 540, "app-hotfix/", "hotfix", wa, [
            ("HEAD", [("hotfix → ", GREEN), (newv, AMBER)]),
            ("files + index", [(newv, AMBER)]),
        ])
        head_box(ctx, 1270, 680, 540, "app/", "hotfix", wa, [
            ("HEAD", [("hotfix → ", GREEN), (newv, AMBER)]),
            ("files + index", [("9df1d09", mix(AMBER, RED, stale)),
                               ("   ≠ HEAD" if stale > 0 else "", RED)]),
        ])
        if stale > 0:
            text(ctx, I_WARN, 1270 + 540 - 44, 680 + 244, 28, RED, MONO, False, wa * stale, "c")
        C, N = (800, 880), (1120, 880)
        pn = eo(prog(t, T.at(2, 0.28), 0.4))
        arrow(ctx, C, N, GREEN, pn, 4, wa, head=0)
        commit(ctx, *C, GREEN, wa)
        commit(ctx, *N, GREEN, wa, back(prog(t, T.at(2, 0.3), 0.45)))
        text(ctx, "9df1d09", C[0], C[1] + 44, 20, AMBER, MONO, False, wa, "c")
        text(ctx, "new commit", N[0], N[1] + 44, 20, AMBER, MONO, False, wa * pn, "c")
        text(ctx, "committed from app-hotfix/", N[0], N[1] + 72, 18, MUTED, SANS, False,
             wa * pn, "c")
        pill(ctx, lerp(C[0], N[0], moved), C[1] - 58, "hotfix", GREEN, 19, wa, align="c")

    # --detach: same commit, branch claimed once
    da = eo(prog(t, T.at(3, 0.55), 0.5))
    if da > 0:
        text(ctx, "--detach: same commit, no branch claimed", 110, 640, 24, MUTED, MONO, False,
             da)
        head_box(ctx, 110, 680, 540, "app-hotfix/", "hotfix", da, [
            ("HEAD", [("hotfix → ", GREEN), ("9df1d09", AMBER)]),
            ("files + index", [("9df1d09", AMBER)]),
        ])
        head_box(ctx, 1270, 680, 540, "app-review/", "detached", da, [
            ("HEAD", [("9df1d09", AMBER), ("  (no branch)", CYAN)]),
            ("files + index", [("9df1d09", AMBER)]),
        ])
        C = (960, 860)
        arrow(ctx, (650, 790), (C[0] - 26, C[1] - 6), GREEN, eo(prog(t, T.at(3, 0.65), 0.5)),
              3, da, bend=-40)
        arrow(ctx, (1270, 790), (C[0] + 26, C[1] - 6), CYAN, eo(prog(t, T.at(3, 0.72), 0.5)),
              3, da, bend=40)
        commit(ctx, *C, GREEN, da)
        text(ctx, "9df1d09", C[0], C[1] + 44, 20, AMBER, MONO, False, da, "c")
        pill(ctx, C[0], C[1] - 58, "hotfix", GREEN, 19, da, align="c")


# ---------------------------------------------------------------- 7 cleanup

def s_cleanup(ctx, t, T):
    a = eo(prog(t, 0.05, 0.4))
    ls1 = {"cmd": "git worktree list", "t": T.b[0] + 0.15, "cwd": "app", "br": "feature"}
    rm = {"cmd": "git worktree remove ../app-review", "t": T.b[1] + 0.2, "cwd": "app",
          "br": "feature"}
    ls2 = {"cmd": "git worktree list", "t": T.at(1, 0.3), "cwd": "app", "br": "feature"}
    rf = {"cmd": "rm -rf ../app-hotfix", "t": T.b[2] + 0.2, "cwd": "app", "br": "feature"}
    pr = {"cmd": "git worktree prune -v", "t": T.at(2, 0.52), "cwd": "app", "br": "feature"}
    br = {"cmd": "git branch", "t": T.b[3] + 0.2, "cwd": "app", "br": "feature"}

    def wl(path, h, ref, c):
        return {"out": [(path, TEXT), (h, AMBER), (ref, c)]}

    terminal(ctx, 110, 170, 1120, 830, "~/app", [
        ls1,
        wl("/home/you/app        ", "250a572 ", "[feature]", PURPLE),
        wl("/home/you/app-hotfix ", "9df1d09 ", "[hotfix]", GREEN),
        wl("/home/you/app-review ", "9df1d09 ", "(detached HEAD)", CYAN),
        {"gap": True, "t": rm["t"]},
        rm, ls2,
        wl("/home/you/app        ", "250a572 ", "[feature]", PURPLE),
        wl("/home/you/app-hotfix ", "9df1d09 ", "[hotfix]", GREEN),
        {"gap": True, "t": rf["t"]},
        rf, pr,
        {"out": "Removing worktrees/app-hotfix: gitdir file points to non-existent location",
         "c": MUTED},
        {"gap": True, "t": br["t"]},
        br,
        {"out": "* feature", "c": GREEN},
        {"out": "  hotfix", "c": TEXT, "hl": (T.at(3, 0.25), GREEN)},
        {"out": "  main", "c": TEXT},
    ], t, 22, a)

    cx, cw = 1290, 520

    def card(i, y, h, title, body, ok=None, extra=None):
        ca, cdy = appear(t, T.b[i] + 0.1, 0.5)
        if ca <= 0:
            return
        y += cdy
        box(ctx, cx, y, cw, h, 16, PANEL, ca)
        if title.startswith("git"):
            code_line(ctx, title, cx + 28, y + 40, 22, ca)
        else:
            spans(ctx, [(I_CHECK + "  ", GREEN, False, MONO), (title, GREEN, True)], cx + 28,
                  y + 40, 24, SANS, ca)
        para(ctx, body, cx + 28, y + 86, 22, cw - 56, MUTED, SANS, False, ca)
        if extra:
            extra(y, ca)

    card(0, 170, 160, "git worktree list", "Every worktree, its commit, and its branch.")

    def refusal(y, ca):
        ea = ca * eo(prog(t, T.at(1, 0.55), 0.5))
        box(ctx, cx + 20, y + 158, cw - 40, 84, 10, TERM_BG, ea, mix(STROKE, RED, 0.5), 1.5)
        msg = "fatal: '../app-hotfix' contains modified or untracked files, use --force to delete it"
        for j, ln in enumerate(wrap(ctx, msg, 16, cw - 76, MONO)):
            text(ctx, ln, cx + 38, y + 186 + j * 27, 16, RED, MONO, False, ea)

    card(1, 350, 270, "git worktree remove <path>",
         "Deletes the folder and its admin folder. If the worktree is dirty:", extra=refusal)
    card(2, 640, 160, "git worktree prune", "Clears admin folders left by deleted worktrees.")
    card(3, 820, 180, "Branches stay",
         "hotfix and its commit 9df1d09 are still in the repository.")


# ---------------------------------------------------------------- 8 uses

def s_uses(ctx, t, T):
    ha, hdy = appear(t, T.b[0] + 0.1, 0.5)
    text(ctx, "Use a worktree when you need two branches at once", W / 2, 190 + hdy, 42, TEXT,
         SANS, True, ha, "c")
    cards = [
        (GREEN, I_FIRE, "Hotfix next to unfinished work",
         ["git worktree add -b hotfix ../app-hotfix main"]),
        (CYAN, I_PR, "Review a PR without losing your place",
         ["git fetch origin pull/482/head:pr-482", "git worktree add ../app-pr-482 pr-482"]),
        (BLUE, I_FLASK, "Run slow tests while you keep coding",
         ["git worktree add ../app-tests release", "cd ../app-tests && make test"]),
        (PURPLE, I_ROBOT, "One directory per coding agent",
         ["git worktree add -b agent-1 ../agent-1", "git worktree add -b agent-2 ../agent-2"]),
    ]
    for i, (c, icon, title, code) in enumerate(cards):
        ca, cdy = appear(t, T.b[i + 1], 0.5)
        if ca <= 0:
            continue
        x = 110 + (i % 2) * 870
        y = 280 + (i // 2) * 370 + cdy
        w, h = 830, 340
        box(ctx, x, y, w, h, 18, PANEL, ca, mix(STROKE, c, 0.4), 2)
        ctx.new_path()
        ctx.arc(x + 66, y + 70, 36, 0, 2 * math.pi)
        color(ctx, c, 0.15 * ca)
        ctx.fill()
        text(ctx, icon, x + 66, y + 70, 34, c, MONO, False, ca, "c")
        lines = wrap(ctx, title, 30, w - 170, SANS, True)
        for j, ln in enumerate(lines):
            text(ctx, ln, x + 126, y + 70 + (j - (len(lines) - 1) / 2) * 40, 30, TEXT, SANS,
                 True, ca)
        box(ctx, x + 28, y + 150, w - 56, 160, 12, TERM_BG, ca, STROKE, 1.5)
        for j, ln in enumerate(code):
            ly = y + 230 + (j - (len(code) - 1) / 2) * 44
            text(ctx, "$", x + 52, ly, 22, DIM, MONO, False, ca)
            code_line(ctx, ln, x + 82, ly, 22, ca)


# ---------------------------------------------------------------- 9 recap

def s_recap(ctx, t, T):
    ta, tdy = appear(t, T.b[0] + 0.1, 0.5)
    text(ctx, "One repository, many working directories.", W / 2, 180 + tdy, 50, TEXT, SANS,
         True, ta, "c")

    cols = [
        (110, AMBER, I_DB, "Shared", T.b[1] + 0.1,
         [("objects/", "all history"), ("refs/", "branches and tags"), ("config, hooks/", ""),
          ("refs/stash", "the stash")]),
        (980, GREEN, I_FOLDER, "Per worktree", T.at(1, 0.52),
         [("HEAD", "what's checked out"), ("index", "staging area"),
          ("files on disk", "tracked, untracked, ignored")]),
    ]
    for x, c, icon, title, st, items in cols:
        ca, cdy = appear(t, st, 0.5)
        y = 260 + cdy
        box(ctx, x, y, 830, 340, 18, PANEL, ca, mix(STROKE, c, 0.6), 2)
        text(ctx, icon, x + 32, y + 46, 30, c, MONO, False, ca)
        text(ctx, title, x + 80, y + 46, 32, c, SANS, True, ca)
        line(ctx, x, y + 88, x + 830, y + 88, STROKE, 1.5, ca)
        for j, (nm, note) in enumerate(items):
            iy = y + 128 + j * 54
            text(ctx, nm, x + 32, iy, 25, TEXT, MONO, True, ca)
            text(ctx, note, x + 340, iy, 22, MUTED, SANS, False, ca)

    ra, rdy = appear(t, T.b[2] + 0.1, 0.5)
    box(ctx, 110, 640 + rdy, 1700, 90, 16, mix(PANEL, RED, 0.06), ra, mix(STROKE, RED, 0.6), 2)
    spans(ctx, [(I_BRANCH + "  ", RED, False, MONO), ("Each branch is checked out in at most one worktree.",
                                         TEXT, True)], W / 2, 685 + rdy, 30, SANS, ra,
          align="c")

    sa, sdy = appear(t, T.e[2] + 0.4, 0.6)
    y = 770 + sdy
    box(ctx, 110, y, 1700, 240, 16, TERM_BG, sa, STROKE, 2)
    cmds = [("git worktree add -b <branch> <path> <start>", "# new directory on a new branch"),
            ("git worktree list", "# every worktree and its branch"),
            ("git worktree remove <path>", "# delete one when you're done"),
            ("git worktree prune", "# forget folders deleted by hand")]
    for j, (cmd, note) in enumerate(cmds):
        ry = y + 50 + j * 47
        text(ctx, "$", 150, ry, 24, DIM, MONO, False, sa)
        code_line(ctx, cmd, 184, ry, 24, sa)
        text(ctx, note, 1000, ry, 22, DIM, MONO, False, sa)


DRAW = {
    "title": s_title, "problem": s_problem, "anatomy": s_anatomy, "add": s_add,
    "hood": s_hood, "shared": s_shared, "rule": s_rule, "cleanup": s_cleanup,
    "uses": s_uses, "recap": s_recap,
}
