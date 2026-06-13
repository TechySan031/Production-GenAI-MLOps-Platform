"""
Token cost calculator for LLM provider calls.

Prices are USD per 1 million tokens (the industry standard unit).
Last updated: June 2025.

Sources:
    OpenAI:       https://openai.com/pricing
    Azure OpenAI: https://azure.microsoft.com/pricing/details/cognitive-services/openai-service/

Azure note: Azure OpenAI returns deployment names in response.model, not base model
names. Example: "my-gpt4o-prod" instead of "gpt-4o". The _normalize_model_name()
function handles this via substring matching so costs are correctly attributed.
"""

from dataclasses import asdict, dataclass

# (input_per_1m_usd, output_per_1m_usd)
MODEL_PRICING: dict[str, tuple[float, float]] = {
    # GPT-4o family
    "gpt-4o": (2.50, 10.00),
    "gpt-4o-mini": (0.150, 0.600),
    # GPT-4 Turbo
    "gpt-4-turbo": (10.00, 30.00),
    "gpt-4-turbo-preview": (10.00, 30.00),
    # GPT-3.5
    "gpt-3.5-turbo": (0.50, 1.50),
    "gpt-3.5-turbo-0125": (0.50, 1.50),
    # o1 family
    "o1-preview": (15.00, 60.00),
    "o1-mini": (3.00, 12.00),
    # o3 family
    "o3-mini": (1.10, 4.40),
    # Groq-hosted models (pricing per 1M tokens, paid tier)
    "llama-3.1-8b-instant": (0.05, 0.08),
    "llama-3.3-70b-versatile": (0.59, 0.79),
    "llama3-8b-8192": (0.05, 0.08),
    "llama3-70b-8192": (0.59, 0.79),
    "mixtral-8x7b-32768": (0.24, 0.24),
    "gemma2-9b-it": (0.20, 0.20),
    "gemma-7b-it": (0.07, 0.07),
}


@dataclass(frozen=True)
class CostBreakdown:
    """Immutable cost breakdown for a single LLM inference call."""

    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    prompt_cost_usd: float
    completion_cost_usd: float
    total_cost_usd: float

    def as_log_dict(self) -> dict:
        """Return flat dict for structured logging (Azure Monitor compatible)."""
        return {f"cost_{k}" if k == "model" else k: v for k, v in asdict(self).items()}


def calculate_cost(
    model: str,
    prompt_tokens: int,
    completion_tokens: int,
) -> CostBreakdown:
    """
    Calculate USD cost for one LLM inference call.

    Returns CostBreakdown with all-zero costs if model is not in the pricing
    table. This happens for unknown Azure deployment names — add them to
    MODEL_PRICING or rely on the substring normalization below.
    """
    normalized = _normalize_model_name(model)
    input_price, output_price = MODEL_PRICING.get(normalized, (0.0, 0.0))

    prompt_cost = (prompt_tokens / 1_000_000) * input_price
    completion_cost = (completion_tokens / 1_000_000) * output_price

    return CostBreakdown(
        model=normalized,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=prompt_tokens + completion_tokens,
        prompt_cost_usd=round(prompt_cost, 8),
        completion_cost_usd=round(completion_cost, 8),
        total_cost_usd=round(prompt_cost + completion_cost, 8),
    )


def _normalize_model_name(model: str) -> str:
    """
    Normalize model identifier to a known pricing key.

    Azure deployment names embed model info but don't match exactly.
    We try exact match first, then strip hyphens and do substring match.

    Examples:
        "gpt-4o-mini"             → "gpt-4o-mini"  (exact)
        "my-prod-gpt4omini-dep"   → "gpt-4o-mini"  (substring after strip)
        "totally-unknown"         → "totally-unknown" (no match, cost = 0)
    """
    if model in MODEL_PRICING:
        return model

    # Normalize: lowercase, remove hyphens for fuzzy comparison
    model_stripped = model.lower().replace("-", "").replace("_", "")
    for known_model in sorted(
        MODEL_PRICING.keys(),
        key=len,
        reverse=True,
    ):
        known_stripped = known_model.lower().replace("-", "")
        if known_stripped in model_stripped:
            return known_model

    return model
