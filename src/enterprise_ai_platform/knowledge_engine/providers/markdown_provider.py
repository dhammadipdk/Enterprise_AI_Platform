"""
Markdown knowledge provider.
"""

from __future__ import annotations

from pathlib import Path

from enterprise_ai_platform.framework.base import BaseProvider


class MarkdownProvider(BaseProvider[str]):
    """
    Loads Markdown knowledge assets (READMEs, domain overviews) as raw text.
    """

    def load(
        self,
        path: Path,
    ) -> str:
        """
        Load a Markdown file as text.
        """

        return path.read_text(encoding="utf-8")

    def save(
        self,
        data: str,
        path: Path,
    ) -> None:
        """
        Save text to a Markdown file.
        """

        path.write_text(data, encoding="utf-8")