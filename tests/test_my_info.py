"""fork: my_get_reaper_version — Python tool and its Lua handler."""

import asyncio
import re
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from mcp.server.fastmcp import FastMCP

LUA = Path(__file__).resolve().parent.parent / "reaper_scripts" / "reaper_mcp_server.lua"


def _tool(name):
    mcp = FastMCP("t")
    client = AsyncMock()
    client.execute = AsyncMock(return_value={"success": True})
    with patch("reaper_mcp.main.client", client):
        from reaper_mcp.tools.my_info import register
        register(mcp)
    return mcp._tool_manager._tools[name].fn, client


def test_sends_the_bridge_command():
    fn, client = _tool("my_get_reaper_version")
    asyncio.run(fn())
    client.execute.assert_awaited_once_with("my_get_reaper_version")


def test_lua_handler_exists():
    source = LUA.read_text(encoding="utf-8")
    assert "function my.my_get_reaper_version(p)" in source
    assert "for k, v in pairs(my) do handlers[k] = v end -- fork:" in source


def _fork_block() -> str:
    source = LUA.read_text(encoding="utf-8")
    m = re.search(r"^local my = \{\}\n.*?^-- fork: end$", source, re.M | re.S)
    assert m, "fork block with `local my = {}` not found"
    return m.group(0)


@pytest.mark.parametrize(
    "raw, version, platform",
    [
        ("7.80/macOS-arm64", "7.80", "macOS-arm64"),
        ("6.17/x64", "6.17", "x64"),
        ("6.17", "6.17", ""),
    ],
)
def test_lua_handler_splits_version_and_platform(raw, version, platform):
    lupa = pytest.importorskip("lupa")
    lua = lupa.LuaRuntime()
    lua.globals().reaper = lua.table(GetAppVersion=lambda: raw)
    handler = lua.execute(_fork_block() + "\nreturn my.my_get_reaper_version")
    result = handler(lua.table())
    assert result["version_string"] == raw
    assert result["version"] == version
    assert result["platform"] == platform
