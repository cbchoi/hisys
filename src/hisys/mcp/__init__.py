"""Fail-closed MCP gateway surface for Hisys.

The first slice is transport-independent and local/fixture-only. It exposes
bounded wrappers around existing Hisys CLI/runtime seams without enabling live
provider calls, publication, mutation, or model sampling.
"""

__all__ = ["contracts", "config", "cli_adapter", "tools"]
