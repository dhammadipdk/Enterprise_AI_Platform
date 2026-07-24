import pytest

from enterprise_ai_platform.tool_engine import (
    BaseToolAdapter,
    ToolCategory,
    ToolDefinition,
    ToolPermission,
    ToolResponse,
    ToolService,
)


class _FakePolicyLookupAdapter(BaseToolAdapter):
    """
    Deterministic fake adapter -- no real database, no network.
    """

    def execute(self, request, tool):

        policy_id = request.parameters.get("policy_id")

        return ToolResponse(
            request_id=request.request_id,
            status="success",
            result={"policy_id": policy_id, "status": "active"},
        )


class _AlwaysRaisesAdapter(BaseToolAdapter):

    def execute(self, request, tool):

        raise RuntimeError("simulated database connection failure")


_INPUT_SCHEMA = {
    "type": "object",
    "properties": {"policy_id": {"type": "string"}},
    "required": ["policy_id"],
}


def _register_basic_tool(
    service: ToolService,
    permissions: list[ToolPermission] | None = None,
    input_schema: dict | None = None,
    adapter: BaseToolAdapter | None = None,
) -> None:

    service.register_tool(
        ToolDefinition(
            name="check_policy_status",
            version="1.0.0",
            category=ToolCategory.DATABASE,
            input_schema=input_schema,
            permissions=permissions or [],
        ),
        adapter or _FakePolicyLookupAdapter(),
    )


def test_register_and_get_tool() -> None:

    service = ToolService()

    _register_basic_tool(service)

    assert service.tool_exists("check_policy_status")

    tool = service.get_tool("check_policy_status")

    assert tool.category == ToolCategory.DATABASE


def test_get_tool_missing_raises_key_error() -> None:

    service = ToolService()

    with pytest.raises(KeyError):
        service.get_tool("does_not_exist")


def test_get_tool_default_returns_latest_version() -> None:

    service = ToolService()

    service.register_tool(
        ToolDefinition(name="check_policy_status", version="1.0.0"),
        _FakePolicyLookupAdapter(),
    )

    service.register_tool(
        ToolDefinition(name="check_policy_status", version="2.0.0"),
        _FakePolicyLookupAdapter(),
    )

    tool = service.get_tool("check_policy_status")

    assert tool.version == "2.0.0"


def test_get_tool_latest_uses_numeric_not_string_comparison() -> None:

    service = ToolService()

    service.register_tool(
        ToolDefinition(name="check_policy_status", version="1.9.0"),
        _FakePolicyLookupAdapter(),
    )

    service.register_tool(
        ToolDefinition(name="check_policy_status", version="1.10.0"),
        _FakePolicyLookupAdapter(),
    )

    tool = service.get_tool("check_policy_status")

    assert tool.version == "1.10.0"


def test_list_tools_filtered_by_category() -> None:

    service = ToolService()

    service.register_tool(
        ToolDefinition(
            name="check_policy_status", version="1.0.0", category=ToolCategory.DATABASE
        ),
        _FakePolicyLookupAdapter(),
    )

    service.register_tool(
        ToolDefinition(
            name="send_renewal_email", version="1.0.0", category=ToolCategory.EMAIL
        ),
        _FakePolicyLookupAdapter(),
    )

    assert service.list_tools(category=ToolCategory.EMAIL) == [
        "send_renewal_email"
    ]

    assert service.list_tools(category=ToolCategory.DATABASE) == [
        "check_policy_status"
    ]


def test_execute_success() -> None:

    service = ToolService()

    _register_basic_tool(service)

    response = service.execute(
        "check_policy_status", parameters={"policy_id": "POL123"}
    )

    assert response.status == "success"

    assert response.result == {"policy_id": "POL123", "status": "active"}

    assert response.execution_time_seconds is not None


def test_execute_missing_tool_raises_key_error() -> None:

    service = ToolService()

    with pytest.raises(KeyError):
        service.execute("does_not_exist")


def test_disable_prevents_execution() -> None:

    service = ToolService()

    _register_basic_tool(service)

    service.disable("check_policy_status")

    with pytest.raises(RuntimeError, match="disabled"):
        service.execute("check_policy_status", parameters={"policy_id": "POL123"})


def test_enable_restores_execution() -> None:

    service = ToolService()

    _register_basic_tool(service)

    service.disable("check_policy_status")

    service.enable("check_policy_status")

    response = service.execute(
        "check_policy_status", parameters={"policy_id": "POL123"}
    )

    assert response.status == "success"


def test_is_enabled_reflects_state() -> None:

    service = ToolService()

    _register_basic_tool(service)

    assert service.is_enabled("check_policy_status")

    service.disable("check_policy_status")

    assert not service.is_enabled("check_policy_status")


def test_execute_missing_permission_raises() -> None:

    service = ToolService()

    _register_basic_tool(
        service, permissions=[ToolPermission(name="read_customer_data")]
    )

    with pytest.raises(PermissionError, match="read_customer_data"):
        service.execute(
            "check_policy_status",
            parameters={"policy_id": "POL123"},
            granted_permissions=set(),
        )


def test_execute_with_granted_permission_succeeds() -> None:

    service = ToolService()

    _register_basic_tool(
        service, permissions=[ToolPermission(name="read_customer_data")]
    )

    response = service.execute(
        "check_policy_status",
        parameters={"policy_id": "POL123"},
        granted_permissions={"read_customer_data"},
    )

    assert response.status == "success"


def test_execute_invalid_parameters_raises_value_error() -> None:

    service = ToolService()

    _register_basic_tool(service, input_schema=_INPUT_SCHEMA)

    with pytest.raises(ValueError, match="policy_id"):
        service.execute("check_policy_status", parameters={})


def test_validate_returns_report_without_executing() -> None:

    service = ToolService()

    _register_basic_tool(service, input_schema=_INPUT_SCHEMA)

    report = service.validate("check_policy_status", {})

    assert not report.is_valid

    report_valid = service.validate(
        "check_policy_status", {"policy_id": "POL123"}
    )

    assert report_valid.is_valid


def test_execute_catches_adapter_exception_as_failure_response() -> None:

    service = ToolService()

    _register_basic_tool(service, adapter=_AlwaysRaisesAdapter())

    response = service.execute(
        "check_policy_status", parameters={"policy_id": "POL123"}
    )

    assert response.status == "failure"

    assert "simulated database connection failure" in response.error

    assert response.execution_time_seconds is not None


def test_health_reflects_registration_and_enabled_state() -> None:

    service = ToolService()

    assert not service.health("check_policy_status")

    _register_basic_tool(service)

    assert service.health("check_policy_status")

    service.disable("check_policy_status")

    assert not service.health("check_policy_status")


def test_lifecycle_transitions() -> None:

    service = ToolService()

    service.initialize()

    service.start()

    assert service.is_running

    service.stop()

    service.dispose()


def test_dispose_clears_tools_adapters_and_disabled_state() -> None:

    service = ToolService()

    _register_basic_tool(service)

    service.disable("check_policy_status")

    service.initialize()

    service.start()

    service.stop()

    service.dispose()

    assert not service.tool_exists("check_policy_status")