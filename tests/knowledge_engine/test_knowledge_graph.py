from enterprise_ai_platform.knowledge_engine import KnowledgeGraphEdge
from enterprise_ai_platform.knowledge_engine.graph import KnowledgeGraph


def _edge(
    subject: str,
    predicate: str,
    object: str,
    domain: str = "insurance",
    source_asset: str = "relationships",
) -> KnowledgeGraphEdge:

    return KnowledgeGraphEdge(
        subject=subject,
        predicate=predicate,
        object=object,
        domain=domain,
        source_asset=source_asset,
    )


def _sample_graph() -> KnowledgeGraph:

    return KnowledgeGraph(
        [
            _edge("Policy", "has", "Coverage"),
            _edge("Coverage", "has", "Exclusion"),
            _edge("Exclusion", "triggered_by", "ClaimEvent"),
            _edge("ClaimEvent", "affects", "Policyholder"),
            _edge("Policyholder", "owns", "Vehicle"),
            _edge("Vehicle", "classified_as", "UsedCar"),
            _edge("UsedCar", "eligible_for", "ThirdPartyInsurance"),
            _edge("UsedCar", "eligible_for", "ComprehensiveInsurance"),
        ]
    )


def test_empty_graph_has_no_edges_or_entities() -> None:

    graph = KnowledgeGraph([])

    assert graph.edge_count() == 0

    assert graph.entities() == []


def test_edge_count_and_edges() -> None:

    graph = _sample_graph()

    assert graph.edge_count() == 8

    assert len(graph.edges) == 8


def test_entities_includes_subjects_and_objects() -> None:

    graph = _sample_graph()

    entities = graph.entities()

    assert "Policy" in entities

    assert "ComprehensiveInsurance" in entities

    assert "UsedCar" in entities


def test_neighbors_returns_outgoing_edges() -> None:

    graph = _sample_graph()

    results = graph.neighbors("UsedCar")

    objects = {edge.object for edge in results}

    assert objects == {"ThirdPartyInsurance", "ComprehensiveInsurance"}


def test_neighbors_filtered_by_predicate() -> None:

    graph = _sample_graph()

    results = graph.neighbors("UsedCar", predicate="eligible_for")

    assert len(results) == 2


def test_neighbors_unknown_entity_returns_empty() -> None:

    graph = _sample_graph()

    assert graph.neighbors("NotAnEntity") == []


def test_incoming_returns_edges_pointing_to_entity() -> None:

    graph = _sample_graph()

    results = graph.incoming("UsedCar")

    assert len(results) == 1

    assert results[0].subject == "Vehicle"

    assert results[0].predicate == "classified_as"


def test_find_by_predicate_only() -> None:

    graph = _sample_graph()

    results = graph.find(predicate="has")

    pairs = {(edge.subject, edge.object) for edge in results}

    assert pairs == {("Policy", "Coverage"), ("Coverage", "Exclusion")}


def test_find_by_full_triple() -> None:

    graph = _sample_graph()

    results = graph.find(
        subject="UsedCar",
        predicate="eligible_for",
        object="ThirdPartyInsurance",
    )

    assert len(results) == 1


def test_find_with_no_filters_returns_all_edges() -> None:

    graph = _sample_graph()

    assert len(graph.find()) == 8


def test_traverse_respects_max_depth() -> None:

    graph = _sample_graph()

    shallow = graph.traverse("Policy", max_depth=1)

    assert {edge.object for edge in shallow} == {"Coverage"}

    deeper = graph.traverse("Policy", max_depth=3)

    assert {edge.object for edge in deeper} == {
        "Coverage",
        "Exclusion",
        "ClaimEvent",
    }


def test_traverse_stops_when_no_more_edges() -> None:

    graph = _sample_graph()

    # ComprehensiveInsurance has no outgoing edges at all.
    results = graph.traverse("ComprehensiveInsurance", max_depth=5)

    assert results == []