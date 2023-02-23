from __future__ import annotations

try:
    # noinspection PyProtectedMember
    from pavo._version import version as __version__
except ImportError:
    __version__ = "not-installed"
