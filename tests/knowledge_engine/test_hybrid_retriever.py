from enterprise_ai_platform.knowledge_engine import Chunk
from enterprise_ai_platform.knowledge_engine.retrieval import HybridRetriever
from enterprise_ai_platform.knowledge_engine.vector_store import VectorStoreMatch


def _match(
    content: str,
    score: float,
    domain: str = "policy",
    asset: str = "glossary",
    chunk_index: int = 0,
) -> VectorStoreMatch:

    return VectorStoreMatch(
        chunk=Chunk(
            content=content,
            repository="insurance",
            domain=domain,
            asset=asset,
            chunk_index=chunk_index,
        ),
        score=score,
    )


def test_hybrid_retrieve_combines_both_sources() -> None:

    def semantic_search(repository, query_text, top_k=5, domain=None):
        return [_match("semantic only", 0.9, chunk_index=0)]

    def keyword_search(repository, query_text, top_k=5, domain=None):
        return [_match("keyword only", 5.2, chunk_index=1)]

    retriever = HybridRetriever(semantic_search, keyword_search)

    results = retriever.retrieve("insurance", "query")

    contents = {match.chunk.content for match in results}

    assert contents == {"semantic only", "keyword only"}


def test_hybrid_retrieve_ranks_chunk_found_in_both_first() -> None:

    def semantic_search(repository, query_text, top_k=5, domain=None):
        return [
            _match("in both", 0.95, chunk_index=0),
            _match("semantic only", 0.80, chunk_index=1),
        ]

    def keyword_search(repository, query_text, top_k=5, domain=None):
        return [
            _match("in both", 8.0, chunk_index=0),
            _match("keyword only", 6.0, chunk_index=2),
        ]

    retriever = HybridRetriever(semantic_search, keyword_search)

    results = retriever.retrieve("insurance", "query")

    assert results[0].chunk.content == "in both"


def test_hybrid_retrieve_respects_top_k() -> None:

    def semantic_search(repository, query_text, top_k=5, domain=None):
        return [
            _match("a", 0.9, chunk_index=0),
            _match("b", 0.8, chunk_index=1),
            _match("c", 0.7, chunk_index=2),
        ]

    def keyword_search(repository, query_text, top_k=5, domain=None):
        return []

    retriever = HybridRetriever(semantic_search, keyword_search)

    results = retriever.retrieve("insurance", "query", top_k=2)

    assert len(results) == 2


def test_hybrid_retrieve_passes_candidate_pool_to_both_sources() -> None:

    calls = []

    def semantic_search(repository, query_text, top_k=5, domain=None):
        calls.append(("semantic", top_k))
        return []

    def keyword_search(repository, query_text, top_k=5, domain=None):
        calls.append(("keyword", top_k))
        return []

    retriever = HybridRetriever(semantic_search, keyword_search)

    retriever.retrieve("insurance", "query", top_k=3, candidate_pool=15)

    assert ("semantic", 15) in calls

    assert ("keyword", 15) in calls


def test_hybrid_retrieve_candidate_pool_at_least_top_k() -> None:

    calls = []

    def semantic_search(repository, query_text, top_k=5, domain=None):
        calls.append(top_k)
        return []

    def keyword_search(repository, query_text, top_k=5, domain=None):
        return []

    retriever = HybridRetriever(semantic_search, keyword_search)

    retriever.retrieve("insurance", "query", top_k=10, candidate_pool=3)

    assert calls == [10]


def test_hybrid_retrieve_empty_when_both_sources_empty() -> None:

    def semantic_search(repository, query_text, top_k=5, domain=None):
        return []

    def keyword_search(repository, query_text, top_k=5, domain=None):
        return []

    retriever = HybridRetriever(semantic_search, keyword_search)

    assert retriever.retrieve("insurance", "query") == []


def test_hybrid_retrieve_passes_domain_through() -> None:

    calls = []

    def semantic_search(repository, query_text, top_k=5, domain=None):
        calls.append(("semantic", domain))
        return []

    def keyword_search(repository, query_text, top_k=5, domain=None):
        calls.append(("keyword", domain))
        return []

    retriever = HybridRetriever(semantic_search, keyword_search)

    retriever.retrieve("insurance", "query", domain="claims")

    assert ("semantic", "claims") in calls

    assert ("keyword", "claims") in calls