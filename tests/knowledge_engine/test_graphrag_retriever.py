from enterprise_ai_platform.knowledge_engine import Chunk, KnowledgeGraphEdge
from enterprise_ai_platform.knowledge_engine.graph import KnowledgeGraph
from enterprise_ai_platform.knowledge_engine.retrieval import GraphRAGRetriever
from enterprise_ai_platform.knowledge_engine.vector_store import VectorStoreMatch


def _match(content: str, score: float = 0.8) -> VectorStoreMatch:

    return VectorStoreMatch(
        chunk=Chunk(
            content=content,
            repository="insurance",
            domain="policy",
            asset="glossary",
            chunk_index=0,
        ),
        score=score,
    )


def _edge(subject: str, predicate: str, object: str) -> KnowledgeGraphEdge:

    return KnowledgeGraphEdge(
        subject=subject,
        predicate=predicate,
        object=object,
        domain="insurance",
        source_asset="relationships",
    )


def _sample_graph() -> KnowledgeGraph:

    return KnowledgeGraph(
        [
            _edge("UsedCar", "eligible_for", "ThirdPartyInsurance"),
            _edge("UsedCar", "eligible_for", "ComprehensiveInsurance"),
            _edge("Vehicle", "classified_as", "UsedCar"),
        ]
    )


def test_returns_chunk_context_when_no_graph_exists() -> None:

    def hybrid_search(repository, query_text, top_k=5, domain=None):
        return [_match("Some relevant policy text.")]

    def graph_provider(repository):
        raise KeyError("no graph built")

    retriever = GraphRAGRetriever(hybrid_search, graph_provider)

    context = retriever.retrieve_context("insurance", "policy question")

    assert "Some relevant policy text." in context

    assert "Related facts" not in context


def test_appends_graph_facts_when_entity_found_in_query() -> None:

    def hybrid_search(repository, query_text, top_k=5, domain=None):
        return [_match("Generic policy information.")]

    def graph_provider(repository):
        return _sample_graph()

    retriever = GraphRAGRetriever(hybrid_search, graph_provider)

    context = retriever.retrieve_context(
        "insurance", "is my UsedCar covered?"
    )

    assert "Related facts (from knowledge graph):" in context

    assert "UsedCar eligible_for ThirdPartyInsurance" in context

    assert "UsedCar eligible_for ComprehensiveInsurance" in context


def test_appends_graph_facts_when_entity_found_in_chunk_content() -> None:

    def hybrid_search(repository, query_text, top_k=5, domain=None):
        return [_match("This clause discusses UsedCar eligibility rules.")]

    def graph_provider(repository):
        return _sample_graph()

    retriever = GraphRAGRetriever(hybrid_search, graph_provider)

    context = retriever.retrieve_context(
        "insurance", "what am I covered for?"
    )

    assert "UsedCar eligible_for ThirdPartyInsurance" in context


def test_no_graph_facts_when_no_entities_match() -> None:

    def hybrid_search(repository, query_text, top_k=5, domain=None):
        return [_match("Unrelated content.")]

    def graph_provider(repository):
        return _sample_graph()

    retriever = GraphRAGRetriever(hybrid_search, graph_provider)

    context = retriever.retrieve_context(
        "insurance", "something about the weather"
    )

    assert "Related facts" not in context


def test_traversal_depth_is_respected() -> None:

    def hybrid_search(repository, query_text, top_k=5, domain=None):
        return []

    def graph_provider(repository):
        return _sample_graph()

    shallow = GraphRAGRetriever(
        hybrid_search, graph_provider, traversal_depth=1
    )

    context_shallow = shallow.retrieve_context("insurance", "Vehicle")

    assert "UsedCar" in context_shallow

    assert "ThirdPartyInsurance" not in context_shallow

    deep = GraphRAGRetriever(hybrid_search, graph_provider, traversal_depth=2)

    context_deep = deep.retrieve_context("insurance", "Vehicle")

    assert "ThirdPartyInsurance" in context_deep


def test_facts_are_deduplicated_across_matched_entities() -> None:

    def hybrid_search(repository, query_text, top_k=5, domain=None):
        return []

    def graph_provider(repository):
        return _sample_graph()

    retriever = GraphRAGRetriever(
        hybrid_search, graph_provider, traversal_depth=2
    )

    context = retriever.retrieve_context(
        "insurance", "Vehicle and UsedCar eligibility"
    )

    assert context.count("ThirdPartyInsurance") == 1


def test_empty_when_no_chunks_and_no_graph_facts() -> None:

    def hybrid_search(repository, query_text, top_k=5, domain=None):
        return []

    def graph_provider(repository):
        raise KeyError("no graph")

    retriever = GraphRAGRetriever(hybrid_search, graph_provider)

    assert retriever.retrieve_context("insurance", "anything") == ""


def test_traversal_depth_property() -> None:

    retriever = GraphRAGRetriever(
        lambda *a, **k: [], lambda r: _sample_graph(), traversal_depth=3
    )

    assert retriever.traversal_depth == 3