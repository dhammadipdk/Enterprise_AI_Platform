"""
Model capability.
"""

from __future__ import annotations

from enum import Enum


class ModelCapability(str, Enum):
    """
    Every capability the frozen spec (Section 10) names.
    """

    CHAT = "chat"

    COMPLETION = "completion"

    EMBEDDING = "embedding"

    VISION = "vision"

    AUDIO = "audio"

    SPEECH = "speech"

    IMAGE_GENERATION = "image_generation"

    FUNCTION_CALLING = "function_calling"

    STRUCTURED_OUTPUT = "structured_output"

    STREAMING = "streaming"

    REASONING = "reasoning"