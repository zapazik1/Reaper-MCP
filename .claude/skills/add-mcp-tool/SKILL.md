---
name: add-mcp-tool
description: Step-by-step checklist for adding a new MCP tool to this ReaperMCP fork end to end — Python module reaper_mcp/tools/my_*.py, the matching Lua handler in the REAPER bridge, undo classification, producer profile, tests, pytest + ruff, and restart reminders. Use it whenever the user asks for a new REAPER tool/command/capability exposed to Claude ("add a tool that…", "make the MCP able to…", "/add-mcp-tool"), or when extending an existing my_* tool with a new bridge command.
---

# Add an MCP tool to the ReaperMCP fork

A tool is two halves that must agree: a Python function that validates input
and sends a command name, and a Lua handler with exactly that name inside
REAPER. Missing either half fails only at runtime ("Unknown command"), and
the repo's tests enforce undo classification — so go through every step.

Read `CLAUDE.md` first; it has the fork rules (own code in `my_*`, `-- fork:`
markers, no `mix_engine/` changes). Use the `reascript-api` skill for every
`reaper.*` call.

## Checklist

Copy this into your task list and tick it off:

1. [ ] Pick a topic name `<topic>` and command names (`snake_case`, ideally
       prefixed `my_`, e.g. `my_get_reaper_version`). Check the name is free:
       `grep -n "<name>" reaper_scripts/reaper_mcp_server.lua reaper_mcp/tools/*.py`
2. [ ] Look up every REAPER function you'll call (`reascript-api`).
3. [ ] Python module `reaper_mcp/tools/my_<topic>.py` (template below), and
       its name added to `_EXPECTED_MODULES` in `reaper_mcp/tool_registry.py`
       as `"my_<topic>",  # fork:` (tests/test_tool_registry.py fails otherwise).
4. [ ] Lua handler in the fork block of `reaper_scripts/reaper_mcp_server.lua`.
5. [ ] Undo decision for every handler that changes the project.
6. [ ] Producer profile: add `my_<topic>` to `include_modules` in
       `producer/profile.toml` if a producer should have it (read-only and
       mixing tools usually yes; dev/debug tools no).
7. [ ] Tests `tests/test_my_<topic>.py`.
8. [ ] `.venv/bin/pytest tests/ -x -q` and `.venv/bin/ruff check .` pass.
9. [ ] Report changed files and remind the user: **re-run the bridge script in
       REAPER** (Lua changed) and **restart the Claude Code session** (new tool).

Use `.venv/bin/...` explicitly: in this user's zsh `python`/`pip` are aliases
to a global 3.11 and bypass the venv.

## 3. Python module

The registry imports any module in `reaper_mcp/tools/` with `register(mcp)`,
but it also keeps a sanity list, `_EXPECTED_MODULES` in
`reaper_mcp/tool_registry.py`; add the new module name there (one line marked
`# fork:`), or `test_every_registrable_module_is_expected` fails. Use the
shared client from `main`, the way upstream modules do:

```python
from mcp.server.fastmcp import FastMCP

from reaper_mcp_shared.error_codes import ErrorCode, ReaperMCPError


def register(mcp: FastMCP):
    from reaper_mcp.main import client

    @mcp.tool()
    async def my_track_set_color(track_index: int, rgb: str) -> dict:
        """Set a track's colour.

        Args:
            track_index: 0-based track index.
            rgb: Hex colour like "#ff8800".
        """
        if track_index < 0:
            raise ReaperMCPError(ErrorCode.VALUE_OUT_OF_RANGE, f"track_index must be >= 0, got {track_index}")
        if len(rgb) != 7 or not rgb.startswith("#"):
            raise ReaperMCPError(ErrorCode.INVALID_PARAMETER, f"rgb must look like #rrggbb, got {rgb!r}")
        return await client.execute("my_track_set_color", track_index=track_index, rgb=rgb)
```

Rules from CONTRIBUTING.md: range-check numbers, length-cap strings, file
paths absolute only; error messages name the bad value. The docstring is what
the model sees — say what it does and what each arg means, briefly.
`client.execute_long(...)` only for bulk writes that may exceed 30 s.

## 4. Lua handler

Own handlers live in one fork block (`local my = {}` … `-- fork: end`) placed
right **before** the "Command dispatch table" section, so helpers like
`get_track` are in scope. It already exists — add new `function my.…` inside
it. The merge line `for k, v in pairs(my) do handlers[k] = v end -- fork:`
already sits right after `pairs(script)`; don't add another. Because merges
overwrite by key, a `my.*` name equal to an upstream command would silently
replace it — grep first (checklist step 1). If the block is ever missing,
recreate it like this:

```lua
-- fork: handlers of the zapazik1 fork (see CLAUDE.md)
local my = {}

function my.my_track_set_color(p)
  local tr, _, err = get_numbered_track(p, "track_index")
  if not tr then return nil, err end
  local r, g, b = p.rgb:match("^#(%x%x)(%x%x)(%x%x)$")
  if not r then return nil, "Invalid rgb: " .. tostring(p.rgb) end
  local native = reaper.ColorToNative(tonumber(r, 16), tonumber(g, 16), tonumber(b, 16))
  reaper.SetTrackColor(tr, native)
  return {track_index = p.track_index, rgb = p.rgb}
end
-- fork: end
```

and next to the other merges:

```lua
for k, v in pairs(my) do handlers[k] = v end -- fork:
```

Conventions: the function name equals the Python command string; return a
table on success or `nil, "message"` on failure (the dispatcher turns that
into an error response); never `load`/`dofile`/`loadstring`. Write the
definition as `function my.<name>(p)` at column 0 — the undo test finds
handlers by that exact pattern.

## 5. Undo classification

`tests/test_lua_undo_points.py` scans every handler; if it calls something
mutating (`Set*`, `Insert*`, `Delete*`, `TrackFX_Set*`, `MIDI_Set*`, …) without
its own `Undo_BeginBlock` it must be listed in a table in the bridge:

| Handler changes… | Do this |
|---|---|
| a simple property (fader, colour, FX param, marker, send) | add `name = true,` to `UNDO_POINT_COMMANDS` |
| items, takes, MIDI notes/CC | add to `UNDO_POINT_COMMANDS` **and** `UNDO_ITEM_COMMANDS` (undo blocks don't capture MIDI) |
| many tracks/FX/routes in one call | wrap in `reaper.Undo_BeginBlock()` / `reaper.Undo_EndBlock("MCP: …", -1)` |
| nothing (read-only) but trips the regex, or files/renders/selection | add `name = "reason",` to `UNDO_EXEMPT_COMMANDS` |

Add the lines with a `-- fork:` comment. Read-only handlers that call only
`Get*`/`Count*` need no entry.

## 7. Tests

Follow `tests/test_master_bus_batch.py`: patch the shared client, register the
module on a fresh FastMCP, call the tool function directly.

```python
import asyncio
from unittest.mock import AsyncMock, patch

import pytest
from mcp.server.fastmcp import FastMCP

from reaper_mcp_shared.error_codes import ReaperMCPError


def _tool(name):
    mcp = FastMCP("t")
    client = AsyncMock()
    client.execute = AsyncMock(return_value={"success": True})
    with patch("reaper_mcp.main.client", client):
        from reaper_mcp.tools.my_colors import register
        register(mcp)
    return mcp._tool_manager._tools[name].fn, client


def test_sends_the_bridge_command():
    fn, client = _tool("my_track_set_color")
    asyncio.run(fn(track_index=0, rgb="#ff8800"))
    client.execute.assert_awaited_once_with("my_track_set_color", track_index=0, rgb="#ff8800")


def test_rejects_bad_colour():
    fn, _ = _tool("my_track_set_color")
    with pytest.raises(ReaperMCPError):
        asyncio.run(fn(track_index=0, rgb="orange"))
```

Also assert the Lua side exists, so the two halves can't drift:

```python
from pathlib import Path
LUA = Path(__file__).resolve().parent.parent / "reaper_scripts" / "reaper_mcp_server.lua"

def test_lua_handler_exists():
    assert "function my.my_track_set_color(p)" in LUA.read_text(encoding="utf-8")
```

`tests/test_lua_syntax.py` already parses the whole bridge with `lupa`, so a
Lua syntax error shows up in the normal test run. To test the handler's
*logic* without REAPER, cut the fork block out of the bridge, run it under
`lupa` with a stub `reaper` table and call the function — working example:
`tests/test_my_info.py`.

Note for the undo test: it treats everything from `function my.<last>(p)` up to
the next `function x.y(` as that handler's text, so the last handler in the
fork block "contains" the dispatch table and block-guard code. If it is
reported as unclassified while being read-only, that's why — check the
handler itself, then classify or reorder.

## 9. Finish

List changed files (`git status --short`), confirm pytest/ruff output, then
remind: re-run `reaper_mcp_server.lua` in REAPER (Actions → the script → Run),
restart Claude Code so the new tool is loaded, and don't run developer and
producer sessions at the same time (shared IPC directory).
