#!/usr/bin/env python3
"""Look up REAPER ReaScript functions (Lua flavour) in REAPER's own HTML help.

Usage:
  reascript_lookup.py NAME [NAME ...]        exact lookup (case-insensitive),
                                             prints Lua signature + description
  reascript_lookup.py -s REGEX               search function names
  reascript_lookup.py -s REGEX -d            search names and descriptions
  reascript_lookup.py --html PATH ...        use another copy of the help file

Only the standard library is used, so any python3 works.
"""

import argparse
import difflib
import html
import re
import sys
from pathlib import Path

DEFAULT_HTML = Path(__file__).resolve().parent.parent / "references" / "reascripthelp.html"

ANCHOR = re.compile(r'<a name="([^"]+)"><hr></a>')
LUA_DIV = re.compile(r'<div class="l_func">.*?<code>(.*?)</code>', re.S)
LUA_BUILTIN = re.compile(r"^\s*(?:<br>)?\s*Lua: <code>(.*?)</code>", re.S)
FUNC_DIVS = re.compile(r'<div class="[a-z]_func">.*?</div>', re.S)
TAG = re.compile(r"<[^>]+>")


def clean(fragment: str) -> str:
    text = fragment.replace("<br>", "\n")
    text = html.unescape(TAG.sub("", text))
    lines = [" ".join(line.split()) for line in text.splitlines()]
    return "\n".join(line for line in lines if line).strip()


def parse(path: Path) -> dict:
    source = path.read_text(encoding="utf-8", errors="replace")
    marks = list(ANCHOR.finditer(source))
    entries = {}
    for i, m in enumerate(marks):
        name = m.group(1)
        end = marks[i + 1].start() if i + 1 < len(marks) else len(source)
        body = source[m.end():end]
        lua = LUA_DIV.search(body)
        if lua:
            signature = clean(lua.group(1))
        else:
            builtin = LUA_BUILTIN.search(body)
            if not builtin:
                continue  # C/EEL/Python-only entry, not callable from Lua
            signature = clean(builtin.group(1))
            body = body[builtin.end():]
        description = clean(FUNC_DIVS.sub("", body).replace("Lua: ", "", 0))
        display = name[4:] if name.startswith("lua_") else name
        entries[display] = (signature, description)
    return entries


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("names", nargs="*", help="exact function names, e.g. GetAppVersion MIDI_InsertNote")
    ap.add_argument("-s", "--search", help="regex over function names (case-insensitive)")
    ap.add_argument("-d", "--desc", action="store_true", help="with -s: also search descriptions")
    ap.add_argument("-n", "--limit", type=int, default=40, help="max search results (default 40)")
    ap.add_argument("--html", type=Path, default=DEFAULT_HTML)
    args = ap.parse_args()

    if not args.html.is_file():
        print(f"Help file not found: {args.html}", file=sys.stderr)
        return 2
    entries = parse(args.html)
    lower = {k.lower(): k for k in entries}

    if args.search:
        rx = re.compile(args.search, re.I)
        hits = [k for k, (sig, desc) in entries.items() if rx.search(k) or (args.desc and rx.search(desc))]
        for k in hits[: args.limit]:
            print(f"{k}\n    {entries[k][0]}")
        if len(hits) > args.limit:
            print(f"... {len(hits) - args.limit} more, narrow the pattern or raise -n")
        if not hits:
            print("No matches.")
        return 0 if hits else 1

    if not args.names:
        ap.print_help()
        return 2

    status = 0
    for raw in args.names:
        key = lower.get(raw.removeprefix("reaper.").lower())
        if key is None:
            status = 1
            close = difflib.get_close_matches(raw, entries.keys(), n=5, cutoff=0.6)
            print(f"== {raw}: not in the Lua API" + (f". Did you mean: {', '.join(close)}?" if close else "."))
            continue
        sig, desc = entries[key]
        print(f"== {key}\nLua: {sig}\n{desc}\n")
    return status


if __name__ == "__main__":
    sys.exit(main())
