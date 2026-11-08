#!/usr/bin/env python3
"""PostToolUse: after writing a Supabase migration, check for CREATE without
GRANT. Exit 2 feeds the warning back to Claude before the migration runs."""
import json, re, sys

try:
    data = json.load(sys.stdin)
except Exception:
    sys.exit(0)

if data.get("tool_name") not in ("Write", "Edit", "MultiEdit"):
    sys.exit(0)
ti = data.get("tool_input", {}) or {}
path = str(ti.get("file_path", ""))
if "supabase/migrations" not in path or not path.endswith(".sql"):
    sys.exit(0)

try:
    sql = open(path).read()
except Exception:
    sys.exit(0)

creates = re.findall(
    r"CREATE\s+(?:OR\s+REPLACE\s+)?(?:TABLE|VIEW|MATERIALIZED\s+VIEW|FUNCTION)"
    r"\s+(?:IF\s+NOT\s+EXISTS\s+)?(?:public\.)?([\w\"]+)", sql, re.I)
# Full comma-separated relation list — `GRANT select ON public.a, public.b TO ...`
granted = set(
    rel.strip().lower().strip('"').removeprefix("public.").removesuffix("()")
    for match in re.findall(
        r"GRANT\s+[\w, ]+\s+ON\s+(?:TABLE\s+|FUNCTION\s+)?"
        r"((?:(?:public\.)?[\w\"]+(?:\(\))?)(?:\s*,\s*(?:public\.)?[\w\"]+(?:\(\))?)*)",
        sql, re.I)
    for rel in match.split(","))
missing = [c for c in creates if c.lower().strip('"') not in granted]
if missing:
    print(f"MIGRATION CHECK ({path}): CREATE without GRANT for: "
          f"{', '.join(missing)}. security_invoker RLS is NOT sufficient — "
          f"PostgREST needs explicit GRANT to authenticated/service_role "
          f"(Postgres error 42501). Add GRANTs before applying.",
          file=sys.stderr)
    sys.exit(2)
sys.exit(0)
