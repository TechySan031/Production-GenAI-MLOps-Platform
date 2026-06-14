"""
AI Evaluation Gate.

Sends each test case in eval_dataset.json to the running gateway,
scores responses using an LLM-as-judge, and compares the aggregate
score to the stored baseline.

EXIT CODES:
    0 = passed — score is within acceptable range of baseline
    1 = regression detected — score dropped below threshold, deploy blocked
    2 = infrastructure error — gateway unreachable, judge unavailable, etc.

JUDGE CONFIGURATION:
    The judge defaults to Groq (same free tier as the gateway).
    Override via environment variables for different setups:

        JUDGE_API_KEY   — defaults to GROQ_API_KEY
        JUDGE_BASE_URL  — defaults to https://api.groq.com/openai/v1
        JUDGE_MODEL     — defaults to llama-3.3-70b-versatile

    Using a larger model as the judge than the gateway is intentional —
    the judge needs better reasoning to score the gateway's responses fairly.

USAGE:
    # Standard run (used in CI)
    python scripts/eval/run_evals.py --api-url http://localhost:8000

    # Update baseline after a confirmed quality improvement
    python scripts/eval/run_evals.py --api-url http://localhost:8000 --update-baseline

    # Verbose output (shows full response content)
    python scripts/eval/run_evals.py --api-url http://localhost:8000 --verbose
"""

import argparse
import json
import os
import sys
import time
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import httpx
import openai

# ── Paths ────────────────────────────────────────────────────────────────────

EVAL_DIR = Path(__file__).parent
DATASET_PATH = EVAL_DIR / "eval_dataset.json"
BASELINE_PATH = EVAL_DIR / "baseline_score.json"
RESULTS_OUTPUT_PATH = Path("eval_results.json")

# ── Judge configuration ───────────────────────────────────────────────────────

_GROQ_BASE_URL = "https://api.groq.com/openai/v1"

JUDGE_API_KEY = os.environ.get("JUDGE_API_KEY") or os.environ.get("GROQ_API_KEY", "")
JUDGE_BASE_URL = os.environ.get("JUDGE_BASE_URL", _GROQ_BASE_URL)
JUDGE_MODEL = os.environ.get("JUDGE_MODEL", "llama-3.3-70b-versatile")

# ── Constants ─────────────────────────────────────────────────────────────────

GATEWAY_TIMEOUT_S = 30
JUDGE_MAX_RETRIES = 2
JUDGE_RETRY_DELAY_S = 2

# ── Prompt templates (inlined to avoid cross-script import complexity) ─────────

JUDGE_SYSTEM_PROMPT = """You are an objective AI response evaluator.

Your task is to rate an AI assistant's response against a given criteria.

SCORING SCALE:
1 = Response completely fails to meet the criteria
2 = Response partially meets criteria but has significant problems
3 = Response mostly meets criteria with minor issues
4 = Response fully meets criteria
5 = Response meets criteria and goes beyond what was required

OUTPUT FORMAT: You must respond with valid JSON only. No explanation outside the JSON.
Use exactly this structure: {"score": <integer 1-5>, "reason": "<one sentence>"}

Rules:
- Score based ONLY on whether the criteria are met, not writing style
- Do not reward verbosity — brief accurate answers score the same as verbose ones
- Never output anything outside the JSON object"""

JUDGE_USER_TEMPLATE = """Rate this AI assistant response against the provided criteria.

CRITERIA: {criteria}

USER'S QUESTION: {user_input}

ASSISTANT'S RESPONSE:
{response}

Respond with JSON only.

Example:
{{"score": 4, "reason": "Response correctly addressed the criteria."}}
"""

# ── Data classes ──────────────────────────────────────────────────────────────


@dataclass
class EvalResult:
    test_id: str
    category: str
    score: int  # 1–5
    reason: str
    passed: bool  # score >= test_case["min_score"]
    latency_ms: float
    response_preview: str  # first 120 chars of gateway response
    error: str | None = None  # set if gateway or judge errored


@dataclass
class EvalSummary:
    total_cases: int
    passed: int
    failed: int
    average_score: float
    min_score: int
    max_score: int
    avg_latency_ms: float
    category_scores: dict[str, float]


# ── Data loading ──────────────────────────────────────────────────────────────


def load_dataset() -> list[dict[str, Any]]:
    with open(DATASET_PATH) as f:
        return json.load(f)


def load_baseline() -> dict[str, Any]:
    with open(BASELINE_PATH) as f:
        data = json.load(f)
    # Strip comment key if present
    data.pop("_comment", None)
    return data


# ── Gateway interaction ───────────────────────────────────────────────────────


def call_gateway(
    api_url: str,
    messages: list[dict[str, str]],
) -> tuple[str, float]:
    """
    Send a chat request to the gateway.

    Returns (response_content, latency_ms).
    Raises httpx.HTTPError on HTTP failures.
    """
    start = time.monotonic()
    response = httpx.post(
        f"{api_url}/chat",
        json={"messages": messages},
        timeout=GATEWAY_TIMEOUT_S,
    )
    latency_ms = (time.monotonic() - start) * 1000
    response.raise_for_status()
    content = response.json()["choices"][0]["message"]["content"]
    return content, round(latency_ms, 2)


# ── Judge interaction ─────────────────────────────────────────────────────────


def _build_judge_client() -> openai.OpenAI:
    return openai.OpenAI(
        api_key=JUDGE_API_KEY,
        base_url=JUDGE_BASE_URL,
    )


def judge_response(
    client: openai.OpenAI,
    user_input: str,
    response_content: str,
    eval_criteria: str,
) -> tuple[int, str]:
    """
    Score a gateway response using LLM-as-judge.

    Returns (score 1–5, one-sentence reason).
    On judge failure, returns (1, error_description) so the eval continues.
    """
    user_message = JUDGE_USER_TEMPLATE.format(
        criteria=eval_criteria,
        user_input=user_input,
        response=response_content,
    )

    for attempt in range(JUDGE_MAX_RETRIES + 1):
        try:
            completion = client.chat.completions.create(
                model=JUDGE_MODEL,
                messages=[
                    {"role": "system", "content": JUDGE_SYSTEM_PROMPT},
                    {"role": "user", "content": user_message},
                ],
                max_tokens=200,
                temperature=0.0,  # deterministic scoring
            )
            raw = completion.choices[0].message.content or ""

            # Strip markdown fences if the model wrapped its JSON
            raw = raw.strip()
            if raw.startswith("```"):
                lines = raw.split("\n")
                raw = "\n".join(
                    line for line in lines if not line.strip().startswith("```")
                ).strip()

            parsed = json.loads(raw)
            score = int(parsed.get("score", 1))
            reason = str(parsed.get("reason", "No reason provided"))
            return max(1, min(5, score)), reason

        except (json.JSONDecodeError, KeyError, ValueError, TypeError) as exc:
            if attempt < JUDGE_MAX_RETRIES:
                time.sleep(JUDGE_RETRY_DELAY_S)
                continue
            return 1, f"Judge parse error after {JUDGE_MAX_RETRIES + 1} attempts: {exc}"

        except openai.OpenAIError as exc:
            if attempt < JUDGE_MAX_RETRIES:
                time.sleep(JUDGE_RETRY_DELAY_S)
                continue
            return 1, f"Judge API error: {exc}"

    return 1, "Judge failed after all retries"


# ── Core evaluation logic ─────────────────────────────────────────────────────


def run_single_case(
    api_url: str,
    test_case: dict[str, Any],
    judge_client: openai.OpenAI,
    verbose: bool = False,
) -> EvalResult:
    """Run one eval case end-to-end and return its result."""
    test_id = test_case["id"]
    category = test_case["category"]
    messages = test_case["input"]
    criteria = test_case["eval_criteria"]
    min_score = test_case.get("min_score", 3)

    description = test_case.get("description", test_id)
    print(f"  [{test_id}] {description[:65]}...")

    # ── Step 1: Call the gateway ──────────────────────────────────────────
    try:
        response_content, latency_ms = call_gateway(api_url, messages)
    except httpx.HTTPStatusError as exc:
        error_msg = f"Gateway HTTP {exc.response.status_code}"
        print(f"    ✗ {error_msg}")
        return EvalResult(
            test_id=test_id,
            category=category,
            score=1,
            reason=error_msg,
            passed=False,
            latency_ms=0.0,
            response_preview="",
            error=error_msg,
        )
    except httpx.RequestError as exc:
        error_msg = f"Gateway unreachable: {exc}"
        print(f"    ✗ {error_msg}")
        return EvalResult(
            test_id=test_id,
            category=category,
            score=1,
            reason=error_msg,
            passed=False,
            latency_ms=0.0,
            response_preview="",
            error=error_msg,
        )

    # ── Step 2: Judge the response ────────────────────────────────────────
    # Extract the last user message as the question for the judge
    user_input = next(
        (m["content"] for m in reversed(messages) if m["role"] == "user"),
        str(messages),
    )

    score, reason = judge_response(judge_client, user_input, response_content, criteria)
    passed = score >= min_score

    status_icon = "✓" if passed else "✗"
    print(f"    {status_icon} Score {score}/5 (min {min_score}) — {reason}")

    if verbose:
        preview = response_content[:120].replace("\n", " ")
        print(f"      Response: {preview}{'...' if len(response_content) > 120 else ''}")

    return EvalResult(
        test_id=test_id,
        category=category,
        score=score,
        reason=reason,
        passed=passed,
        latency_ms=latency_ms,
        response_preview=response_content[:120],
    )


def compute_summary(results: list[EvalResult]) -> EvalSummary:
    scores = [r.score for r in results]
    latencies = [r.latency_ms for r in results]

    by_category: dict[str, list[int]] = {}
    for r in results:
        by_category.setdefault(r.category, []).append(r.score)

    return EvalSummary(
        total_cases=len(results),
        passed=sum(1 for r in results if r.passed),
        failed=sum(1 for r in results if not r.passed),
        average_score=round(sum(scores) / len(scores), 3) if scores else 0.0,
        min_score=min(scores) if scores else 0,
        max_score=max(scores) if scores else 0,
        avg_latency_ms=round(sum(latencies) / len(latencies), 2) if latencies else 0.0,
        category_scores={cat: round(sum(s) / len(s), 3) for cat, s in by_category.items()},
    )


# ── Regression check ──────────────────────────────────────────────────────────


def check_regression(
    current_avg: float,
    baseline: dict[str, Any],
) -> tuple[bool, str]:
    """
    Compare current score to baseline.

    Returns (passed: bool, message: str).
    Fails if the relative drop exceeds regression_threshold.
    """
    baseline_score: float = baseline["baseline_score"]
    threshold: float = baseline.get("regression_threshold", 0.10)

    if baseline_score == 0:
        return True, "Baseline is zero — skipping regression check"

    relative_drop = (baseline_score - current_avg) / baseline_score

    if relative_drop > threshold:
        return False, (
            f"REGRESSION: {current_avg:.3f} vs baseline {baseline_score:.3f} "
            f"({relative_drop:.1%} drop > {threshold:.1%} allowed)"
        )

    improvement = current_avg - baseline_score
    sign = "+" if improvement >= 0 else ""
    return True, (
        f"Quality OK: {current_avg:.3f} vs baseline {baseline_score:.3f} "
        f"({sign}{improvement:.3f}, within {threshold:.1%} threshold)"
    )


# ── Baseline management ───────────────────────────────────────────────────────


def update_baseline(
    summary: EvalSummary,
    baseline: dict[str, Any],
    git_sha: str,
) -> None:
    """Write current scores as the new baseline. Preserves threshold."""
    new_baseline = {
        "baseline_score": summary.average_score,
        "baseline_date": datetime.now(UTC).strftime("%Y-%m-%d"),
        "baseline_git_sha": git_sha,
        "regression_threshold": baseline.get("regression_threshold", 0.10),
        "category_scores": summary.category_scores,
    }
    with open(BASELINE_PATH, "w") as f:
        json.dump(new_baseline, f, indent=2)
    print(f"\nBaseline updated to {summary.average_score:.3f} → {BASELINE_PATH}")
    print("Commit this file to make the new baseline effective.")


# ── Pre-flight checks ─────────────────────────────────────────────────────────


def verify_gateway(api_url: str) -> bool:
    """Return True if the gateway health endpoint is reachable."""
    try:
        response = httpx.get(f"{api_url}/health", timeout=10)
        return response.status_code == 200
    except httpx.RequestError:
        return False


def verify_judge_api() -> bool:
    """Return True if the judge API (Groq or configured endpoint) is reachable."""
    if not JUDGE_API_KEY:
        return False
    try:
        client = _build_judge_client()
        # Use models.list() — zero tokens, just a connectivity check
        client.models.list()
        return True
    except Exception:
        return False


# ── Entry point ───────────────────────────────────────────────────────────────


def main() -> int:
    parser = argparse.ArgumentParser(
        description="AI evaluation gate — blocks deployment on quality regression"
    )
    parser.add_argument(
        "--api-url",
        default="http://localhost:8000",
        help="Base URL of the running gateway (default: http://localhost:8000)",
    )
    parser.add_argument(
        "--update-baseline",
        action="store_true",
        help="Write current scores as the new baseline instead of checking regression",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show first 120 characters of each gateway response",
    )
    parser.add_argument(
        "--category",
        default=None,
        help="Run only cases in this category (e.g. basic_inference)",
    )
    args = parser.parse_args()

    # ── Pre-flight ────────────────────────────────────────────────────────
    print(f"Gateway: {args.api_url}")
    print(f"Judge:   {JUDGE_BASE_URL} / {JUDGE_MODEL}")
    print()

    if not verify_gateway(args.api_url):
        print(f"ERROR: Gateway not reachable at {args.api_url}/health")
        print("Start the server first: make run")
        return 2

    if not JUDGE_API_KEY:
        print("ERROR: No judge API key found.")
        print("Set JUDGE_API_KEY or GROQ_API_KEY in your environment.")
        return 2

    if not verify_judge_api():
        print(f"ERROR: Judge API not reachable at {JUDGE_BASE_URL}")
        print("Check JUDGE_API_KEY / GROQ_API_KEY and JUDGE_BASE_URL.")
        return 2

    print("Pre-flight checks passed.\n")

    # ── Load data ─────────────────────────────────────────────────────────
    dataset = load_dataset()
    baseline = load_baseline()
    judge_client = _build_judge_client()

    if args.category:
        dataset = [c for c in dataset if c["category"] == args.category]
        if not dataset:
            print(f"No cases found for category: {args.category}")
            return 2

    # ── Run evaluations ───────────────────────────────────────────────────
    print(f"Running {len(dataset)} evaluation cases...\n")
    print("─" * 70)

    results: list[EvalResult] = []
    for test_case in dataset:
        result = run_single_case(args.api_url, test_case, judge_client, args.verbose)
        results.append(result)

    print("─" * 70)

    # ── Summary ───────────────────────────────────────────────────────────
    summary = compute_summary(results)

    print(f"\nResults:          {summary.passed}/{summary.total_cases} cases passed")
    print(f"Average score:    {summary.average_score:.3f} / 5.000")
    print(f"Score range:      {summary.min_score} – {summary.max_score}")
    print(f"Average latency:  {summary.avg_latency_ms:.1f} ms")
    print("\nBy category:")
    for cat, score in sorted(summary.category_scores.items()):
        baseline_cat = baseline.get("category_scores", {}).get(cat, "N/A")
        baseline_str = (
            f"baseline: {baseline_cat:.3f}" if isinstance(baseline_cat, float) else "no baseline"
        )
        print(f"  {cat:<26} {score:.3f}  ({baseline_str})")

    # ── Write results artifact ────────────────────────────────────────────
    output = {
        "git_sha": os.environ.get("GITHUB_SHA", "local"),
        "timestamp": datetime.now(UTC).isoformat(),
        "api_url": args.api_url,
        "judge_model": JUDGE_MODEL,
        "judge_base_url": JUDGE_BASE_URL,
        "summary": asdict(summary),
        "baseline": baseline,
        "results": [asdict(r) for r in results],
    }
    with open(RESULTS_OUTPUT_PATH, "w") as f:
        json.dump(output, f, indent=2)
    print(f"\nResults written to {RESULTS_OUTPUT_PATH}")

    # ── Update baseline or check regression ───────────────────────────────
    if args.update_baseline:
        update_baseline(summary, baseline, os.environ.get("GITHUB_SHA", "manual"))
        return 0

    passed, message = check_regression(summary.average_score, baseline)
    print(f"\n{'PASS' if passed else 'FAIL'}: {message}")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
