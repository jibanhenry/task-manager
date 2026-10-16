"""Tests for .claude/hooks/guard_writes.py (the PreToolUse guard)."""
import json
import os
import subprocess
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOOK = os.path.join(ROOT, ".claude", "hooks", "guard_writes.py")


def run_hook(tool_name: str, tool_input: dict) -> subprocess.CompletedProcess:
    payload = json.dumps({"tool_name": tool_name, "tool_input": tool_input})
    env = dict(os.environ, CLAUDE_PROJECT_DIR=ROOT)
    return subprocess.run([sys.executable, HOOK], input=payload, text=True,
                          capture_output=True, cwd=ROOT, env=env)


def p(rel_path: str) -> str:
    """Absolute path, as Claude Code sends it."""
    return os.path.join(ROOT, rel_path)


# ── Path guard ──────────────────────────────────────────────────────────
@pytest.mark.parametrize("path", [
    "utils/errors.py", "requirements.txt", "tests/conftest.py", ".env",
    ".claude/settings.json", "migrations/versions/add_x.py",
])
@pytest.mark.parametrize("tool", ["Write", "Edit", "MultiEdit"])
def test_path_guard_blocks_protected_paths(tool, path):
    result = run_hook(tool, {"file_path": p(path)})
    assert result.returncode == 2
    assert "BLOCKED" in result.stderr


# Vector 1 (HOOK_LOG.md): on macOS Utils/errors.py is the same file.
@pytest.mark.parametrize("path", [
    "Utils/errors.py", "UTILS/ERRORS.PY", "utils/Errors.py",
    "Requirements.txt", "Tests/conftest.py", "MIGRATIONS/versions/x.py",
    "services/../utils/errors.py", "./utils//errors.py",
])
def test_path_guard_is_case_and_dot_insensitive(path):
    result = run_hook("Edit", {"file_path": p(path)})
    assert result.returncode == 2
    assert "BLOCKED" in result.stderr


def test_path_guard_follows_symlinks(tmp_path):
    link = os.path.join(ROOT, "tmp_link_to_errors.py")
    os.symlink(os.path.join(ROOT, "utils", "errors.py"), link)
    try:
        assert run_hook("Write", {"file_path": link}).returncode == 2
    finally:
        os.remove(link)


def test_content_guard_is_case_insensitive_on_path():
    result = run_hook("Write", {"file_path": p("Services/Tasks.py"),
                                "content": 'U = "sqlite:///x.db"'})
    assert result.returncode == 2


@pytest.mark.parametrize("path", ["services/tasks.py", "tests/test_tasks.py",
                                  "routes/api.py"])
def test_path_guard_allows_normal_files(path):
    assert run_hook("Edit", {"file_path": p(path),
                             "new_string": "x = 1"}).returncode == 0


# ── Bash guard ──────────────────────────────────────────────────────────
@pytest.mark.parametrize("command", [
    "sqlite3 app.db 'DROP TABLE tasks;'",
    "psql -c \"truncate   table users\"",
    "rm -rf build/",
    "rm -fr /tmp/x",
    "rm -r -f services",
    "rm --recursive --force tests",
    "cd /tmp && sudo rm -Rf task-manager",
    "git push --force origin main",
    "git push -f",
    "git push origin main --force-with-lease",
    # Found live: Claude cleaned caches with find -exec (rm not first word)
    "find . -name __pycache__ -prune -exec rm -rf {} +",
    "ls build | xargs rm -rf",
    "bash -c 'rm -rf build'",
])
def test_bash_guard_blocks_dangerous_commands(command):
    result = run_hook("Bash", {"command": command})
    assert result.returncode == 2
    assert "Prohibited command" in result.stderr


@pytest.mark.parametrize("command", [
    "/usr/bin/python3 -m pytest -q",
    "rm -r build",                     # recursive but not forced
    "rm -f notes.txt",                 # forced but not recursive
    "cat rm-rf-notes.txt",             # 'rm -rf' only as a substring
    "echo 'backdrop tablet'",          # DROP/TABLE only inside words
    "grep -n DROPTABLE README.md",
    "git push origin feature",
    "git log --format=-f",
    "find . -name '*.pyc' -exec rm -f {} +",   # forced, not recursive
])
def test_bash_guard_allows_safe_commands(command):
    assert run_hook("Bash", {"command": command}).returncode == 0


# ── Content guard ───────────────────────────────────────────────────────
@pytest.mark.parametrize("url", [
    "postgresql://admin:pw@localhost:5432/tasks",
    "postgresql+psycopg2://u:p@db/tasks",
    "sqlite:///tasks.db",
])
def test_content_guard_blocks_connection_strings(url):
    line = f'DB_URL = "{url}"\n'
    for tool, tool_input in [
        ("Write", {"content": line}),
        ("Edit", {"old_string": "x", "new_string": line}),
        ("MultiEdit", {"edits": [{"old_string": "x", "new_string": line}]}),
    ]:
        tool_input["file_path"] = p("services/tasks.py")
        result = run_hook(tool, tool_input)
        assert result.returncode == 2
        assert "environment variables" in result.stderr


def test_content_guard_allows_env_lookup():
    line = 'DB_URL = os.environ["DATABASE_URL"]\n'
    assert run_hook("Write", {"file_path": p("services/tasks.py"),
                              "content": line}).returncode == 0


def test_content_guard_only_applies_to_guarded_file():
    line = 'EXAMPLE = "sqlite:///demo.db"\n'
    assert run_hook("Write", {"file_path": p("services/tags.py"),
                              "content": line}).returncode == 0


# ── Vector 2 (HOOK_LOG.md): writes to protected files through Bash ──────
@pytest.mark.parametrize("command", [
    "cat >> utils/errors.py <<'EOF'\nclass X(AppError): pass\nEOF",
    "echo 'x = 1' > utils/errors.py",
    "printf 'x' >>Utils/errors.py",
    "echo flask==3.1 | tee -a requirements.txt",
    "sed -i '1i # hi' utils/errors.py",
    "sed -i.bak 's/a/b/' Utils/errors.py",
    "cp /tmp/evil.py utils/errors.py",
    "mv new.py tests/conftest.py",
    "rm utils/errors.py",
    "touch migrations/001.py",
    "echo SECRET=1 >> .env",
    "python3 -c \"open('utils/errors.py','a').write('x')\"",
    "dd if=/dev/null of=utils/errors.py",
    "cd utils && echo x > ../utils/errors.py",
    "cd utils && echo x >> errors.py",
])
def test_bash_path_guard_blocks_writes_to_protected_files(command):
    result = run_hook("Bash", {"command": command})
    assert result.returncode == 2
    assert "BLOCKED" in result.stderr


@pytest.mark.parametrize("command", [
    "cat utils/errors.py",
    "head -5 Utils/errors.py",
    "grep -n AppError utils/errors.py",
    "cp utils/errors.py /tmp/errors_backup.py",
    "diff utils/errors.py /tmp/errors_backup.py",
    "/usr/bin/python3 -m pytest -q 2>&1 | tail -5",
    "echo ok > /tmp/out.txt",
    "sed -n 1,20p utils/errors.py",
    "cat >> services/tasks.py <<'EOF'\nx = 1\nEOF",
    # False positive seen live after the first Vector 2 fix: 2>&1 is not
    # a write, and the protected file is only read here.
    "ls; ls utils Utils 2>&1 | head; head -5 utils/errors.py",
    "cd utils && cat errors.py > /tmp/copy.py",
])
def test_bash_path_guard_allows_reads_and_other_files(command):
    assert run_hook("Bash", {"command": command}).returncode == 0
