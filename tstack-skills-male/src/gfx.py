"""Drawing primitives for the worktree explainer. Pure pycairo, 1920x1080."""
import math
import cairo

W, H = 1920, 1080
FPS = 30

SANS = "Noto Sans"
MONO = "JetBrainsMono Nerd Font"


def hexc(s):
    s = s.lstrip("#")
    return tuple(int(s[i:i + 2], 16) / 255 for i in (0, 2, 4))


BG = hexc("#0d1017")
PANEL = hexc("#151a24")
PANEL2 = hexc("#1b2130")
STROKE = hexc("#2a3142")
TEXT = hexc("#e6e9ef")
MUTED = hexc("#8a93a6")
DIM = hexc("#4b5366")
AMBER = hexc("#e5b567")
BLUE = hexc("#7aa2f7")
PURPLE = hexc("#bb9af7")
GREEN = hexc("#9ece6a")
RED = hexc("#f7768e")
CYAN = hexc("#7dcfff")
TERM_BG = hexc("#0a0d13")

BRANCH = {"main": BLUE, "feature": PURPLE, "hotfix": GREEN, "detached": CYAN,
          "release": BLUE, "pr-482": CYAN}

# Nerd Font icons
I_FOLDER = "\uf07b"
I_FILE = "\uf016"
I_BRANCH = "\ue725"
I_CHECK = "\uf00c"
I_X = "\uf00d"
I_WARN = "\uf071"
I_DB = "\uf1c0"
I_ARROW = "\uf061"
I_BOLT = "\uf0e7"
I_LINK = "\uf0c1"
I_ROBOT = "\U000f06a9"
I_EYE = "\uf06e"
I_FLASK = "\uf0c3"
I_FIRE = "\uf06d"
I_PR = "\uf407"
I_TERM = "\uf120"


# ---------- timing ----------

def clamp(v, lo=0.0, hi=1.0):
    return lo if v < lo else hi if v > hi else v


def prog(t, start, dur=0.45):
    if dur <= 0:
        return 1.0 if t >= start else 0.0
    return clamp((t - start) / dur)


def eo(p):
    return 1 - (1 - p) ** 3


def eio(p):
    return 4 * p ** 3 if p < 0.5 else 1 - (-2 * p + 2) ** 3 / 2


def back(p):
    c1, c3 = 1.70158, 2.70158
    return 1 + c3 * (p - 1) ** 3 + c1 * (p - 1) ** 2


def lerp(a, b, p):
    return a + (b - a) * p


def mix(c1, c2, p):
    return tuple(lerp(a, b, p) for a, b in zip(c1, c2))


def appear(t, start, dur=0.45):
    """(alpha, y_offset) for a fade-and-rise entrance."""
    p = eo(prog(t, start, dur))
    return p, (1 - p) * 18


# ---------- context ----------

def new_surface():
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    ctx = cairo.Context(surf)
    fo = cairo.FontOptions()
    fo.set_antialias(cairo.ANTIALIAS_GRAY)
    fo.set_hint_style(cairo.HINT_STYLE_NONE)
    fo.set_hint_metrics(cairo.HINT_METRICS_OFF)
    ctx.set_font_options(fo)
    return surf, ctx


def color(ctx, c, a=1.0):
    ctx.set_source_rgba(c[0], c[1], c[2], a)


def font(ctx, size, family=SANS, bold=False, italic=False):
    ctx.select_font_face(family,
                         cairo.FONT_SLANT_ITALIC if italic else cairo.FONT_SLANT_NORMAL,
                         cairo.FONT_WEIGHT_BOLD if bold else cairo.FONT_WEIGHT_NORMAL)
    ctx.set_font_size(size)


def tw(ctx, s, size, family=SANS, bold=False):
    font(ctx, size, family, bold)
    return ctx.text_extents(s).x_advance


def text(ctx, s, x, y, size, c=TEXT, family=SANS, bold=False, a=1.0, align="l",
         italic=False):
    """Draw text with y as the vertical center of the line. Returns width."""
    if a <= 0 or not s:
        return tw(ctx, s, size, family, bold) if s else 0
    font(ctx, size, family, bold, italic)
    w = ctx.text_extents(s).x_advance
    asc, desc = ctx.font_extents()[:2]
    if align == "c":
        x -= w / 2
    elif align == "r":
        x -= w
    color(ctx, c, a)
    ctx.move_to(x, y + (asc - desc) / 2)
    ctx.show_text(s)
    return w


def spans(ctx, parts, x, y, size, family=MONO, a=1.0, bold=False, align="l"):
    """parts: [(text, color)], [(text, color, bold)] or [(text, color, bold, family)].
    y is line center."""
    def fam(p):
        return p[3] if len(p) > 3 else family

    total = sum(tw(ctx, p[0], size, fam(p), p[2] if len(p) > 2 else bold) for p in parts)
    if align == "c":
        x -= total / 2
    for p in parts:
        b = p[2] if len(p) > 2 else bold
        x += text(ctx, p[0], x, y, size, p[1], fam(p), b, a)
    return total


def wrap(ctx, s, size, maxw, family=SANS, bold=False):
    words, lines, cur = s.split(), [], ""
    for wd in words:
        trial = (cur + " " + wd).strip()
        if tw(ctx, trial, size, family, bold) <= maxw or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = wd
    if cur:
        lines.append(cur)
    return lines


def para(ctx, s, x, y, size, maxw, c=TEXT, family=SANS, bold=False, a=1.0, lh=1.35,
         align="l"):
    lines = wrap(ctx, s, size, maxw, family, bold)
    for i, ln in enumerate(lines):
        text(ctx, ln, x, y + i * size * lh, size, c, family, bold, a, align)
    return len(lines) * size * lh


# ---------- shapes ----------

def rrect(ctx, x, y, w, h, r):
    r = min(r, w / 2, h / 2)
    ctx.new_sub_path()
    ctx.arc(x + w - r, y + r, r, -math.pi / 2, 0)
    ctx.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    ctx.arc(x + r, y + h - r, r, math.pi / 2, math.pi)
    ctx.arc(x + r, y + r, r, math.pi, 3 * math.pi / 2)
    ctx.close_path()


def box(ctx, x, y, w, h, r=16, fill=PANEL, a=1.0, stroke=STROKE, lw=2, sa=None,
        dash=None):
    if a <= 0:
        return
    rrect(ctx, x, y, w, h, r)
    if fill is not None:
        color(ctx, fill, a)
        ctx.fill_preserve()
    if stroke is not None:
        color(ctx, stroke, a if sa is None else sa * a)
        ctx.set_line_width(lw)
        if dash:
            ctx.set_dash(dash)
        ctx.stroke()
        ctx.set_dash([])
    else:
        ctx.new_path()


def glow(ctx, x, y, w, h, c, a, r=14, spread=10):
    """Soft halo behind a rect: a few expanding translucent strokes."""
    if a <= 0:
        return
    for i in range(spread, 0, -2):
        rrect(ctx, x - i, y - i, w + 2 * i, h + 2 * i, r + i)
        color(ctx, c, a * 0.05)
        ctx.fill()


def pill(ctx, x, y, label, c, size=22, a=1.0, icon=I_BRANCH, align="l"):
    """Branch-style pill. y is the vertical center. Returns width."""
    if a <= 0:
        return 0
    pad = size * 0.55
    iw = tw(ctx, icon + " ", size * 0.9, MONO) if icon else 0
    w = iw + tw(ctx, label, size, MONO, True) + pad * 2
    h = size * 1.6
    if align == "r":
        x -= w
    elif align == "c":
        x -= w / 2
    rrect(ctx, x, y - h / 2, w, h, h / 2)
    color(ctx, c, 0.16 * a)
    ctx.fill_preserve()
    color(ctx, c, 0.55 * a)
    ctx.set_line_width(1.5)
    ctx.stroke()
    cx = x + pad
    if icon:
        cx += text(ctx, icon + " ", cx, y, size * 0.9, c, MONO, False, a)
    text(ctx, label, cx, y, size, c, MONO, True, a)
    return w


def chip(ctx, x, y, label, c, size=20, a=1.0, align="l", fill_a=0.14):
    if a <= 0:
        return 0
    pad = size * 0.5
    w = tw(ctx, label, size, MONO, True) + pad * 2
    h = size * 1.5
    if align == "r":
        x -= w
    elif align == "c":
        x -= w / 2
    rrect(ctx, x, y - h / 2, w, h, 6)
    color(ctx, c, fill_a * a)
    ctx.fill()
    text(ctx, label, x + pad, y, size, c, MONO, True, a)
    return w


def bezier_pts(p0, c0, c1, p1, n=64):
    pts = []
    for i in range(n + 1):
        u = i / n
        mt = 1 - u
        x = mt ** 3 * p0[0] + 3 * mt ** 2 * u * c0[0] + 3 * mt * u ** 2 * c1[0] + u ** 3 * p1[0]
        y = mt ** 3 * p0[1] + 3 * mt ** 2 * u * c0[1] + 3 * mt * u ** 2 * c1[1] + u ** 3 * p1[1]
        pts.append((x, y))
    return pts


def arrow(ctx, p0, p1, c, p=1.0, lw=3, a=1.0, bend=None, c0=None, c1=None, head=14,
          dash=None, both=False):
    """Animated arrow from p0 to p1. `bend` offsets the control points sideways;
    or pass explicit control points c0/c1."""
    if p <= 0 or a <= 0:
        return
    if c0 is None:
        dx, dy = p1[0] - p0[0], p1[1] - p0[1]
        if bend:
            nx, ny = -dy, dx
            ln = math.hypot(nx, ny) or 1
            nx, ny = nx / ln * bend, ny / ln * bend
        else:
            nx = ny = 0
        c0 = (p0[0] + dx / 3 + nx, p0[1] + dy / 3 + ny)
        c1 = (p0[0] + 2 * dx / 3 + nx, p0[1] + 2 * dy / 3 + ny)
    pts = bezier_pts(p0, c0, c1, p1)
    k = max(2, int(len(pts) * p))
    vis = pts[:k]
    color(ctx, c, a)
    ctx.set_line_width(lw)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    if dash:
        ctx.set_dash(dash)
    ctx.move_to(*vis[0])
    for q in vis[1:]:
        ctx.line_to(*q)
    ctx.stroke()
    ctx.set_dash([])

    def tip(at, frm):
        ang = math.atan2(at[1] - frm[1], at[0] - frm[0])
        ctx.move_to(*at)
        ctx.line_to(at[0] - head * math.cos(ang - 0.45), at[1] - head * math.sin(ang - 0.45))
        ctx.line_to(at[0] - head * math.cos(ang + 0.45), at[1] - head * math.sin(ang + 0.45))
        ctx.close_path()
        color(ctx, c, a)
        ctx.fill()

    if head:
        tip(vis[-1], vis[max(0, len(vis) - 3)])
        if both and p >= 1:
            tip(pts[0], pts[2])


def line(ctx, x0, y0, x1, y1, c, lw=2, a=1.0, dash=None):
    color(ctx, c, a)
    ctx.set_line_width(lw)
    if dash:
        ctx.set_dash(dash)
    ctx.move_to(x0, y0)
    ctx.line_to(x1, y1)
    ctx.stroke()
    ctx.set_dash([])


def commit(ctx, x, y, c, a=1.0, scale=1.0, r=17):
    if a <= 0 or scale <= 0:
        return
    ctx.new_path()
    ctx.arc(x, y, r * scale, 0, 2 * math.pi)
    color(ctx, BG, a)
    ctx.fill_preserve()
    color(ctx, c, a)
    ctx.set_line_width(4)
    ctx.stroke()
    ctx.arc(x, y, r * scale * 0.42, 0, 2 * math.pi)
    color(ctx, c, a)
    ctx.fill()


def mark(ctx, x, y, ok, size=26, a=1.0):
    """Check or cross in a tinted circle; (x, y) is the center."""
    c = GREEN if ok else RED
    ctx.new_path()
    ctx.arc(x, y, size * 0.75, 0, 2 * math.pi)
    color(ctx, c, 0.16 * a)
    ctx.fill()
    text(ctx, I_CHECK if ok else I_X, x, y, size * 0.8, c, MONO, False, a, "c")


# ---------- composite widgets ----------

def prompt_parts(cwd, branch):
    if not branch:
        return [("~/" + cwd, BLUE, True), (" $ ", MUTED)]
    bc = BRANCH.get(branch, CYAN)
    return [("~/" + cwd, BLUE, True), (" (", DIM), (branch, bc), (")", DIM), (" $ ", MUTED)]


CPS = 34  # typing speed, chars per second


def terminal(ctx, x, y, w, h, title, entries, t, size=24, a=1.0, lh=1.62):
    """entries (in order):
      {"cmd": str, "t": start, "cwd": dir, "br": branch}
      {"out": str or [(text,color)], "c": color, "t": optional start, "hl": (start, color)}
      {"gap": True}
    Output lines without an explicit "t" appear shortly after the preceding entry."""
    if a <= 0:
        return
    box(ctx, x, y, w, h, 14, TERM_BG, a, STROKE, 2)
    # title bar
    for i, cc in enumerate((hexc("#ff5f57"), hexc("#febc2e"), hexc("#28c840"))):
        ctx.new_path()
        ctx.arc(x + 26 + i * 22, y + 24, 6.5, 0, 2 * math.pi)
        color(ctx, cc, 0.75 * a)
        ctx.fill()
    text(ctx, title, x + w / 2, y + 24, 18, MUTED, MONO, False, a, "c")
    line(ctx, x, y + 48, x + w, y + 48, STROKE, 1.5, a)

    pad_x, top = 28, y + 48 + 22 + size * 0.5
    row_h = size * lh
    rows = []  # (parts, alpha, cursor, hl)
    prev_end = 0.0
    for e in entries:
        if "cmd" in e:
            st = e["t"]
            if t < st:
                break
            n = min(len(e["cmd"]), int((t - st) * CPS))
            typed = e["cmd"][:n]
            done = n >= len(e["cmd"])
            rows.append((prompt_parts(e["cwd"], e["br"]) + [(typed, TEXT)], 1.0,
                         True, None))
            prev_end = st + len(e["cmd"]) / CPS + 0.25
            if not done:
                break
        elif "gap" in e:
            st = e.get("t", prev_end)
            if t < st:
                break
            rows.append(([], 1.0, False, None))
        else:
            st = e.get("t", prev_end)
            if t < st:
                break
            parts = e["out"] if isinstance(e["out"], list) else [(e["out"], e.get("c", MUTED))]
            rows.append((parts, eo(prog(t, st, 0.18)), False, e.get("hl")))
            prev_end = st + 0.06
    max_rows = int((y + h - top + row_h * 0.3) // row_h)
    rows = rows[-max_rows:] if max_rows > 0 else []
    for i, (parts, ra, has_cursor, hl) in enumerate(rows):
        cy = top + i * row_h
        if hl and t >= hl[0]:
            ha = eo(prog(t, hl[0], 0.35))
            wline = sum(tw(ctx, p[0], size, MONO, p[2] if len(p) > 2 else False) for p in parts)
            rrect(ctx, x + pad_x - 10, cy - row_h / 2 + 3, wline + 20, row_h - 6, 6)
            color(ctx, hl[1], 0.16 * ha * a)
            ctx.fill()
        wline = spans(ctx, parts, x + pad_x, cy, size, MONO, a * ra)
        last = i == len(rows) - 1
        if has_cursor and last and (int(t * 2.2) % 2 == 0):
            ctx.rectangle(x + pad_x + wline + 2, cy - size * 0.62, size * 0.55, size * 1.24)
            color(ctx, TEXT, 0.7 * a)
            ctx.fill()


def cmd_end(entry):
    return entry["t"] + len(entry["cmd"]) / CPS


def folder_header(ctx, x, y, w, name, a=1.0, branch=None, bcolor=None, size=28,
                  icon=I_FOLDER, icolor=None, pill_a=None):
    text(ctx, icon, x + 26, y + 38, size, icolor or MUTED, MONO, False, a)
    text(ctx, name, x + 26 + size * 1.5, y + 38, size, TEXT, MONO, True, a)
    if branch:
        pill(ctx, x + w - 20, y + 38, branch, bcolor or BRANCH.get(branch, CYAN), 21,
             a if pill_a is None else pill_a, icon=None if branch == "detached" else I_BRANCH,
             align="r")


def row(ctx, x, y, w, icon, name, note=None, c=TEXT, a=1.0, size=24, icolor=None,
        badge=None, strike=False, indent=0, note_c=MUTED, note_x=None, bold=False,
        note_family=SANS):
    """A file-tree style row; y is its center."""
    if a <= 0:
        return
    ix = x + 26 + indent * 34
    if icon:
        text(ctx, icon, ix, y, size * 0.95, icolor or MUTED, MONO, False, a)
        ix += size * 1.55
    nw = text(ctx, name, ix, y, size, c, MONO, bold, a)
    if strike:
        line(ctx, ix - 4, y + 1, ix + nw + 4, y + 1, c, 2.5, a)
    if note:
        nx = note_x if note_x is not None else ix + nw + 22
        text(ctx, note, nx, y, size * 0.82, note_c, note_family, False, a)
    if badge:
        chip(ctx, x + w - 22, y, badge[0], badge[1], 18, a, "r")


def route(ctx, pts, c, p=1.0, lw=3, a=1.0, r=28, head=14):
    """Animated arrow along a polyline with rounded corners."""
    if p <= 0 or a <= 0:
        return
    dense = [pts[0]]
    for i in range(1, len(pts) - 1):
        (x0, y0), (x1, y1), (x2, y2) = pts[i - 1], pts[i], pts[i + 1]
        d0 = math.hypot(x1 - x0, y1 - y0)
        d1 = math.hypot(x2 - x1, y2 - y1)
        rr = min(r, d0 / 2, d1 / 2)
        a0 = (x1 - (x1 - x0) / d0 * rr, y1 - (y1 - y0) / d0 * rr)
        a1 = (x1 + (x2 - x1) / d1 * rr, y1 + (y2 - y1) / d1 * rr)
        dense.append(a0)
        for k in range(1, 9):
            u = k / 8
            dense.append(((1 - u) ** 2 * a0[0] + 2 * (1 - u) * u * x1 + u ** 2 * a1[0],
                          (1 - u) ** 2 * a0[1] + 2 * (1 - u) * u * y1 + u ** 2 * a1[1]))
    dense.append(pts[-1])
    seg = [math.hypot(dense[i + 1][0] - dense[i][0], dense[i + 1][1] - dense[i][1])
           for i in range(len(dense) - 1)]
    goal = sum(seg) * p
    vis, acc = [dense[0]], 0.0
    for i, s in enumerate(seg):
        if acc + s >= goal:
            u = (goal - acc) / s if s else 1
            vis.append((lerp(dense[i][0], dense[i + 1][0], u), lerp(dense[i][1], dense[i + 1][1], u)))
            break
        acc += s
        vis.append(dense[i + 1])
    color(ctx, c, a)
    ctx.set_line_width(lw)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.move_to(*vis[0])
    for q in vis[1:]:
        ctx.line_to(*q)
    ctx.stroke()
    if head and len(vis) >= 2:
        (fx, fy), (tx, ty) = vis[-2], vis[-1]
        ang = math.atan2(ty - fy, tx - fx)
        ctx.move_to(tx, ty)
        ctx.line_to(tx - head * math.cos(ang - 0.45), ty - head * math.sin(ang - 0.45))
        ctx.line_to(tx - head * math.cos(ang + 0.45), ty - head * math.sin(ang + 0.45))
        ctx.close_path()
        ctx.fill()
