"""fork: undo classification for the fork's own `my.*` handlers.

tests/test_lua_undo_points.py treats a handler's text as everything up to the
next `function x.y(`. For the last handler in the fork block that span runs
past the dispatch table into the block guard, which contains
`Undo_BeginBlock`, so a mutating `my.*` handler placed last would never be
reported. Here every `my.*` handler is checked on its own text only.
"""

import re

from tests.test_lua_undo_points import MUTATING_CALL, _classified, _source

MY_HANDLER = re.compile(r"^function my\.([a-z_0-9]+)\(", re.M)


def _fork_handlers(source: str) -> dict:
    start = source.index("local my = {}")
    block = source[start: source.index("-- fork: end", start)]
    starts = [(m.start(), m.group(1)) for m in MY_HANDLER.finditer(block)]
    return {
        name: block[pos: starts[i + 1][0] if i + 1 < len(starts) else len(block)]
        for i, (pos, name) in enumerate(starts)
    }


def test_fork_block_has_handlers():
    assert _fork_handlers(_source())


def test_every_mutating_fork_handler_is_classified():
    source = _source()
    recorded, exempt = _classified(source)
    unclassified = [
        name
        for name, text in _fork_handlers(source).items()
        if MUTATING_CALL.search(text)
        and "Undo_BeginBlock" not in text
        and name not in recorded
        and name not in exempt
    ]
    assert not unclassified, (
        f"Fork handlers that change the project without an undo decision: {sorted(unclassified)}. "
        "Add each to UNDO_POINT_COMMANDS (items/MIDI also UNDO_ITEM_COMMANDS) or "
        "UNDO_EXEMPT_COMMANDS with a reason, or wrap it in its own undo block."
    )
