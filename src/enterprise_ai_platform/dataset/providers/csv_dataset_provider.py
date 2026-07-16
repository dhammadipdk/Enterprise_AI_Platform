"""
CSV dataset provider.
"""

from pathlib import Path
from typing import Any

import pandas as pd

from enterprise_ai_platform.framework.base import BaseProvider


class CSVDatasetProvider(BaseProvider[list[dict[str, Any]]]):
    """
    Generic CSV dataset provider.
    """

    def load(
        self,
        path: Path,
    ) -> list[dict[str, Any]]:

        dataframe = pd.read_csv(path)

        return dataframe.to_dict(orient="records")

    def save(
        self,
        data: list[dict[str, Any]],
        path: Path,
    ) -> None:

        dataframe = pd.DataFrame(data)

        dataframe.to_csv(
            path,
            index=False,
        )