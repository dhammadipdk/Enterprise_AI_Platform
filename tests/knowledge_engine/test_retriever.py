from enterprise_ai_platform.knowledge_engine import Chunk
from enterprise_ai_platform.knowledge_engine.retrieval import Retriever
from enterprise_ai_platform.knowledge_engine.vector_store import VectorStoreMatch


def _match(
    content: str,
    score: float,
    domain: str = "policy",
    asset: str = "glossary",
) -> VectorStoreMatch:

    return VectorStoreMatch(
        chunk=Chunk(
            content=content,
            repository="insurance",
            domain=domain,
            asset=asset,
            chunk_index=0,
        ),
        score=score,
    )


def test_retrieve_passes_through_arguments() -> None:

    calls = []

    def fake_search(repository, query_text, top_k=5, domain=None):
        calls.append((repository, query_text, top_k, domain))
        return [_match("hello", 0.9)]

    retriever = Retriever(fake_search)

    results = retriever.retrieve(
        "insurance", "what is IDV?", top_k=3, domain="policy"
    )

    assert calls == [("insurance", "what is IDV?", 3, "policy")]

    assert len(results) == 1


def test_retrieve_filters_below_score_threshold() -> None:

    def fake_search(repository, query_text, top_k=5, domain=None):
        return [_match("strong match", 0.8), _match("weak match", 0.1)]

    retriever = Retriever(fake_search, score_threshold=0.5)

    results = retriever.retrieve("insurance", "query")

    assert len(results) == 1

    assert results[0].chunk.content == "strong match"


def test_retrieve_default_threshold_keeps_all_non_negative_scores() -> None:

    def fake_search(repository, query_text, top_k=5, domain=None):
        return [_match("a", 0.01), _match("b", 0.0)]

    retriever = Retriever(fake_search)

    results = retriever.retrieve("insurance", "query")

    assert len(results) == 2


def test_retrieve_default_threshold_excludes_negative_scores() -> None:

    def fake_search(repository, query_text, top_k=5, domain=None):
        return [_match("a", 0.5), _match("b", -0.1)]

    retriever = Retriever(fake_search)

    results = retriever.retrieve("insurance", "query")

    assert len(results) == 1

    assert results[0].chunk.content == "a"


def test_retrieve_as_context_formats_matches() -> None:

    def fake_search(repository, query_text, top_k=5, domain=None):
        return [
            _match(
                "IDV means Insured Declared Value",
                0.87,
                domain="policy",
                asset="glossary",
            )
        ]

    retriever = Retriever(fake_search)

    context = retriever.retrieve_as_context("insurance", "what is IDV?")

    assert "[1] (source: policy/glossary, score: 0.87)" in context

    assert "IDV means Insured Declared Value" in context


def test_retrieve_as_context_empty_when_no_matches() -> None:

    def fake_search(repository, query_text, top_k=5, domain=None):
        return []

    retriever = Retriever(fake_search)

    assert retriever.retrieve_as_context("insurance", "query") == ""


def test_retrieve_as_context_multiple_matches_are_separated() -> None:

    def fake_search(repository, query_text, top_k=5, domain=None):
        return [_match("first", 0.9), _match("second", 0.8)]

    retriever = Retriever(fake_search)

    context = retriever.retrieve_as_context("insurance", "query")

    assert "[1]" in context

    assert "[2]" in context

    assert context.count("\n\n") >= 1


def test_score_threshold_property() -> None:

    retriever = Retriever(lambda *a, **k: [], score_threshold=0.42)

    assert retriever.score_threshold == 0.42