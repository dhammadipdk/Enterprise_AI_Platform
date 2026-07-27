"""
Memory type.
"""

from __future__ import annotations

from enum import Enum


class MemoryType(str, Enum):
    """
    Every memory type the frozen spec (Section 8) names.
    """

    WORKING = "working"

    EPISODIC = "episodic"

    SEMANTIC = "semantic"

    PROCEDURAL = "procedural"

    REFERENCE = "reference"

    SYSTEM = "system"