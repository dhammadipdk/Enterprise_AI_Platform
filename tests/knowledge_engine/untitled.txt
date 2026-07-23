from enterprise_ai_platform.knowledge_engine import (
    KnowledgeAsset,
    KnowledgeDomain,
    KnowledgeRepository,
)
from enterprise_ai_platform.knowledge_engine.graph import GraphBuilder


def _repository_with_relationships(rows: list[dict]) -> KnowledgeRepository:

    domain = KnowledgeDomain(
        name="policy",
        assets=[
            KnowledgeAsset(
                name="relationships",
                asset_type="relationship",
                path="policy/relationships.csv",
            ),
        ],
    )

    def _content_loader(repository, domain_name, asset_name):
        return rows

    builder = GraphBuilder(_content_loader)

    repository = KnowledgeRepository(domains=[domain])

    return builder.build("insurance", repository)


def test_build_produces_one_edge_per_row() -> None:

    graph = _repository_with_relationships(
        [
            {"subject": "Policy", "predicate": "has", "object": "Coverage"},
            {
                "subject": "Coverage",
                "predicate": "has",
                "object": "Exclusion",
            },
        ]
    )

    assert graph.edge_count() == 2


def test_build_sets_domain_and_source_asset_provenance() -> None:

    graph = _repository_with_relationships(
        [{"subject": "Policy", "predicate": "has", "object": "Coverage"}]
    )

    edge = graph.edges[0]

    assert edge.domain == "policy"

    assert edge.source_asset == "relationships"


def test_build_ignores_non_relationship_assets() -> None:

    def _content_loader(repository, domain_name, asset_name):
        raise AssertionError(
            "content loader should not be called for non-relationship "
            "assets"
        )

    domain = KnowledgeDomain(
        name="policy",
        assets=[
            KnowledgeAsset(
                name="canonical_schema",
                asset_type="schema",
                path="policy/canonical_schema.csv",
            ),
        ],
    )

    repository = KnowledgeRepository(domains=[domain])

    builder = GraphBuilder(_content_loader)

    graph = builder.build("insurance", repository)

    assert graph.edge_count() == 0


def test_build_combines_relationships_across_domains() -> None:

    def _content_loader(repository, domain_name, asset_name):
        if domain_name == "policy":
            return [
                {
                    "subject": "Policy",
                    "predicate": "has",
                    "object": "Coverage",
                }
            ]
        return [
            {
                "subject": "Vehicle",
                "predicate": "classified_as",
                "object": "UsedCar",
            }
        ]

    policy_domain = KnowledgeDomain(
        name="policy",
        assets=[
            KnowledgeAsset(
                name="relationships",
                asset_type="relationship",
                path="policy/relationships.csv",
            ),
        ],
    )

    vehicle_domain = KnowledgeDomain(
        name="vehicle",
        assets=[
            KnowledgeAsset(
                name="relationships",
                asset_type="relationship",
                path="vehicle/relationships.csv",
            ),
        ],
    )

    repository = KnowledgeRepository(domains=[policy_domain, vehicle_domain])

    builder = GraphBuilder(_content_loader)

    graph = builder.build("insurance", repository)

    assert graph.edge_count() == 2

    assert {edge.domain for edge in graph.edges} == {"policy", "vehicle"}


def test_build_raises_clear_error_on_missing_column() -> None:

    import pytest

    def _content_loader(repository, domain_name, asset_name):
        return [{"subject": "Policy", "predicate": "has"}]

    domain = KnowledgeDomain(
        name="policy",
        assets=[
            KnowledgeAsset(
                name="relationships",
                asset_type="relationship",
                path="policy/relationships.csv",
            ),
        ],
    )

    repository = KnowledgeRepository(domains=[domain])

    builder = GraphBuilder(_content_loader)

    with pytest.raises(ValueError):
        builder.build("insurance", repository)