"""Tests for the token cost calculator."""

import pytest

from app.observability.cost_calculator import (
    CostBreakdown,
    _normalize_model_name,
    calculate_cost,
)


class TestCalculateCost:
    def test_gpt4o_mini_exact_pricing(self):
        # At 1M tokens: $0.150 input + $0.600 output = $0.750 total
        cost = calculate_cost("gpt-4o-mini", prompt_tokens=1_000_000, completion_tokens=1_000_000)
        assert cost.prompt_cost_usd == pytest.approx(0.150, rel=1e-5)
        assert cost.completion_cost_usd == pytest.approx(0.600, rel=1e-5)
        assert cost.total_cost_usd == pytest.approx(0.750, rel=1e-5)

    def test_unknown_model_returns_zero_cost(self):
        cost = calculate_cost("completely-unknown-model-xyz", 1000, 500)
        assert cost.prompt_cost_usd == 0.0
        assert cost.completion_cost_usd == 0.0
        assert cost.total_cost_usd == 0.0

    def test_returns_correct_token_counts(self):
        cost = calculate_cost("gpt-4o", 50, 30)
        assert cost.prompt_tokens == 50
        assert cost.completion_tokens == 30
        assert cost.total_tokens == 80

    def test_returns_cost_breakdown_type(self):
        cost = calculate_cost("gpt-4o-mini", 100, 50)
        assert isinstance(cost, CostBreakdown)

    def test_cost_breakdown_is_immutable(self):
        cost = calculate_cost("gpt-4o-mini", 100, 50)
        with pytest.raises((AttributeError, TypeError)):
            cost.total_cost_usd = 999.0  # frozen=True should prevent this

    def test_small_token_count_is_non_zero_for_known_model(self):
        cost = calculate_cost("gpt-4o-mini", 1, 1)
        assert cost.total_cost_usd > 0.0

    def test_as_log_dict_contains_expected_keys(self):
        cost = calculate_cost("gpt-4o-mini", 10, 20)
        log_dict = cost.as_log_dict()
        for key in ["prompt_tokens", "completion_tokens", "total_tokens", "total_cost_usd"]:
            assert key in log_dict


class TestNormalizeModelName:
    def test_exact_match_returned_as_is(self):
        assert _normalize_model_name("gpt-4o-mini") == "gpt-4o-mini"

    def test_azure_deployment_name_normalized(self):
        # Azure deployment names often embed the model name
        result = _normalize_model_name("prod-gpt4omini-eastus")
        assert result == "gpt-4o-mini"

    def test_completely_unknown_name_returned_unchanged(self):
        result = _normalize_model_name("my-custom-local-model")
        assert result == "my-custom-local-model"