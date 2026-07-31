import pytest

from enterprise_ai_platform.model_engine import (
    BaseModelAdapter,
    ModelDefinition,
    ModelResponse,
    ModelService,
    ProviderDefinition,
)
from enterprise_ai_platform.tool_engine import ToolService
from enterprise_ai_platform.workflow_engine import ExecutionContext, WorkflowService

from enterprise_ai_platform.domains.insurance.policy_advisor.register_policy_advisor_workflow import (
    register_policy_advisor_workflow,
)

CATALOG_PATH = "src/enterprise_ai_platform/domains/insurance/knowledge/policy_catalog/entity_catalog.csv"


class _FakeExplanationAdapter(BaseModelAdapter):
    """
    Deterministic fake -- no real Ollama call. Echoes back which
    prompt_kind-flavored content it received, so tests can assert on
    control flow without depending on real model output.
    """

    def invoke(self, request, model):

        return ModelResponse(
            request_id=request.request_id,
            text=f"[FAKE RESPONSE] {request.prompt[:60]}...",
        )


@pytest.fixture
def services():

    model_service = ModelService()

    model_service.register_provider(
        ProviderDefinition(name="fake", description="fake explanation model"),
        _FakeExplanationAdapter(),
    )

    model_service.register_model(
        ModelDefinition(name="explanation_model", version="1.0.0", provider="fake")
    )

    tool_service = ToolService()

    workflow_service = WorkflowService()

    register_policy_advisor_workflow(
        workflow_service, tool_service, model_service, CATALOG_PATH
    )

    return workflow_service


def test_complete_info_reaches_recommendation_path(services) -> None:

    instance = services.execute(
        "policy_advisor",
        initial_variables={
            "vehicle_idv_rs": 400000,
            "vehicle_age_years": 3,
            "ncb_percent": 20,
            "coverage_priorities": ["zero_dep", "roadside_assistance", "ncb_protect"],
            "prefers_cashless": True,
        },
    )

    path = [result.node_id for result in instance.node_history]

    assert path == [
        "start",
        "ensure_session",
        "extract_and_merge_profile",
        "check_slots",
        "get_recommendations",
        "format_explanation",
        "end_recommend",
    ]

    assert instance.context.get_variable("response_text") is not None

    recommendations_result = instance.context.get_variable("recommendations_result")

    assert recommendations_result["recommendations"][0]["policy_id"] == (
        "INS_C_FAMILY_CAR_PLUS"
    )


def test_missing_info_reaches_clarifying_question_path(services) -> None:

    instance = services.execute(
        "policy_advisor",
        initial_variables={"vehicle_idv_rs": 400000},  # vehicle_age_years missing
    )

    path = [result.node_id for result in instance.node_history]

    assert path == [
        "start",
        "ensure_session",
        "extract_and_merge_profile",
        "check_slots",
        "ask_clarifying_question",
        "end_ask",
    ]
    assert instance.context.get_variable("response_text") is not None


def test_no_info_at_all_still_asks_clarifying_question(services) -> None:

    instance = services.execute("policy_advisor", initial_variables={})

    path = [result.node_id for result in instance.node_history]

    assert path[-1] == "end_ask"


def test_workflow_completes_successfully_in_both_branches(services) -> None:

    from enterprise_ai_platform.workflow_engine import ExecutionState

    complete = services.execute(
        "policy_advisor",
        initial_variables={"vehicle_idv_rs": 400000, "vehicle_age_years": 3},
    )

    incomplete = services.execute(
        "policy_advisor",
        initial_variables={"vehicle_idv_rs": 400000},
    )

    assert complete.state == ExecutionState.COMPLETED

    assert incomplete.state == ExecutionState.COMPLETED
