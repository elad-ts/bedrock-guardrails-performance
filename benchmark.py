#!/usr/bin/env python3
"""
Bedrock Guardrails Performance Benchmark
Compares model invocation latency with and without guardrails.
Uses Amazon Nova Pro 1.0 model.
"""

import boto3
import json
import time
import statistics
from dataclasses import dataclass
from typing import Optional


# Configuration
REGION = "us-east-1"
MODEL_ID = "amazon.nova-pro-v1:0"
GUARDRAIL_ID = "wys9zt8hy6n4"
GUARDRAIL_VERSION = "1"

# Test prompts - mix of safe and potentially filtered content
TEST_PROMPTS = [
    # Safe prompts
    "What is the capital of France?",
    "Explain how photosynthesis works in simple terms.",
    "Write a short poem about the ocean.",
    "What are the benefits of regular exercise?",
    "Describe the water cycle.",
    # Prompts that may trigger PII detection
    "My email is test@example.com, can you help me write a professional signature?",
    "The server IP 192.168.1.100 is not responding, what should I check?",
    # Prompts that may trigger content filters
    "What are some conflict resolution strategies?",
    "How do I handle criticism at work?",
    "Explain the history of martial arts.",
]


@dataclass
class BenchmarkResult:
    """Result of a single benchmark run."""
    prompt: str
    with_guardrail: bool
    latency_ms: float
    input_tokens: Optional[int]
    output_tokens: Optional[int]
    blocked: bool
    error: Optional[str]


def create_bedrock_client():
    """Create Bedrock Runtime client."""
    return boto3.client("bedrock-runtime", region_name=REGION)


def invoke_model(
    client,
    prompt: str,
    use_guardrail: bool = False
) -> BenchmarkResult:
    """
    Invoke the Nova Pro model with or without guardrail.
    Returns benchmark result with latency and token counts.
    """
    # Build request body for Nova Pro
    request_body = {
        "messages": [
            {
                "role": "user",
                "content": [{"text": prompt}]
            }
        ],
        "inferenceConfig": {
            "maxTokens": 512,
            "temperature": 0.7,
            "topP": 0.9
        }
    }

    # Build API call parameters
    api_params = {
        "modelId": MODEL_ID,
        "body": json.dumps(request_body),
        "contentType": "application/json",
        "accept": "application/json"
    }

    # Add guardrail if enabled
    if use_guardrail:
        api_params["guardrailIdentifier"] = GUARDRAIL_ID
        api_params["guardrailVersion"] = GUARDRAIL_VERSION

    blocked = False
    error = None
    input_tokens = None
    output_tokens = None

    try:
        # Measure latency
        start_time = time.perf_counter()
        response = client.invoke_model(**api_params)
        end_time = time.perf_counter()

        latency_ms = (end_time - start_time) * 1000

        # Parse response
        response_body = json.loads(response["body"].read())

        # Extract token counts
        if "usage" in response_body:
            input_tokens = response_body["usage"].get("inputTokens")
            output_tokens = response_body["usage"].get("outputTokens")

        # Check if blocked by guardrail
        if use_guardrail:
            stop_reason = response_body.get("stopReason", "")
            if stop_reason == "guardrail_intervened":
                blocked = True

    except client.exceptions.ValidationException as e:
        end_time = time.perf_counter()
        latency_ms = (end_time - start_time) * 1000
        error = str(e)
        if "guardrail" in error.lower():
            blocked = True

    except Exception as e:
        end_time = time.perf_counter()
        latency_ms = (end_time - start_time) * 1000
        error = str(e)

    return BenchmarkResult(
        prompt=prompt[:50] + "..." if len(prompt) > 50 else prompt,
        with_guardrail=use_guardrail,
        latency_ms=latency_ms,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        blocked=blocked,
        error=error
    )


def run_benchmark(
    client,
    prompts: list[str],
    iterations: int = 3
) -> dict:
    """
    Run benchmark comparing guardrail vs no guardrail performance.
    Each prompt is run multiple times to get stable measurements.
    """
    results_without_guardrail = []
    results_with_guardrail = []

    total_runs = len(prompts) * iterations * 2
    current_run = 0

    print(f"\n{'='*70}")
    print(f"BEDROCK GUARDRAILS PERFORMANCE BENCHMARK")
    print(f"{'='*70}")
    print(f"Model: {MODEL_ID}")
    print(f"Guardrail ID: {GUARDRAIL_ID}")
    print(f"Prompts: {len(prompts)}")
    print(f"Iterations per prompt: {iterations}")
    print(f"Total invocations: {total_runs}")
    print(f"{'='*70}\n")

    # Warm-up call
    print("Warming up...")
    invoke_model(client, "Hello", use_guardrail=False)
    invoke_model(client, "Hello", use_guardrail=True)
    print("Warm-up complete.\n")

    for prompt in prompts:
        print(f"Testing: {prompt[:60]}...")

        for i in range(iterations):
            # Without guardrail
            current_run += 1
            print(f"  [{current_run}/{total_runs}] Without guardrail...", end=" ")
            result = invoke_model(client, prompt, use_guardrail=False)
            results_without_guardrail.append(result)
            print(f"{result.latency_ms:.1f}ms")

            # With guardrail
            current_run += 1
            print(f"  [{current_run}/{total_runs}] With guardrail...", end=" ")
            result = invoke_model(client, prompt, use_guardrail=True)
            results_with_guardrail.append(result)
            status = "BLOCKED" if result.blocked else f"{result.latency_ms:.1f}ms"
            print(status)

        print()

    return {
        "without_guardrail": results_without_guardrail,
        "with_guardrail": results_with_guardrail
    }


def analyze_results(results: dict) -> None:
    """Analyze and print benchmark results."""
    without_gr = results["without_guardrail"]
    with_gr = results["with_guardrail"]

    # Filter out errors for latency calculation
    latencies_without = [r.latency_ms for r in without_gr if not r.error]
    latencies_with = [r.latency_ms for r in with_gr if not r.error]

    blocked_count = sum(1 for r in with_gr if r.blocked)

    print(f"\n{'='*70}")
    print("BENCHMARK RESULTS")
    print(f"{'='*70}\n")

    # Without guardrail stats
    print("WITHOUT GUARDRAIL:")
    print(f"  Total requests:    {len(without_gr)}")
    print(f"  Successful:        {len(latencies_without)}")
    if latencies_without:
        print(f"  Mean latency:      {statistics.mean(latencies_without):.1f} ms")
        print(f"  Median latency:    {statistics.median(latencies_without):.1f} ms")
        print(f"  Std deviation:     {statistics.stdev(latencies_without):.1f} ms" if len(latencies_without) > 1 else "")
        print(f"  Min latency:       {min(latencies_without):.1f} ms")
        print(f"  Max latency:       {max(latencies_without):.1f} ms")
        p95_without = sorted(latencies_without)[int(len(latencies_without) * 0.95)] if len(latencies_without) >= 20 else max(latencies_without)
        print(f"  P95 latency:       {p95_without:.1f} ms")

    print()

    # With guardrail stats
    print("WITH GUARDRAIL:")
    print(f"  Total requests:    {len(with_gr)}")
    print(f"  Successful:        {len(latencies_with)}")
    print(f"  Blocked:           {blocked_count}")
    if latencies_with:
        print(f"  Mean latency:      {statistics.mean(latencies_with):.1f} ms")
        print(f"  Median latency:    {statistics.median(latencies_with):.1f} ms")
        print(f"  Std deviation:     {statistics.stdev(latencies_with):.1f} ms" if len(latencies_with) > 1 else "")
        print(f"  Min latency:       {min(latencies_with):.1f} ms")
        print(f"  Max latency:       {max(latencies_with):.1f} ms")
        p95_with = sorted(latencies_with)[int(len(latencies_with) * 0.95)] if len(latencies_with) >= 20 else max(latencies_with)
        print(f"  P95 latency:       {p95_with:.1f} ms")

    print()

    # Comparison
    if latencies_without and latencies_with:
        mean_without = statistics.mean(latencies_without)
        mean_with = statistics.mean(latencies_with)
        overhead = mean_with - mean_without
        overhead_pct = (overhead / mean_without) * 100

        print(f"{'='*70}")
        print("GUARDRAIL OVERHEAD ANALYSIS")
        print(f"{'='*70}")
        print(f"  Mean latency overhead:     {overhead:+.1f} ms")
        print(f"  Percentage overhead:       {overhead_pct:+.1f}%")
        print(f"  Requests blocked:          {blocked_count}/{len(with_gr)} ({100*blocked_count/len(with_gr):.1f}%)")

    print()

    # Detailed results table
    print(f"{'='*70}")
    print("DETAILED RESULTS")
    print(f"{'='*70}")
    print(f"{'Prompt':<45} {'No GR (ms)':<12} {'With GR (ms)':<12} {'Blocked':<8}")
    print("-" * 77)

    # Group by prompt
    prompts_seen = []
    for r in without_gr:
        if r.prompt not in prompts_seen:
            prompts_seen.append(r.prompt)

    for prompt in prompts_seen:
        without_times = [r.latency_ms for r in without_gr if r.prompt == prompt and not r.error]
        with_times = [r.latency_ms for r in with_gr if r.prompt == prompt and not r.error]
        was_blocked = any(r.blocked for r in with_gr if r.prompt == prompt)

        avg_without = statistics.mean(without_times) if without_times else 0
        avg_with = statistics.mean(with_times) if with_times else 0

        blocked_str = "YES" if was_blocked else "NO"
        print(f"{prompt:<45} {avg_without:<12.1f} {avg_with:<12.1f} {blocked_str:<8}")


def export_results_json(results: dict, filename: str = "benchmark_results.json") -> None:
    """Export results to JSON file."""
    export_data = {
        "config": {
            "model_id": MODEL_ID,
            "guardrail_id": GUARDRAIL_ID,
            "guardrail_version": GUARDRAIL_VERSION,
            "region": REGION
        },
        "results": {
            "without_guardrail": [
                {
                    "prompt": r.prompt,
                    "latency_ms": r.latency_ms,
                    "input_tokens": r.input_tokens,
                    "output_tokens": r.output_tokens,
                    "error": r.error
                }
                for r in results["without_guardrail"]
            ],
            "with_guardrail": [
                {
                    "prompt": r.prompt,
                    "latency_ms": r.latency_ms,
                    "input_tokens": r.input_tokens,
                    "output_tokens": r.output_tokens,
                    "blocked": r.blocked,
                    "error": r.error
                }
                for r in results["with_guardrail"]
            ]
        }
    }

    with open(filename, "w") as f:
        json.dump(export_data, f, indent=2)

    print(f"\nResults exported to: {filename}")


def main():
    """Main entry point."""
    client = create_bedrock_client()

    # Run benchmark
    results = run_benchmark(
        client=client,
        prompts=TEST_PROMPTS,
        iterations=3
    )

    # Analyze and display results
    analyze_results(results)

    # Export to JSON
    export_results_json(results)


if __name__ == "__main__":
    main()
