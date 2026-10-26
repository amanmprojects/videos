"""Narration, one entry per visual beat. `cap` is the on-screen caption; the
spoken text is derived from it by speech() so the two never drift apart."""
import re

SCENES = [
    ("title", None, [
        dict(cap="Git worktrees let you check out several branches of one repository "
                 "at the same time, each in its own directory.", hold=1.6),
    ]),
    ("problem", "The problem", [
        dict(cap="Say you're halfway through a feature, with uncommitted changes, "
                 "when a bug report comes in that needs a fix on main."),
        dict(cap="You could stash your work and switch branches, but that changes files "
                 "underneath your editor and running tools, and you have to undo it all afterwards."),
        dict(cap="Or you could clone the repository again, which downloads the whole history "
                 "a second time and leaves you two repositories to keep in sync."),
        dict(cap="Worktrees are a third option.", hold=0.6),
    ]),
    ("anatomy", "What a repository is made of", [
        dict(cap="To see how they work, split a repository into two parts."),
        dict(cap="The .git directory is the repository itself: every commit, every branch "
                 "and tag, plus config and hooks."),
        dict(cap="The working tree is the files you edit. Each checkout also has two pieces "
                 "of its own state: HEAD, which records what's checked out, and the index, "
                 "your staging area."),
        dict(cap="A normal clone gives you exactly one working tree for each repository.",
             hold=0.6),
    ]),
    ("add", "git worktree add", [
        dict(cap="git worktree add creates another one.", hold=0.4),
        dict(cap="It creates a new directory called app-hotfix, starts a branch named "
                 "hotfix from main, and checks it out there."),
        dict(cap="Your feature directory isn't touched. Both directories share one repository, "
                 "so history exists once, but each has its own HEAD, index, and files."),
        dict(cap="One catch: it's a fresh checkout. Ignored files like node_modules and .env "
                 "are not copied over, so install your dependencies again in the new directory.",
             hold=0.6),
    ]),
    ("hood", "Under the hood", [
        dict(cap="Under the hood, the new directory doesn't get a .git folder. "
                 "It gets a .git file, one line long."),
        dict(cap="That line points into the main repository, where git keeps a small "
                 "admin folder for each linked worktree."),
        dict(cap="It holds that worktree's HEAD and index, plus a commondir file that "
                 "points back to the shared repository."),
        dict(cap="Objects, branches, tags, and config all come from that shared store.",
             hold=0.6),
    ]),
    ("shared", "Commits are shared instantly", [
        dict(cap="Because branches live in the shared store, a commit made in one worktree "
                 "is visible from all the others immediately."),
        dict(cap="There's no push or fetch involved. Back in the original directory, "
                 "git log hotfix already shows the fix."),
        dict(cap="And git branch marks hotfix with a plus sign, meaning it's checked out "
                 "in another worktree.", hold=0.6),
    ]),
    ("rule", "One branch, one worktree", [
        dict(cap="There's one rule: a branch can be checked out in only one worktree at a time."),
        dict(cap="Try to switch to hotfix from the original directory, and git refuses.",
             hold=0.4),
        dict(cap="If two directories had hotfix checked out, a commit in one would move the "
                 "branch under the other, and its files and index would no longer match.",
             hold=0.8),
        dict(cap="To look at that code without claiming the branch, add a worktree with "
                 "--detach. You get the same commit, with no branch checked out.", hold=0.8),
    ]),
    ("cleanup", "Cleaning up", [
        dict(cap="git worktree list shows every worktree and what it has checked out."),
        dict(cap="When you're done, git worktree remove deletes the directory and its admin "
                 "folder. It refuses if there are uncommitted changes, unless you add --force."),
        dict(cap="If you delete a worktree folder by hand instead, git worktree prune cleans "
                 "up the leftover admin folder."),
        dict(cap="Neither one deletes the branch. Your commits stay in the repository until "
                 "you merge or delete it.", hold=0.6),
    ]),
    ("uses", "When to reach for one", [
        dict(cap="Reach for a worktree whenever you need two branches at once:"),
        dict(cap="a hotfix next to unfinished work,"),
        dict(cap="reviewing a pull request without losing your place,"),
        dict(cap="running a slow test suite on one branch while you keep coding on another,"),
        dict(cap="or giving each coding agent its own directory, so their edits never collide.",
             hold=1.0),
    ]),
    ("recap", "Recap", [
        dict(cap="So: one repository, many working directories."),
        dict(cap="History, branches, config, and the stash are shared. HEAD, the index, and "
                 "the files on disk belong to each worktree."),
        dict(cap="And each branch can be checked out in only one place at a time.", hold=4.5),
    ]),
]

_SPEECH = [
    (r"\bworktrees\b", "work trees"),
    (r"\bWorktrees\b", "Work trees"),
    (r"\bworktree's\b", "work tree's"),
    (r"\bworktree\b", "work tree"),
    (r"\.git\b", "dot git"),
    (r"\bHEAD\b", "head"),
    (r"\bapp-hotfix\b", "app hotfix"),
    (r"\bnode_modules\b", "node modules"),
    (r"\.env\b", "dot E N V"),
    (r"--detach\b", "dash dash detach"),
    (r"--force\b", "dash dash force"),
    (r"\bcommondir\b", "common durr"),
]


def speech(cap):
    s = cap
    for pat, rep in _SPEECH:
        s = re.sub(pat, rep, s)
    return s


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
