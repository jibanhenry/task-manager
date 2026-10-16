# Evidence for PA6 / Week 6 drills

Each `*.txt` is a condensed transcript of one Claude Code session: every tool
call, any hook block (`ERR> PreToolUse:… BLOCKED…`), and Claude's final
report. Each `*.diff` is the `git diff` that the session left behind, or the
change I made to the hook. `<repo>` stands for the task-manager root.

| File prefix | What |
|---|---|
| `d1_v1_tasks`, `d1_v2_tasks`, `d1_v2_users`, `d1_v3_users` | Drill 1 / COMMAND_LOG rows 1–4 (audit-errors v1→v3) |
| `t1_scaffold`, `t1_scaffold_get`, `t1_filltests` | COMMAND_LOG rows 5–7 |
| `d2_p3_errors`, `d2_fix1.diff`, `d2_p3_errors_fixed`, `d2_p3_migr`, `d2_p4_legit` | Drill 2 phases 3–4 |
| `t2_content`, `t2_rmrf`, `fix_rm_anywhere.diff`, `t2_rmrf_fixed` | HOOK_LOG Part A live checks |
| `v1_case`, `v1_case_mac`, `fix_v1.diff`, `v1_case_edit`, `v1_case_mac_fixed`, `v1_rerun_final*` | HOOK_LOG Vector 1 |
| `v2_bash`, `fix_v2.diff`, `v2_bash_fixed`, `v2_bash_final` | HOOK_LOG Vector 2 |
