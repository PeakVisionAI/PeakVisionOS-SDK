"""Compatibility import for the former ``agentos`` package.

New applications should use ``import pvos``. This module remains available
through the PeakVisionOS 1.x compatibility window.
"""
from pvos import *  # noqa: F401,F403
from pvos import __all__, __version__
