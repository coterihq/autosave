#!/usr/bin/env python3
"""PreToolUse guard: pattern-based hard controls for common risky commands (not a sandbox).
Blocks: .env* modification, live-mode toggles (DRY_RUN/TESTNET=false, --live),
destructive prod DB ops (supabase db reset/push, MCP apply_migration), rm -rf on
root-level dirs, and two self-fixable shell footguns (self-matching wait loops,
unquoted multi-value $vars under zsh).
Exit 0 = allow. Exit 2 = block (stderr is shown to Claude).
Fail-open on parse errors so a broken guard never bricks the session.
Config (env, set in settings.json "env"):
  CLAUDE_KIT_APPROVER      who Claude must ask on a block (default "the user")
  CLAUDE_GUARD_DB_WRAPPERS extra regex for project wrappers that push to prod DB
"""
import json, os, re, sys

APPROVER = os.getenv("CLAUDE_KIT_APPROVER", "the user")
HOME = re.escape(os.path.expanduser("~"))

ENV_RE = re.compile(r"\.env(\.[\w.-]+)?$")
ENV_OK = re.compile(r"\.env\.(example|sample|template|test)$")

def deny(msg):
    print(f"BLOCKED by ~/.claude/hooks/guard.py: {msg} "
          f"Ask {APPROVER} for explicit confirmation; they can run it manually.",
          file=sys.stderr)
    sys.exit(2)

def is_env(path):
    p = str(path or "")
    return bool(ENV_RE.search(p)) and not ENV_OK.search(p)

def _code_only(text):
    """The command with every quoted span blanked, so a literal mention is not a use."""
    out, q, i = [], None, 0
    while i < len(text):
        c = text[i]
        if q:
            out.append(" " if c != q else c)
            if c == q:
                q = None
            elif c == "\\" and q == '"':
                out.append(" ")
                i += 1
        else:
            out.append(c)
            if c in "'\"":
                q = c
        i += 1
    return "".join(out)

def _drop_data_heredocs(text):
    """Drop heredoc bodies that are data (a commit message, a doc). A body fed to a shell
    (`bash <<EOF`, `source`, `eval`) is code and stays."""
    def repl(m):
        opener = text[text.rfind("\n", 0, m.start()) + 1:m.start()]
        return m.group(0) if re.search(r"\b(?:ba|z)?sh\b|\bsource\b|\beval\b", opener) else m.group(1)
    return re.sub(r"(<<-?\s*(['\"]?)(\w+)\2[^\n]*)\n.*?\n\3\b", repl, text, flags=re.S)

try:
    data = json.load(sys.stdin)
except Exception:
    sys.exit(0)

tool = data.get("tool_name", "")
ti = data.get("tool_input", {}) or {}

# --- File-editing tools: protect .env* ---
if tool in ("Write", "Edit", "MultiEdit", "NotebookEdit"):
    if is_env(ti.get("file_path", "")):
        deny(f"direct edit of {ti.get('file_path')} (.env files are hands-off).")
    for e in ti.get("edits", []) or []:
        if is_env(e.get("file_path", "")):
            deny("multi-edit touches a .env file.")

# --- Bash: pattern checks on the command string ---
if tool == "Bash":
    cmd = str(ti.get("command", ""))
    # Newlines separate commands like ; does. Backslash-newline is one command, so
    # join those first or `cp x \` + `.env` on the next line would slip through.
    cmd = re.sub(r"\\\n", " ", cmd)

    # 1. Writes to .env (reads are fine)
    env_write = re.search(
        r"(?:>{1,2}|\btee\b|\bsed\s+-i\b|\bmv\b|\bcp\b|\brm\b)[^|;&\n]*"
        r"\.env(?!\.(example|sample|template|test))(\.[\w.-]+)?\b", cmd)
    if env_write:
        deny("command writes to/removes a .env file.")

    # Rules 2, 3 and 6 read the command with quoted spans blanked and data heredoc bodies
    # dropped, so a grep for the phrase or a commit message that mentions it is not a use. A
    # heredoc written to a file that the command then runs is kept whole.
    # ponytail: misses a toggle hidden inside `bash -c '...'`; parse -c bodies if that shows up.
    written = re.search(r">\s*(\S+)\s*<<-?\s*['\"]?\w+", cmd)
    writes_and_runs = bool(written and re.search(r"\b(?:ba|z)?sh\s+" + re.escape(written.group(1)) + r"\b", cmd))
    scan = cmd if writes_and_runs else _drop_data_heredocs(cmd)
    code = _code_only(scan)

    # 2. Live-mode toggles: never flipped by model judgment
    #    The NAME= must be outside quotes (in `code`); its value is read from `scan` at the same
    #    offset, since `_code_only` keeps length, so DRY_RUN="false" counts and a quoted mention doesn't.
    off_value = re.compile(r"""["']?(false|0)["']?(?!\w)""", re.I)
    if any(off_value.match(scan, m.end())
           for m in re.finditer(r"\b(\w+_)?(DRY_RUN|TESTNET)\s*=\s*", code, re.I)) or \
       re.search(r"(?:^|[\s(;&|])--live(?=$|[\s;&|)>]|=(?!(?:false|0)\b))", code):
        deny("live-mode toggle detected (DRY_RUN/TESTNET=false or --live).")

    # 3. Destructive prod DB ops. Project wrappers that push to prod under another name
    #    (e.g. `npm run db:migrate`) go in CLAUDE_GUARD_DB_WRAPPERS; none are assumed.
    if re.search(r"supabase\s+db\s+reset\b(?![^|;&\n]*--local)", code) or \
       re.search(r"supabase\s+db\s+push\b(?![^|;&\n]*--local)", code) or \
       (os.getenv("CLAUDE_GUARD_DB_WRAPPERS") and re.search(os.getenv("CLAUDE_GUARD_DB_WRAPPERS"), code)):
        deny("supabase db reset/push against linked (prod) project.")

    # 4. Catastrophic rm: / , ~ , $HOME (any spelling), their /* , and ~/.claude itself.
    #    A relative `.claude` (a project folder) is allowed.
    homes = r"(?:~|\$\{?HOME\}?|" + HOME + r")"
    target = r"(?:/\*?|" + homes + r"/?\*?|" + homes + r"/\.claude/?\*?)"
    if re.search(r"\brm\s+(?:(?:-\w*[rf]\w*|--recursive|--force|--no-preserve-root)\s+)+"
                 r"[\"']?" + target + r"[\"']?(?=\s|$|[;&|)])", cmd):
        deny("rm -rf on a root-level directory.")

    # 5. Self-matching wait loop (seen repeatedly in practice). The process table contains
    #    this command's OWN wrapper shell, whose argv holds the entire command text, so a loop that
    #    greps that table can wait on itself forever. Not an approval block; Claude fixes it.
    #    Two matchers, because one incident slipped past a rule that knew only the first:
    #      a) pgrep/pkill -f X          b) ps ... | grep/rg/awk X
    #    A bracket class protects the PATTERN but not the command: That incident bracketed its pattern and
    #    still hung, because the loop's own progress message ("waiting: another next build is
    #    running") put the bare literal in the same argv. So a bracketed pattern is cleared only
    #    when the bare literal appears nowhere else in the command.
    #    Heredoc bodies are data (prose quoting the pattern blocked a doc edit once) UNLESS the
    #    command also runs the file it just wrote — then the body is executable code .
    def _pat(m):
        return m.group(1) or m.group(2) or m.group(3) or ""
    QUOTED = r"(?:'([^']+)'|\"([^\"]+)\"|([^\s;|&)]+))"
    #    The heredoc body is kept only when the command writes it to a path and then RUNS that
    #    path (writes_and_runs, above); `python3 - <<PY` or `cat > notes.md <<EOF` stay data.
    loop_cmd = cmd if writes_and_runs else re.sub(r"<<-?\s*(['\"]?)(\w+)\1.*?\n\2\b", "", cmd, flags=re.S)
    #    Scan only each loop's CONDITION (between while/until and its `do`). Scanning the whole
    #    command cross-products an unrelated `while` with an unrelated `ps | grep`. Seen when `while read -r line; do …` plus a quoted `ps aux | grep foo`
    #    elsewhere in the same call tripped the block.
    for cond in re.findall(r"\b(?:while|until)\b(.*?)\bdo\b", loop_cmd, flags=re.S):
        hits = list(re.finditer(r"\bp(?:grep|kill)\s+(?:-\w+\s+)*-\w*f\w*\s+(?:-\w+\s+)*" + QUOTED, cond))
        hits += list(re.finditer(r"\bps\b[^|;&\n]*\|\s*(?:grep|rg|awk)\s+(?:-\w+\s+)*" + QUOTED, cond))
        for m in hits:
            pat = _pat(m)
            if not pat:
                continue
            bare = pat.replace("[", "").replace("]", "")
            # the whole command is what sits in the wrapper's argv, so look for the bare literal
            # across all of it — minus this matcher itself
            rest = loop_cmd.replace(m.group(0), "", 1)
            if "[" not in pat:
                why = "matches this command's own shell and never exits"
            elif bare in rest:
                why = (f"is bracketed, but the bare text {bare!r} also appears elsewhere in this "
                       f"command (a message, comment or heredoc body), and THAT copy sits in the "
                       f"wrapper shell's argv — the loop matches its own announcement")
            else:
                continue
            print(f"BLOCKED by ~/.claude/hooks/guard.py: process match {pat!r} inside a wait loop {why}. "
                  f"Use a bracket class AND keep the bare literal out of the rest of the command, or "
                  f"poll a pid/port/artefact instead. Fix and rerun; no approval needed.", file=sys.stderr)
            sys.exit(2)

    # --- 6. zsh does not word-split an unquoted $var  ---
    #    zsh is NOT bash here: `du -scm $dirs` passes the whole newline-joined string as ONE
    #    argument, so the command silently checks nothing and reports a confident wrong answer
    #    (0 MB of build dirs; "0 differ"; a rerun loop that never fired). Single-value vars are
    #    safe for the same reason, so this only fires on shapes that NEED splitting:
    #      a) `set -- $var`   — set's whole job is to split; unquoted here is always the bug.
    #      b) `$var` bare, where var was assigned from a substitution that yields many lines
    #         (ls / find / git ls-* / grep -l / seq / awk / tr / a `for x in` list var).
    #    Self-fixable, so it reads like rule 5: fix the quoting and rerun, no approval needed.
    #    bash DOES word-split, so the rule only applies when the user's shell is zsh.
    MULTI = r"\b(?:ls|find|seq|tr|awk|cut|sort|uniq|xargs|git\s+ls-\w+|git\s+diff\s+--name|grep\s+(?:-\w*\s+)*-\w*l)\b"
    SINGLE = r"\|\s*(?:wc\b[^|]*|head\s+-(?:n\s*)?1|tail\s+-(?:n\s*)?1)\s*$"  # ends in one value
    is_zsh = os.path.basename(os.getenv("SHELL", "")) == "zsh"

    def _unquoted_vars(text):
        """Names used as a bare $var / ${var}, skipping anything inside ' or " quotes."""
        out, q, i = [], None, 0
        while i < len(text):
            c = text[i]
            if q:
                if c == q:
                    q = None
                elif c == "\\" and q == '"':
                    i += 1
            elif c in "'\"":
                q = c
            elif c == "$":
                m = re.match(r"\$\{?([A-Za-z_]\w*)\}?", text[i:])
                if m:
                    out.append((m.group(1), i))
                    i += m.end() - 1
            i += 1
        return out

    for m in re.finditer(r"\bset\s+--\s+\$\{?([A-Za-z_]\w*)\}?", code if is_zsh else ""):
        print(f"BLOCKED by ~/.claude/hooks/guard.py: `set -- ${m.group(1)}` relies on word "
              f"splitting, which zsh does not do — $1 becomes the whole string and $2 is empty. "
              f"Use an array (set -- ${{=%s}} or read into one), or pass the values literally. "
              f"Fix and rerun; no approval needed." % m.group(1), file=sys.stderr)
        sys.exit(2)

    # A `for x in ...` loop variable holds one value per pass, so it is not tracked.
    assigned = {a: sub for a, sub in re.findall(r"([A-Za-z_]\w*)=\$\(([^)]*)\)", code)}
    for name, where in (_unquoted_vars(code) if is_zsh else []):
        src = assigned.get(name)
        if src is None or not re.search(MULTI, src) or re.search(SINGLE, src):
            continue
        # The assignment itself is not a use; only a later bare reference is.
        if re.match(rf"\s*{re.escape(name)}\s*=", code[max(0, where - len(name) - 2):where]):
            continue
        print(f"BLOCKED by ~/.claude/hooks/guard.py: ${name} holds multiple values (assigned from "
              f"{src.strip()[:40]!r}) but is used unquoted — zsh passes it as ONE argument, so the "
              f"command silently acts on nothing and still exits 0. Loop over it, use an array, or "
              f"pass the glob/paths directly. Fix and rerun; no approval needed.", file=sys.stderr)
        sys.exit(2)

# --- Supabase MCP apply_migration: same prod write as `supabase db push`, minus /preflight. Rule 3 only sees Bash, so it never saw this path . ---
if re.fullmatch(r"mcp__.+__apply_migration", tool):
    deny("Supabase MCP apply_migration writes schema to the linked (prod) project, bypassing "
         "/preflight.")

sys.exit(0)
