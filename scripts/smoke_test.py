"""
Smoke test suite — structural verification of a running deployment.

These tests check that the deployed application is correctly wired up:
endpoints respond, middleware runs, validation works, and the OpenAI-compatible
schema is intact. They do not test LLM output quality (that is eval_gates).

The --skip-inference flag skips the /chat inference call. Use it in CI
before running eval gates to verify the server is up without burning
API credits on a duplicate inference call.

EXIT CODES:
    0 = all checks passed
    1 = one or more checks failed (after retries)

USAGE:
    # Full suite (local development)
    python scripts/smoke_test.py --api-url http://localhost:8000

    # Structural checks only — no LLM call (CI pre-eval check)
    python scripts/smoke_test.py --api-url http://localhost:8000 --skip-inference

    # Against a remote deployment
    python scripts/smoke_test.py --api-url https://your-app.azurecontainerapps.io
"""

import argparse
import sys
import time
import uuid

import httpx


class SmokeTestError(Exception):
    """Raised when a smoke test assertion fails."""


def assert_equal(actual: object, expected: object, label: str) -> None:
    if actual != expected:
        raise SmokeTestError(f"{label}: expected {expected!r}, got {actual!r}")


def assert_true(condition: bool, label: str) -> None:
    if not condition:
        raise SmokeTestError(label)


def run_suite(api_url: str, skip_inference: bool) -> None:
    """Run all smoke tests. Raises SmokeTestError on first failure."""
    api_url = api_url.rstrip("/")

    with httpx.Client(timeout=30, follow_redirects=True) as client:
        # ── 1. Liveness probe ─────────────────────────────────────────────
        print("1. Liveness probe (/health) ...")
        resp = client.get(f"{api_url}/health")
        assert_equal(resp.status_code, 200, "/health status code")
        data = resp.json()
        assert_equal(data.get("status"), "healthy", "/health body.status")
        assert_true(bool(data.get("version")), "/health body.version is non-empty")
        assert_true(bool(data.get("environment")), "/health body.environment is non-empty")
        print(f"   ✓ status={data['status']}  version={data['version']}  env={data['environment']}")

        # ── 2. Readiness probe ────────────────────────────────────────────
        print("2. Readiness probe (/health/ready) ...")
        resp = client.get(f"{api_url}/health/ready")
        assert_equal(resp.status_code, 200, "/health/ready status code")
        data = resp.json()
        assert_equal(data.get("status"), "ready", "/health/ready body.status")
        checks = data.get("checks", {})
        for check_name, result in checks.items():
            assert_true(result is True, f"Readiness check '{check_name}' is True")
        print(f"   ✓ status=ready  checks={list(checks.keys())}")

        # ── 3. Client-provided Request ID echoed ──────────────────────────
        print("3. X-Request-ID propagation (client-provided) ...")
        custom_id = f"smoke-{uuid.uuid4().hex[:12]}"
        resp = client.get(f"{api_url}/health", headers={"x-request-id": custom_id})
        echoed = resp.headers.get("x-request-id", "")
        assert_equal(echoed, custom_id, "X-Request-ID echoed in response headers")
        print(f"   ✓ Client ID echoed: {custom_id}")

        # ── 4. Auto-generated Request ID when none provided ───────────────
        print("4. X-Request-ID auto-generation ...")
        resp = client.get(f"{api_url}/health")
        generated = resp.headers.get("x-request-id", "")
        assert_true(len(generated) > 0, "X-Request-ID auto-generated when not provided")
        print(f"   ✓ Auto-generated ID: {generated[:16]}...")

        # ── 5. Input validation — missing messages returns 422 ────────────
        print("5. Validation: missing messages → 422 ...")
        resp = client.post(f"{api_url}/chat", json={})
        assert_equal(resp.status_code, 422, "Missing messages returns 422")
        print("   ✓ 422 returned for empty body")

        # ── 6. Input validation — empty messages list returns 422 ─────────
        print("6. Validation: empty messages list → 422 ...")
        resp = client.post(f"{api_url}/chat", json={"messages": []})
        assert_equal(resp.status_code, 422, "Empty messages list returns 422")
        print("   ✓ 422 returned for empty messages list")

        # ── 7. Input validation — invalid role returns 422 ────────────────
        print("7. Validation: invalid message role → 422 ...")
        resp = client.post(
            f"{api_url}/chat",
            json={"messages": [{"role": "robot", "content": "Hello"}]},
        )
        assert_equal(resp.status_code, 422, "Invalid message role returns 422")
        print("   ✓ 422 returned for invalid role")

        # ── 8. Streaming not supported → 501 ─────────────────────────────
        print("8. Streaming: stream=true → 501 ...")
        resp = client.post(
            f"{api_url}/chat",
            json={"messages": [{"role": "user", "content": "Hi"}], "stream": True},
        )
        assert_equal(resp.status_code, 501, "stream=true returns 501")
        print("   ✓ 501 returned for streaming request")

        # ── 9. Chat inference (skippable) ─────────────────────────────────
        if skip_inference:
            print("9. Chat inference ... SKIPPED (--skip-inference)")
        else:
            print("9. Chat inference (/chat) ...")
            payload = {
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a helpful assistant. Reply very briefly.",
                    },
                    {"role": "user", "content": "Say the word SMOKE_OK and nothing else."},
                ],
                "max_tokens": 20,
                "temperature": 0.0,
            }
            resp = client.post(f"{api_url}/chat", json=payload, timeout=30)
            assert_equal(resp.status_code, 200, "/chat inference status code")
            data = resp.json()

            # Verify OpenAI-compatible schema
            for field in ("id", "object", "created", "model", "choices", "usage"):
                assert_true(field in data, f"Response contains field '{field}'")

            assert_equal(data["object"], "chat.completion", "response.object")
            assert_true(len(data["choices"]) > 0, "At least one choice returned")

            choice = data["choices"][0]
            content = choice.get("message", {}).get("content", "")
            assert_true(len(content) > 0, "Response content is non-empty")

            usage = data.get("usage", {})
            assert_true(usage.get("total_tokens", 0) > 0, "total_tokens > 0")

            # Verify X-Request-ID is in response headers for this call too
            assert_true(
                bool(resp.headers.get("x-request-id")), "X-Request-ID present on /chat response"
            )

            print(
                f"   ✓ OpenAI schema valid  "
                f"model={data['model']}  "
                f"tokens={usage.get('total_tokens')}  "
                f"content_len={len(content)}"
            )


def main() -> int:
    parser = argparse.ArgumentParser(description="Deployment smoke tests")
    parser.add_argument(
        "--api-url",
        required=True,
        help="Base URL of the deployed application",
    )
    parser.add_argument(
        "--skip-inference",
        action="store_true",
        help="Skip the /chat LLM inference test (structural checks only)",
    )
    parser.add_argument(
        "--retries",
        type=int,
        default=3,
        help="Number of retry attempts before declaring failure (default: 3)",
    )
    args = parser.parse_args()

    mode = "structural only (--skip-inference)" if args.skip_inference else "full suite"
    print(f"Smoke tests [{mode}]: {args.api_url}\n")

    for attempt in range(1, args.retries + 1):
        try:
            run_suite(args.api_url, args.skip_inference)
            print(f"\n{'─' * 50}")
            print("All smoke tests passed.")
            return 0

        except SmokeTestError as exc:
            print(f"\n✗ SMOKE TEST FAILED (attempt {attempt}/{args.retries}): {exc}")
            if attempt < args.retries:
                print("  Retrying in 10 seconds...")
                time.sleep(10)

        except httpx.ConnectError as exc:
            print(f"\n✗ CONNECTION ERROR (attempt {attempt}/{args.retries}): {exc}")
            if attempt < args.retries:
                print("  Retrying in 10 seconds...")
                time.sleep(10)

    print("\nAll retry attempts exhausted. Smoke tests failed.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
