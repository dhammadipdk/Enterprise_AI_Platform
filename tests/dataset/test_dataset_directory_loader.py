from pathlib import Path

from enterprise_ai_platform.dataset import (
    DatasetLoader,
    DatasetRegistry,
)


def test_directory_loader(tmp_path: Path) -> None:

    (tmp_path / "users.csv").write_text(
        "id,name\n1,Alice\n2,Bob\n"
    )

    (tmp_path / "products.csv").write_text(
        "id,title\n1,Laptop\n"
    )

    registry = DatasetRegistry()

    loader = DatasetLoader(registry)

    loader.load_directory(tmp_path)

    assert registry.exists("users")

    assert registry.exists("products")

    assert len(registry.get("users").records) == 2

    assert len(registry.get("products").records) == 1