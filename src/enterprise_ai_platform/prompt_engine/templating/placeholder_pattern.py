"""
Shared prompt placeholder pattern.

Single source of truth for what counts as a "{{variable}}" reference
in a prompt's system_prompt / user_prompt text. Both PromptCompiler
(which extracts referenced variables for validation) and
PromptRenderer (which substitutes them at render time) import this
same pattern, so the two can never silently drift apart -- a variable
the Compiler considers "referenced" is guaranteed to be one the
Renderer will actually substitute.
"""

from __future__ import annotations

import re

VARIABLE_PATTERN = re.compile(r"\{\{\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\}\}")