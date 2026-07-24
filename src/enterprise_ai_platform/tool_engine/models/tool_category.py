"""
Tool category.
"""

from __future__ import annotations

from enum import Enum


class ToolCategory(str, Enum):
    """
    Every category the frozen spec (Section 9) names.
    """

    KNOWLEDGE = "knowledge"

    DATABASE = "database"

    SEARCH = "search"

    FILESYSTEM = "filesystem"

    EMAIL = "email"

    CALENDAR = "calendar"

    VISION = "vision"

    AUDIO = "audio"

    OCR = "ocr"

    DOCUMENT = "document"

    TRANSLATION = "translation"

    WEB = "web"

    MATH = "math"

    CODE = "code"

    CUSTOM = "custom"