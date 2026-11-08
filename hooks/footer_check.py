#!/usr/bin/env python3
"""Stop hook: substantive replies must contain a required footer line.
Default footer: "Tooling rec:" (one line naming the command, skill, connector or rule
already installed that would have improved the answer). Nudges once, never loops.
Config (settings.json env):
  CLAUDE_FOOTER_MARKER     text that must appear (default "Tooling rec")
  CLAUDE_FOOTER_MIN_CHARS  replies shorter than this are exempt (default 1200)
  CLAUDE_FOOTER_DISABLE=1  turn the check off"""
import json, os, sys

MARKER = os.getenv("CLAUDE_FOOTER_MARKER", "Tooling rec")
MIN_CHARS = int(os.getenv("CLAUDE_FOOTER_MIN_CHARS", "1200"))


def last_assistant_text(path):
    text = ""
    with open(path) as f:
        for line in f:
            try:
                e = json.loads(line)
            except ValueError:
                continue
            if e.get("type") == "user" and not e.get("toolUseResult") and isinstance(e.get("message", {}).get("content"), str):
                text = ""  # new human turn: reset
            if e.get("type") == "assistant":
                for c in e.get("message", {}).get("content", []):
                    if c.get("type") == "text":
                        text += c["text"] + "\n"
    return text


def main():
    if os.getenv("CLAUDE_FOOTER_DISABLE") == "1":
        return
    data = json.load(sys.stdin)
    if data.get("stop_hook_active"):
        return  # one nudge max, no loops
    text = last_assistant_text(data["transcript_path"])
    if len(text) >= MIN_CHARS and MARKER.lower() not in text.lower():
        print(json.dumps({"decision": "block", "reason":
            f"Standing rule: add one '{MARKER}:' line naming the command/skill/connector/rule "
            f"already installed that would have improved this output (or say none fit)."}))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass  # never block the session on a hook error
