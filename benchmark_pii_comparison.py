#!/usr/bin/env python3
"""
PII Detection Performance Comparison
Compares:
1. No protection (baseline)
2. Simple PII Guardrail (Bedrock native)
3. Python regex-based PII detection (application level)
"""

import boto3
import json
import re
import time
import statistics
from dataclasses import dataclass
from typing import Optional


# Configuration
REGION = "us-east-1"
MODEL_ID = "amazon.nova-pro-v1:0"
SIMPLE_PII_GUARDRAIL_ID = "beraeckuf5js"
SIMPLE_PII_GUARDRAIL_VERSION = "1"


# Python regex patterns for PII detection (same as guardrail)
PII_PATTERNS = {
    "email": re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"),
    "phone": re.compile(r"(\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}"),
    "ssn": re.compile(r"\b\d{3}[-.\s]?\d{2}[-.\s]?\d{4}\b"),
    "credit_card": re.compile(r"\b(?:\d{4}[-.\s]?){3}\d{4}\b"),
}


# Test prompts with varying PII content
TEST_PROMPTS = [
    # No PII
    "What is the capital of France?",
    "Explain quantum computing in simple terms.",
    "What are best practices for code review?",
    # Contains email
    "My email is john.doe@example.com, can you help me write a professional bio?",
    "Contact support at help@company.org for assistance.",
    # Contains phone
    "Call me at 555-123-4567 to discuss the project.",
    "My office number is (800) 555-0199.",
    # Contains multiple PII
    "Send the report to alice@corp.com or call 555-987-6543.",
    "Reach out to bob@test.io at +1-555-000-1111 for details.",
    # Edge cases
    "The IP address 192.168.1.1 is not a phone number.",
]


@dataclass
class BenchmarkResult:
    prompt: str
    method: str
    latency_ms: float
    pii_check_ms: float
    total_ms: float
    pii_found: list[str]
    blocked: bool
    error: Optional[str]


def create_bedrock_client():
    return boto3.client("bedrock-runtime", region_name=REGION)


def detect_pii_regex(text: str) -> tuple[list[str], float]:
    """
    Detect PII using Python regex patterns.
    Returns list of PII types found and time taken.
    """
    start = time.perf_counter()
    found = []

    for pii_type, pattern in PII_PATTERNS.items():
        if pattern.search(text):
            found.append(pii_type)

    elapsed_ms = (time.perf_counter() - start) * 1000
    return found, elapsed_ms


def anonymize_pii_regex(text: str) -> str:
    """Anonymize PII in text using regex replacement."""
    result = text
    result = PII_PATTERNS["email"].sub("[EMAIL]", result)
    result = PII_PATTERNS["phone"].sub("[PHONE]", result)
    result = PII_PATTERNS["ssn"].sub("[SSN]", result)
    result = PII_PATTERNS["credit_card"].sub("[CARD]", result)
    return result


def invoke_no_protection(client, prompt: str) -> BenchmarkResult:
    """Baseline: No PII protection."""
    request_body = {
        "messages": [{"role": "user", "content": [{"text": prompt}]}],
        "inferenceConfig": {"maxTokens": 256, "temperature": 0.7}
    }

    start = time.perf_counter()
    try:
        response = client.invoke_model(
            modelId=MODEL_ID,
            body=json.dumps(request_body),
            contentType="application/json",
            accept="application/json"
        )
        response_body = json.loads(response["body"].read())
        latency = (time.perf_counter() - start) * 1000

        return BenchmarkResult(
            prompt=prompt[:50] + "..." if len(prompt) > 50 else prompt,
            method="no_protection",
            latency_ms=latency,
            pii_check_ms=0,
            total_ms=latency,
            pii_found=[],
            blocked=False,
            error=None
        )
    except Exception as e:
        latency = (time.perf_counter() - start) * 1000
        return BenchmarkResult(
            prompt=prompt[:50] + "..." if len(prompt) > 50 else prompt,
            method="no_protection",
            latency_ms=latency,
            pii_check_ms=0,
            total_ms=latency,
            pii_found=[],
            blocked=False,
            error=str(e)
        )


def invoke_with_guardrail(client, prompt: str) -> BenchmarkResult:
    """Use Bedrock simple PII guardrail."""
    request_body = {
        "messages": [{"role": "user", "content": [{"text": prompt}]}],
        "inferenceConfig": {"maxTokens": 256, "temperature": 0.7}
    }

    start = time.perf_counter()
    try:
        response = client.invoke_model(
            modelId=MODEL_ID,
            body=json.dumps(request_body),
            contentType="application/json",
            accept="application/json",
            guardrailIdentifier=SIMPLE_PII_GUARDRAIL_ID,
            guardrailVersion=SIMPLE_PII_GUARDRAIL_VERSION
        )
        latency = (time.perf_counter() - start) * 1000
        response_body = json.loads(response["body"].read())

        blocked = response_body.get("stopReason") == "guardrail_intervened"

        return BenchmarkResult(
            prompt=prompt[:50] + "..." if len(prompt) > 50 else prompt,
            method="guardrail",
            latency_ms=latency,
            pii_check_ms=0,  # Included in latency
            total_ms=latency,
            pii_found=[],
            blocked=blocked,
            error=None
        )
    except Exception as e:
        latency = (time.perf_counter() - start) * 1000
        return BenchmarkResult(
            prompt=prompt[:50] + "..." if len(prompt) > 50 else prompt,
            method="guardrail",
            latency_ms=latency,
            pii_check_ms=0,
            total_ms=latency,
            pii_found=[],
            blocked="guardrail" in str(e).lower(),
            error=str(e)
        )


def invoke_with_regex(client, prompt: str) -> BenchmarkResult:
    """Use Python regex for PII detection before/after model call."""
    # Pre-check input for PII
    input_pii, input_check_time = detect_pii_regex(prompt)

    # Anonymize input if PII found (or could block here)
    processed_prompt = anonymize_pii_regex(prompt) if input_pii else prompt

    request_body = {
        "messages": [{"role": "user", "content": [{"text": processed_prompt}]}],
        "inferenceConfig": {"maxTokens": 256, "temperature": 0.7}
    }

    model_start = time.perf_counter()
    try:
        response = client.invoke_model(
            modelId=MODEL_ID,
            body=json.dumps(request_body),
            contentType="application/json",
            accept="application/json"
        )
        model_latency = (time.perf_counter() - model_start) * 1000
        response_body = json.loads(response["body"].read())

        # Post-check output for PII
        output_text = ""
        if "output" in response_body and "message" in response_body["output"]:
            content = response_body["output"]["message"].get("content", [])
            if content and "text" in content[0]:
                output_text = content[0]["text"]

        output_pii, output_check_time = detect_pii_regex(output_text)

        total_pii_check = input_check_time + output_check_time
        all_pii = list(set(input_pii + output_pii))

        return BenchmarkResult(
            prompt=prompt[:50] + "..." if len(prompt) > 50 else prompt,
            method="regex",
            latency_ms=model_latency,
            pii_check_ms=total_pii_check,
            total_ms=model_latency + total_pii_check,
            pii_found=all_pii,
            blocked=False,
            error=None
        )
    except Exception as e:
        model_latency = (time.perf_counter() - model_start) * 1000
        return BenchmarkResult(
            prompt=prompt[:50] + "..." if len(prompt) > 50 else prompt,
            method="regex",
            latency_ms=model_latency,
            pii_check_ms=input_check_time,
            total_ms=model_latency + input_check_time,
            pii_found=input_pii,
            blocked=False,
            error=str(e)
        )


def run_benchmark(client, prompts: list[str], iterations: int = 3) -> dict:
    """Run benchmark comparing all three methods."""
    results = {
        "no_protection": [],
        "guardrail": [],
        "regex": []
    }

    total = len(prompts) * iterations * 3
    current = 0

    print(f"\n{'='*70}")
    print("PII DETECTION PERFORMANCE COMPARISON")
    print(f"{'='*70}")
    print(f"Model: {MODEL_ID}")
    print(f"Simple PII Guardrail: {SIMPLE_PII_GUARDRAIL_ID}")
    print(f"Prompts: {len(prompts)}")
    print(f"Iterations: {iterations}")
    print(f"Total invocations: {total}")
    print(f"{'='*70}\n")

    # Warm-up
    print("Warming up...")
    invoke_no_protection(client, "Hello")
    invoke_with_guardrail(client, "Hello")
    invoke_with_regex(client, "Hello")
    print("Done.\n")

    for prompt in prompts:
        print(f"Testing: {prompt[:55]}...")

        for i in range(iterations):
            # No protection
            current += 1
            print(f"  [{current}/{total}] No protection...", end=" ", flush=True)
            r = invoke_no_protection(client, prompt)
            results["no_protection"].append(r)
            print(f"{r.total_ms:.0f}ms")

            # Guardrail
            current += 1
            print(f"  [{current}/{total}] Guardrail...", end=" ", flush=True)
            r = invoke_with_guardrail(client, prompt)
            results["guardrail"].append(r)
            status = "BLOCKED" if r.blocked else f"{r.total_ms:.0f}ms"
            print(status)

            # Regex
            current += 1
            print(f"  [{current}/{total}] Regex...", end=" ", flush=True)
            r = invoke_with_regex(client, prompt)
            results["regex"].append(r)
            pii_str = f" (PII: {', '.join(r.pii_found)})" if r.pii_found else ""
            print(f"{r.total_ms:.0f}ms{pii_str}")

        print()

    return results


def analyze_results(results: dict) -> None:
    """Analyze and display results."""
    print(f"\n{'='*70}")
    print("RESULTS SUMMARY")
    print(f"{'='*70}\n")

    for method, data in results.items():
        latencies = [r.total_ms for r in data if not r.error]
        blocked = sum(1 for r in data if r.blocked)

        if not latencies:
            continue

        print(f"{method.upper().replace('_', ' ')}:")
        print(f"  Requests:      {len(data)}")
        print(f"  Successful:    {len(latencies)}")
        if blocked:
            print(f"  Blocked:       {blocked}")
        print(f"  Mean latency:  {statistics.mean(latencies):.0f} ms")
        print(f"  Median:        {statistics.median(latencies):.0f} ms")
        print(f"  Min:           {min(latencies):.0f} ms")
        print(f"  Max:           {max(latencies):.0f} ms")
        if len(latencies) > 1:
            print(f"  Std dev:       {statistics.stdev(latencies):.0f} ms")
        print()

    # Overhead comparison
    no_prot = [r.total_ms for r in results["no_protection"] if not r.error]
    guardrail = [r.total_ms for r in results["guardrail"] if not r.error]
    regex = [r.total_ms for r in results["regex"] if not r.error]

    if no_prot and guardrail and regex:
        baseline = statistics.mean(no_prot)
        gr_mean = statistics.mean(guardrail)
        rx_mean = statistics.mean(regex)

        print(f"{'='*70}")
        print("OVERHEAD COMPARISON (vs No Protection)")
        print(f"{'='*70}")
        print(f"  Baseline (no protection):  {baseline:.0f} ms")
        print()
        print(f"  Guardrail overhead:        +{gr_mean - baseline:.0f} ms ({((gr_mean/baseline)-1)*100:+.1f}%)")
        print(f"  Regex overhead:            +{rx_mean - baseline:.0f} ms ({((rx_mean/baseline)-1)*100:+.1f}%)")
        print()
        print(f"  Guardrail vs Regex:        {gr_mean - rx_mean:+.0f} ms")
        print()

    # Regex timing breakdown
    regex_results = [r for r in results["regex"] if not r.error]
    if regex_results:
        avg_pii_check = statistics.mean([r.pii_check_ms for r in regex_results])
        print(f"{'='*70}")
        print("REGEX PII CHECK TIMING")
        print(f"{'='*70}")
        print(f"  Average PII check time:    {avg_pii_check:.3f} ms")
        print(f"  (This is the overhead of regex-based PII detection)")
        print()


def export_results(results: dict, filename: str = "pii_benchmark_results.json"):
    """Export results to JSON."""
    export = {
        "config": {
            "model": MODEL_ID,
            "guardrail_id": SIMPLE_PII_GUARDRAIL_ID,
            "region": REGION
        },
        "results": {}
    }

    for method, data in results.items():
        export["results"][method] = [
            {
                "prompt": r.prompt,
                "latency_ms": r.latency_ms,
                "pii_check_ms": r.pii_check_ms,
                "total_ms": r.total_ms,
                "pii_found": r.pii_found,
                "blocked": r.blocked,
                "error": r.error
            }
            for r in data
        ]

    with open(filename, "w") as f:
        json.dump(export, f, indent=2)

    print(f"Results exported to: {filename}")


def main():
    client = create_bedrock_client()
    results = run_benchmark(client, TEST_PROMPTS, iterations=1000)
    analyze_results(results)
    export_results(results)


if __name__ == "__main__":
    main()
