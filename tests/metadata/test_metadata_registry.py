from enterprise_ai_platform.metadata import (
    MetadataRecord,
    MetadataRegistry,
)


def test_metadata_registry() -> None:

    registry = MetadataRegistry()

    record = MetadataRecord(
        name="policy_catalog",
        source="policy_catalog.csv",
        data={
            "columns": 10,
            "rows": 50,
        },
    )

    registry.register(
        "policy_catalog",
        record,
    )

    assert registry.exists("policy_catalog")

    assert registry.get("policy_catalog") == record

    assert registry.names() == [
        "policy_catalog",
    ]