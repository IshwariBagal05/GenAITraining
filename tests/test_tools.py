from app.tools import call_tool


def test_free_look_calculator_tool_returns_estimate():
    result = call_tool(
        "free_look_calculator",
        {
            "received_date": "2026-01-01",
            "sold_via": "electronic",
            "premium": 2000,
            "medical_exam_cost": 100,
            "stamp_duty": 50,
            "proportionate_risk_premium": 100,
        },
    )

    assert result["ok"] is True
    assert result["result"]["last_date"] == "2026-01-31"
    assert result["result"]["estimated_refund"] == 1750


def test_tool_rejects_unknown_name_and_invalid_arguments():
    unknown = call_tool("missing_tool", {})
    invalid = call_tool("free_look_calculator", {"premium": -1})

    assert unknown["ok"] is False
    assert "Unknown tool" in unknown["error"]
    assert invalid["ok"] is False
    assert "received_date" in invalid["error"]
