"""
Model Engine bootstrap for the InsureAI pitch demo.

THE ONE LINE TO CHANGE, to switch which provider actually serves
requests:
"""

ACTIVE_PROVIDER = "ollama"  # "ollama" | "anthropic" | "openai"


from enterprise_ai_platform.model_engine import (
    AnthropicAdapter,
    ModelCapability,
    ModelDefinition,
    ModelService,
    OllamaAdapter,
    OpenAIAdapter,
    ProviderDefinition,
)


_MODEL_CONFIGS = {
    "ollama": {
        "provider": "ollama",
        "family": "llama",
        "configuration": {"ollama_model_name": "llama3.2:3b"},
    },
    "anthropic": {
        "provider": "anthropic",
        "family": "claude",
        # adjust to whatever specific Claude model string you're using
        "configuration": {"anthropic_model_name": "claude-sonnet-4-5"},
    },
    "openai": {
        "provider": "openai",
        "family": "gpt",
        "configuration": {"openai_model_name": "gpt-4o-mini"},
    },
}


def bootstrap_model_service(
    service: ModelService,
    active_provider: str = ACTIVE_PROVIDER,
) -> None:
    """
    Register all three provider adapters (always safe -- constructing
    an adapter never touches the network or needs credentials, only
    invoking it does), then register ONE model under the canonical
    name "explanation_model" pointing at whichever provider is active.

    Every place in your application that calls
    service.execute("explanation_model", ...) automatically uses
    whatever ACTIVE_PROVIDER points to -- switching providers means
    changing one line here and re-running this function, nothing else.
    """

    service.register_provider(
        ProviderDefinition(
            name="ollama",
            description="Local Ollama (free, no API key)",
        ),
        OllamaAdapter(),
    )

    service.register_provider(
        ProviderDefinition(name="anthropic", description="Anthropic API"),
        AnthropicAdapter(),
    )

    service.register_provider(
        ProviderDefinition(name="openai", description="OpenAI API"),
        OpenAIAdapter(),
    )

    config = _MODEL_CONFIGS[active_provider]

    service.register_model(
        ModelDefinition(
            name="explanation_model",
            version="1.0.0",
            provider=config["provider"],
            family=config["family"],
            capabilities=[ModelCapability.CHAT],
            configuration=config["configuration"],
        )
    )


# Usage:
#
#   service = ModelService()
#   bootstrap_model_service(service)
#   response = service.execute("explanation_model", "Zero dep matlab kya hai?")
#   print(response.text)
#
# To switch to Anthropic later: set ACTIVE_PROVIDER = "anthropic" above,
# set the ANTHROPIC_API_KEY environment variable, and re-run
# bootstrap_model_service(). No other code anywhere needs to change.