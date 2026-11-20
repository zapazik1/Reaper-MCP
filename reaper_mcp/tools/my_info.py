"""fork: read-only info about the running REAPER instance."""

from mcp.server.fastmcp import FastMCP


def register(mcp: FastMCP):
    from reaper_mcp.main import client

    @mcp.tool()
    async def my_get_reaper_version() -> dict:
        """Get the running REAPER version (reaper.GetAppVersion). Read-only.

        Returns version_string (raw, e.g. "7.80/macOS-arm64"), version
        ("7.80") and platform ("macOS-arm64"; empty on 32-bit Windows,
        where REAPER reports no OS/arch suffix).
        """
        return await client.execute("my_get_reaper_version")
