"""
YAML knowledge provider.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from enterprise_ai_platform.framework.base import BaseProvider


class YAMLProvider(BaseProvider[Any]):
    """
    Loads YAML knowledge assets (for example, prompt definitions
    stored under knowledge/platform/prompts/) as parsed Python
    objects, typically a dict.
    """

    def load(self, path: Path) -> Any:
        """
        Load and parse a YAML file.
        """

        raw = path.read_text(encoding="utf-8")

        return yaml.safe_load(raw)

    def save(self, data: Any, path: Path) -> None:
        """
        Serialize data to a YAML file.
        """

        path.write_text(
            yaml.safe_dump(data, sort_keys=False),
            encoding="utf-8",
        )