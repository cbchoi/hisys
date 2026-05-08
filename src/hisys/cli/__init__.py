"""Hisys CLI package.

Traceability: HISYS-PKG-ARCH-001 Section 3.

Keep this package initializer side-effect free so `python -m hisys.cli.main`
does not import the executable module before runpy executes it.
"""

__all__: list[str] = []
