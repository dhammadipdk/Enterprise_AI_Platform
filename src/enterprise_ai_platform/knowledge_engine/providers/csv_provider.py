"""
CSV knowledge provider.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from enterprise_ai_platform.framework.base import BaseProvider


class CSVProvider(BaseProvider[list[dict[str, Any]]]):
    """
    Loads CSV knowledge assets (schemas, glossaries, entity catalogs)
    as a list of row dictionaries.
    """

    def load(
        self,
        path: Path,
    ) -> list[dict[str, Any]]:
        """
        Load a CSV file.
        """

        dataframe = pd.read_csv(path)

        return dataframe.to_dict(orient="records")

    def save(
        self,
        data: list[dict[str, Any]],
        path: Path,
    ) -> None:
        """
        Save records to CSV.
        """

        dataframe = pd.DataFrame(data)

        dataframe.to_csv(
            path,
            index=False,
        )