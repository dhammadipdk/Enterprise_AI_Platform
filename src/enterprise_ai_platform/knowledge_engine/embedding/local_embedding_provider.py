"""
Local embedding provider.

Uses sentence-transformers to embed text entirely on-device — no API
key, no per-call cost, no network dependency beyond the one-time model
download. This is the default provider for InsureAI's V1 pitch, given
there is no budget for a paid embedding API.
"""

from __future__ import annotations

from enterprise_ai_platform.knowledge_engine.embedding.base_embedding_provider import (
    BaseEmbeddingProvider,
)


class LocalEmbeddingProvider(BaseEmbeddingProvider):
    """
    Embeds text locally using a sentence-transformers model.

    The model is loaded lazily on first use, not at construction time,
    so simply creating this provider (e.g. as part of KnowledgeService's
    default wiring) stays fast and offline. Only the first embed_text /
    embed_batch call pays the model download and load cost.
    """

    DEFAULT_MODEL_NAME = "all-MiniLM-L6-v2"

    DEFAULT_DIMENSION = 384

    def __init__(
        self,
        model_name: str = DEFAULT_MODEL_NAME,
        dimension: int = DEFAULT_DIMENSION,
    ) -> None:

        self._model_name = model_name

        self._dimension = dimension

        self._model = None

    @property
    def name(self) -> str:
        return f"local:{self._model_name}"

    @property
    def dimension(self) -> int:
        return self._dimension

    def embed_text(self, text: str) -> list[float]:

        return self.embed_batch([text])[0]

    def embed_batch(self, texts: list[str]) -> list[list[float]]:

        if not texts:
            return []

        model = self._get_model()

        vectors = model.encode(
            texts,
            convert_to_numpy=True,
        )

        return [vector.tolist() for vector in vectors]

    def _get_model(self):
        """
        Lazily construct and cache the sentence-transformers model.
        """

        if self._model is None:

            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(self._model_name)

            actual_dimension = self._model.get_embedding_dimension()

            if actual_dimension != self._dimension:
                raise ValueError(
                    f"Configured dimension ({self._dimension}) does not "
                    f"match the actual output dimension "
                    f"({actual_dimension}) of model '{self._model_name}'."
                )

        return self._model