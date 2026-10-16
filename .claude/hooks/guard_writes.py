#!/usr/bin/env python3
"""PreToolUse hook: the single guard for task-manager.

Three protections, all exit 2 (block) with a reason on stderr:
  1. Path guard     - Write/Edit/MultiEdit on BLOCKED_PATHS.
  2. Bash guard     - Bash commands matching DANGEROUS_COMMANDS / rm -rf.
  3. Content guard  - hardcoded DB connection strings written into
                      CONTENT_GUARDED files.
Exit 0 = allow. To add a rule, see the "## Hooks" section of CLAUDE.md.
"""
import json
import os
import re
import shlex
import sys

PROJECT_DIR = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()

# ── 1. Paths this project must never let Claude write to ───────────────
# Populated from CLAUDE.md "Do not touch" and Week 5 DECOMPOSITION.md.
# Week 7 (MCP): MCP tools fire PreToolUse as mcp__<server>__<tool>. These
# rules should ALSO apply to MCP calls:
#   utils/errors.py, migrations/, .env, .claude/settings.json  -> any MCP
#     filesystem write tool (e.g. mcp__filesystem__write_file / edit_file)
#   migrations/ and .env -> any MCP database / shell tool as well.
# requirements.txt and tests/conftest.py only need the Write/Edit/Bash path.
BLOCKED_PATHS = [
    "utils/errors.py",        # AppError hierarchy — never modified by agents
    "migrations/",            # Migrations require human review
    ".env",                   # Secrets — hard block
    ".claude/settings.json",  # Hook config — agents must not self-modify
    "requirements.txt",       # CLAUDE.md: no new dependencies without asking
    "tests/conftest.py",      # CLAUDE.md: restore_data autouse fixture
]

# ── 2. Bash commands that are never allowed ─────────────────────────────
# Word-boundary regexes: "DROP TABLE" blocks, "backdrop tablet" does not.
DANGEROUS_COMMANDS = [
    (re.compile(r"\b(?:DROP|TRUNCATE)\s+TABLE\b", re.IGNORECASE),
     "destructive SQL (DROP TABLE / TRUNCATE TABLE)"),
    (re.compile(r"\bgit\s+push\b[^;&|\n]*?(?:\s--force(?:-with-lease)?\b"
                r"|\s-f\b)"),
     "git force-push rewrites shared history"),
]
# rm -rf is checked token by token (see rm_is_recursive_force) so that
# `rm -r -f`, `rm -fr`, `rm --recursive --force` are caught but a file
# named "rm-rf-notes.txt" or `echo "rm -rf"` is not.

# ── 3. Files whose CONTENT is inspected ─────────────────────────────────
# Claude may write these files, but not with a hardcoded DB URL in them.
CONTENT_GUARDED = ["services/tasks.py"]   # compared via rel(), lower-case
CONNECTION_STRING = re.compile(r"\bpostgresql(?:\+\w+)?://|\bsqlite:///")

SEGMENT_SPLIT = re.compile(r"&&|\|\||[;|\n]")


def rel(file_path: str) -> str:
    """Project-relative, normalised, lower-cased form of a path.

    - Claude Code sends absolute paths; BLOCKED_PATHS are project-relative.
    - realpath() resolves symlinks and `..`, so a link to a protected file
      is checked as the file it points to.
    - lower(): macOS (APFS) is case-insensitive, so Utils/errors.py IS
      utils/errors.py on disk (HOOK_LOG.md, Vector 1). Compare case-folded.
    """
    path = file_path if os.path.isabs(file_path) else \
        os.path.join(PROJECT_DIR, file_path)
    return os.path.normpath(os.path.relpath(
        os.path.realpath(path), os.path.realpath(PROJECT_DIR))).lower()


def is_blocked(file_path: str) -> tuple[bool, str]:
    """Return (blocked, reason) for the given file path."""
    norm = rel(file_path)
    for pattern in BLOCKED_PATHS:
        target = os.path.normpath(pattern).lower()
        if norm == target:
            return True, f"Protected file: {pattern}"
        if pattern.endswith("/") and (norm + "/").startswith(target + "/"):
            return True, f"Protected directory: {pattern}"
    return False, ""


def segments(command: str) -> list[list[str]]:
    """Split a shell command into simple commands, each a list of tokens."""
    out = []
    for part in SEGMENT_SPLIT.split(command):
        try:
            tokens = shlex.split(part)
        except ValueError:
            tokens = part.split()
        while tokens and ("=" in tokens[0] or tokens[0] in ("sudo", "env")):
            tokens = tokens[1:]
        if tokens:
            out.append(tokens)
    return out


def rm_is_recursive_force(tokens: list[str]) -> bool:
    """True if any `rm` in tokens has both recursive and force flags.

    `rm` is looked for at every position, not only as the first word, so
    `find . -exec rm -rf {} +` and `xargs rm -rf` are caught too.
    """
    for i, tok in enumerate(tokens):
        if os.path.basename(tok) != "rm":
            continue
        flags = set()
        for arg in tokens[i + 1:]:
            if arg == "--recursive":
                flags.add("r")
            elif arg == "--force":
                flags.add("f")
            elif arg.startswith("-") and not arg.startswith("--"):
                flags.update(arg[1:].lower())
            elif arg in ("{}", "+", ";", "--"):
                break
        if {"r", "f"} <= flags:
            return True
    return False


# Commands whose every non-flag argument is a file they write/delete.
WRITE_ALL_ARGS = {"tee", "touch", "truncate", "rm", "unlink", "shred"}
# Commands that write their LAST argument (the destination).
WRITE_LAST_ARG = {"cp", "mv", "install", "ln", "rsync"}
# In-place editors: write every file argument when -i is present.
IN_PLACE = {"sed", "perl", "gsed"}
REDIRECT = re.compile(r"^(?:\d|&)?>>?(.*)$")      # >, >>, 2>, &>, >>file
# Fallback for interpreters only: python -c "open('utils/errors.py', 'w')".
# Shell redirections are parsed exactly above, so `2>&1` is NOT a hint.
WRITE_HINT = re.compile(r"open\([^)]*['\"][wa+]|write_text|\.write\(")


def bash_write_targets(command: str) -> list[str]:
    """Paths a Bash command would write to (best effort, token level)."""
    targets = []
    cwd = PROJECT_DIR
    for tokens in segments(command):
        name = os.path.basename(tokens[0])
        args = tokens[1:]
        if name == "cd" and args:                 # track `cd utils && ...`
            cwd = os.path.join(cwd, args[0])
            continue
        start = len(targets)
        for i, tok in enumerate(tokens):          # redirections
            m = REDIRECT.match(tok)
            if m and not tok.startswith(">&"):
                if m.group(1):
                    targets.append(m.group(1))
                elif i + 1 < len(tokens):
                    targets.append(tokens[i + 1])
        plain = [a for a in args if not a.startswith("-")
                 and not REDIRECT.match(a)]
        if name in WRITE_ALL_ARGS or (
                name in IN_PLACE and any(a.startswith("-i") for a in args)):
            targets.extend(plain)
        elif name in WRITE_LAST_ARG and plain:
            targets.append(plain[-1])
        elif name == "dd":
            targets.extend(a[3:] for a in args if a.startswith("of="))
        targets[start:] = [os.path.join(cwd, t) for t in targets[start:]]
    return targets


def bash_touches_protected(command: str) -> tuple[bool, str]:
    """Path guard for Bash: Vector 2 in HOOK_LOG.md."""
    for target in bash_write_targets(command):
        blocked, reason = is_blocked(target)
        if blocked:
            return True, reason
    # Interpreter one-liners hide the target inside a string; if a
    # protected path is named AND something looks like a write, block.
    lowered = command.lower()
    for pattern in BLOCKED_PATHS:
        named = pattern.lower().rstrip("/") in lowered
        if named and WRITE_HINT.search(command):
            return True, f"Protected path {pattern} named in a writing command"
    return False, ""


def check_bash(command: str) -> tuple[bool, str]:
    """Return (blocked, reason) for a Bash command string."""
    for regex, why in DANGEROUS_COMMANDS:
        if regex.search(command):
            return True, f"Prohibited command ({why})"
    for tokens in segments(command):
        if rm_is_recursive_force(tokens):
            return True, "Prohibited command (rm -rf: recursive force delete)"
        # A quoted argument may itself be a command: bash -c "rm -rf x"
        for tok in tokens:
            if " " in tok.strip() and check_bash(tok)[0]:
                return check_bash(tok)
    return False, ""


def written_content(tool: str, tool_input: dict) -> str:
    """The text a Write/Edit/MultiEdit call is about to put in the file."""
    if tool == "Write":
        return tool_input.get("content", "")
    if tool == "Edit":
        return tool_input.get("new_string", "")
    if tool == "MultiEdit":
        return "\n".join(e.get("new_string", "")
                         for e in tool_input.get("edits", []))
    return ""


def block(lines: list[str]) -> None:
    for line in lines:
        print(line, file=sys.stderr)
    sys.exit(2)


def main():
    payload = json.loads(sys.stdin.read())
    tool = payload.get("tool_name", "")
    tool_input = payload.get("tool_input", {}) or {}

    if tool == "Bash":
        command = tool_input.get("command", "")
        blocked, reason = check_bash(command)
        if blocked:
            block([f"BLOCKED: {reason}.",
                   "This command is prohibited by guard_writes.py. Ask the "
                   "user to run it themselves if it is really needed."])
        blocked, reason = bash_touches_protected(command)
        if blocked:
            block([f"BLOCKED: {reason}. Writing it through Bash is the same "
                   "as Write/Edit and is protected by project policy.",
                   "Do not retry with another shell command; ask the user."])
        sys.exit(0)

    # Only inspect file-write tools
    if tool not in ("Write", "Edit", "MultiEdit"):
        sys.exit(0)

    file_path = tool_input.get("file_path") or tool_input.get("path", "")

    blocked, reason = is_blocked(file_path)
    if blocked:
        block([f"BLOCKED: {reason}. This file is protected by project policy.",
               f"To modify {file_path}, update CLAUDE.md and remove the",
               "protection after team review."])

    if rel(file_path) in CONTENT_GUARDED:
        match = CONNECTION_STRING.search(written_content(tool, tool_input))
        if match:
            block([f"BLOCKED: hardcoded database connection string "
                   f"('{match.group(0)}...') in {rel(file_path)}.",
                   "Connection strings must come from environment variables, "
                   "e.g. os.environ[\"DATABASE_URL\"]; never hardcode them."])
    sys.exit(0)


if __name__ == "__main__":
    main()
