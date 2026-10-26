"""Narration, one entry per visual beat. `cap` is the on-screen caption; the
spoken text is derived from it by speech() so the two never drift apart.

SCENES: (scene_id, title, beats). `title` is the small chip drawn top-left
(None for the title scene). scene_id must match a key in scenes.DRAW.
A beat's `hold` adds seconds of silence after it so a visual can land."""
import re

SCENES = [
    ("title", None, [
        dict(cap="tstack is nine agent skills that Theo Browne uses every day, now public.",
             hold=0.4),
        dict(cap="They work in Claude Code and Codex, and each one teaches the agent one part "
                 "of the pull request workflow."),
        dict(cap="You start one by saying its name, like full send, or babysit.", hold=0.5),
    ]),
    ("pipeline", "How they fit", [
        dict(cap="Most of them chain into one pipeline."),
        dict(cap="Make the change. Review it with sol loop. File the PR. "
                 "Babysit it through CI and review bots. Then merge.", hold=0.3),
        dict(cap="Full send runs that whole pipeline. First, the pieces.", hold=0.5),
    ]),
    ("sol", "Review loop", [
        dict(cap="Sol loop gets your diff reviewed by OpenAI's GPT Sol, in rounds."),
        dict(cap="Sol tags each finding as a blocker, a should, or a nit."),
        dict(cap="The agent fixes the real bugs with the smallest change and pushes back on the rest "
                 "with evidence, tracking every finding in a ledger."),
        dict(cap="Three rounds by default, up to five for risky code. "
                 "It stops when Sol approves, or hands the dispute to you.", hold=0.5),
    ]),
    ("filepr", "Filing", [
        dict(cap="File PR opens a pull request that leads with the problem."),
        dict(cap="The title says why the change matters, not how it was built."),
        dict(cap="The description opens with the problem in plain words, not a list of every "
                 "function that changed.", hold=0.3),
        dict(cap="It checks for secrets, then opens a real PR, not a draft, so review bots run.",
             hold=0.5),
    ]),
    ("babysit", "Babysitting", [
        dict(cap="The babysit PR skill watches a pull request through CI and review bots."),
        dict(cap="It uses one watcher per PR: T3 Code's watch tool, or the bundled pr-wait "
                 "script. Never a homemade polling loop."),
        dict(cap="It checks each bot finding against the source, fixes the real ones, and "
                 "answers false positives with a written reason."),
        dict(cap="It rebases when the main branch moves, and only merges if you ask.", hold=0.5),
    ]),
    ("comments", "Comments", [
        dict(cap="The leaving PR comments skill loads on its own whenever the agent posts on "
                 "GitHub for you."),
        dict(cap="Each comment opens with a note naming the model and who it speaks for."),
        dict(cap="The reply leads with the conclusion, cites the code or the check, and skips "
                 "the filler.", hold=0.5),
    ]),
    ("fullsend", "Autonomy", [
        dict(cap="When you are walking away, say full send."),
        dict(cap="The agent finishes the change, proves it, runs sol loop, files the PR, "
                 "babysits it, and merges it."),
        dict(cap="Proof is evidence it saw itself: a reproduction that now passes, the repo's "
                 "checks, or the running app."),
        dict(cap="It merges only when the gate passes: proof covers the diff, checks are green, "
                 "findings are handled, and the branch is current. No admin bypass."),
        dict(cap="If it gets stuck, it asks through a question tool, so the thread shows it is "
                 "waiting on you.", hold=0.5),
    ]),
    ("fullstop", "Stopping short", [
        dict(cap="Full stop does the same work, but stops at the gate."),
        dict(cap="It turns off auto-merge, never merges, and hands you a PR that is ready, "
                 "waiting on approval, or blocked.", hold=0.5),
    ]),
    ("council", "Multi-model review", [
        dict(cap="Council brings in three reviewers from three providers, such as Claude Opus, "
                 "GPT Sol, and Gemini Pro."),
        dict(cap="Each one scores the work out of ten."),
        dict(cap="It applies the fixes it agrees with, and runs fresh rounds until all three "
                 "are satisfied, without growing the scope."),
        dict(cap="The scores go in a table in the PR description.", hold=0.5),
    ]),
    ("modernize", "Old PRs", [
        dict(cap="Modernize brings an old PR up to date, and asks whether it should still exist."),
        dict(cap="It reads what changed on main since the branch split off."),
        dict(cap="Then it picks a verdict: modernize, rework, or close."),
        dict(cap="Only modernize gets a rebase, checked with git range-diff and pushed with "
                 "force-with-lease. It never merges or closes on its own.", hold=0.5),
    ]),
    ("takeover", "Handoffs", [
        dict(cap="Takeover finishes someone else's PR, branch, or agent thread."),
        dict(cap="It treats the handoff as context, not proof, and checks the original failure "
                 "itself."),
        dict(cap="It carries the original commits onto a new branch and keeps the original "
                 "authors' credit."),
        dict(cap="Then it modernizes, files, and babysits the result.", hold=0.5),
    ]),
    ("graph", "How they connect", [
        dict(cap="Here is how they connect."),
        dict(cap="Full stop builds on full send, which uses sol loop, file PR, and babysit PR."),
        dict(cap="Takeover uses modernize, file PR, and babysit PR."),
        dict(cap="Every skill that comments on GitHub goes through leaving PR comments. "
                 "Council stands alone.", hold=0.8),
    ]),
    ("install", "Install", [
        dict(cap="To install, clone the tstack repo and copy its skills into your Claude Code "
                 "or Codex skills folder."),
        dict(cap="You need an authenticated GitHub CLI and Python 3."),
        dict(cap="Then make them yours: put personal settings in CLAUDE.md or AGENTS.md, so "
                 "updates do not erase them.", hold=3.0),
    ]),
]

# Spoken forms for text the voice misreads. Confirm each with check_narration.py.
_SPEECH = [
    (r"\btstack\b", "tee stack"),
    (r"\bCI\b", "C I"),
    (r"\bCLI\b", "C L I"),
    (r"\bCLAUDE\.md\b", "Claude dot M D"),
    (r"\bAGENTS\.md\b", "agents dot M D"),
    (r"\bpr-wait\b", "P R wait"),
    (r"\bPR\b", "P R"),
    (r"\brange-diff\b", "range diff"),
    (r"\bforce-with-lease\b", "force with lease"),
    (r"--([a-z][\w-]*)", r"dash dash \1"),
]


def speech(cap):
    s = cap
    for pat, rep in _SPEECH:
        s = re.sub(pat, rep, s)
    return s


def sentence_frac(sid, i, k):
    """Fraction of beat i's caption that comes before sentence k, for keying visuals
    to a later sentence within one beat."""
    cap = next(b for s, _, b in SCENES if s == sid)[i]["cap"]
    parts = re.split(r"(?<=[.:])\s+", cap)
    return sum(len(p) + 1 for p in parts[:k]) / len(cap)


def word_frac(sid, i, word):
    """Fraction of beat i's caption before the first occurrence of `word`."""
    cap = next(b for s, _, b in SCENES if s == sid)[i]["cap"]
    return cap.index(word) / len(cap)


LEAD, GAP, TAIL = 0.7, 0.45, 0.9


def layout(durations):
    """durations: {"scene:i": seconds}. Returns per-scene (starts, ends, total)."""
    out = {}
    for sid, _, beats in SCENES:
        t, starts, ends = LEAD, [], []
        for i, b in enumerate(beats):
            d = durations[f"{sid}:{i}"]
            starts.append(t)
            ends.append(t + d)
            t += d + b.get("hold", 0.0) + (GAP if i < len(beats) - 1 else 0)
        out[sid] = (starts, ends, t + TAIL)
    return out
