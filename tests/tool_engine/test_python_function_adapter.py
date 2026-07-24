import pytest

from enterprise_ai_platform.tool_engine import (
    ToolDefinition,
    ToolRequest,
)
from enterprise_ai_platform.tool_engine.adapters import PythonFunctionAdapter


def _calculate_premium(vehicle_age: int, idv: float, ncb_percent: float = 0) -> dict:
    """
    A real, if simplified, business function -- exactly the kind of
    thing PythonFunctionAdapter is meant to wrap directly.
    """

    base_rate = 0.03

    premium = idv * base_rate

    discount = premium * (ncb_percent / 100)

    return {"premium": round(premium - discount, 2)}


def _tool():

    return ToolDefinition(name="calculate_premium", version="1.0.0")


def test_execute_calls_function_with_parameters_as_kwargs() -> None:

    adapter = PythonFunctionAdapter(_calculate_premium)

    request = ToolRequest(
        tool_name="calculate_premium",
        parameters={"vehicle_age": 3, "idv": 400000, "ncb_percent": 20},
    )

    response = adapter.execute(request, _tool())

    assert response.status == "success"

    assert response.result == {"premium": 9600.0}

    assert response.request_id == request.request_id


def test_execute_uses_default_parameter_values() -> None:

    adapter = PythonFunctionAdapter(_calculate_premium)

    request = ToolRequest(
        tool_name="calculate_premium",
        parameters={"vehicle_age": 5, "idv": 200000},
    )

    response = adapter.execute(request, _tool())

    assert response.result == {"premium": 6000.0}


def test_missing_required_parameter_raises_type_error() -> None:

    adapter = PythonFunctionAdapter(_calculate_premium)

    request = ToolRequest(tool_name="calculate_premium", parameters={})

    with pytest.raises(TypeError):
        adapter.execute(request, _tool())


def test_wraps_a_lambda_just_as_well() -> None:

    adapter = PythonFunctionAdapter(lambda x, y: x + y)

    request = ToolRequest(tool_name="add", parameters={"x": 2, "y": 3})

    response = adapter.execute(request, ToolDefinition(name="add", version="1.0.0"))

    assert response.result == 5