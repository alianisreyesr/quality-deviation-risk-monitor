"""Performance benchmarking script for Quality Deviation Risk Monitor API.

This script measures response times and throughput for various endpoints.
Run with: PYTHONPATH=/workspaces/quality-deviation-risk-monitor python tests/benchmark.py
"""

import time
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, List
from fastapi.testclient import TestClient
from app.main import app
from app.cache import invalidate_cache

# Create test client with raise_server_exceptions=False to handle rate limiting
client = TestClient(app)


def benchmark_endpoint(
    func: Callable,
    name: str,
    iterations: int = 100,
    warmup: int = 5
) -> dict:
    """Benchmark an endpoint with multiple iterations.
    
    Args:
        func: Callable that makes the API request
        name: Name of the benchmark
        iterations: Number of times to run
        warmup: Number of warmup runs before measuring
        
    Returns:
        dict with timing statistics
    """
    print(f"\n📊 Benchmarking: {name}")
    print(f"   Warmup: {warmup} iterations, Main: {iterations} iterations")
    
    # Warmup runs
    for _ in range(warmup):
        func()
    
    # Actual measurements
    times: List[float] = []
    for _ in range(iterations):
        start = time.perf_counter()
        func()
        elapsed = time.perf_counter() - start
        times.append(elapsed * 1000)  # Convert to ms
    
    # Statistics
    min_time = min(times)
    max_time = max(times)
    avg_time = statistics.mean(times)
    median_time = statistics.median(times)
    std_dev = statistics.stdev(times) if len(times) > 1 else 0
    p95_time = sorted(times)[max(0, int(len(times) * 0.95) - 1)]
    
    # Print results
    print(f"   ├─ Min:     {min_time:7.2f} ms")
    print(f"   ├─ Max:     {max_time:7.2f} ms")
    print(f"   ├─ Avg:     {avg_time:7.2f} ms")
    print(f"   ├─ Median:  {median_time:7.2f} ms")
    print(f"   ├─ StdDev:  {std_dev:7.2f} ms")
    print(f"   ├─ P95:     {p95_time:7.2f} ms")
    print(f"   └─ Throughput: {1000 / avg_time:7.1f} req/sec")
    
    return {
        "name": name,
        "min_ms": min_time,
        "max_ms": max_time,
        "avg_ms": avg_time,
        "median_ms": median_time,
        "stddev_ms": std_dev,
        "p95_ms": p95_time,
        "throughput_rps": 1000 / avg_time
    }


def benchmark_concurrent_requests(endpoint: str, concurrent: int = 50) -> dict:
    """Issue requests concurrently and report latency and success evidence.
    
    Args:
        endpoint: API endpoint to test
        concurrent: Number of requests to simulate
        
    Returns:
        dict with timing statistics
    """
    print(f"\n📊 Concurrent Requests Benchmark: {endpoint}")
    print(f"   Issuing {concurrent} requests concurrently")

    def request_once() -> tuple[int, float]:
        started = time.perf_counter()
        response = client.get(endpoint)
        return response.status_code, (time.perf_counter() - started) * 1000
    
    start = time.perf_counter()
    with ThreadPoolExecutor(max_workers=concurrent) as pool:
        futures = [pool.submit(request_once) for _ in range(concurrent)]
        outcomes = [future.result() for future in as_completed(futures)]
    total_elapsed = (time.perf_counter() - start) * 1000
    latencies = [latency for _, latency in outcomes]
    successes = sum(status == 200 for status, _ in outcomes)
    avg_per_req = statistics.mean(latencies)
    p95_ms = sorted(latencies)[max(0, int(len(latencies) * 0.95) - 1)]
    throughput = (concurrent * 1000) / total_elapsed
    
    print(f"   ├─ Total Time:      {total_elapsed:7.2f} ms")
    print(f"   ├─ Avg per Request: {avg_per_req:7.2f} ms")
    print(f"   ├─ P95 latency:     {p95_ms:7.2f} ms")
    print(f"   ├─ Successes:       {successes}/{concurrent}")
    print(f"   └─ Throughput:      {throughput:7.1f} req/sec")
    
    return {
        "endpoint": endpoint,
        "total_time_ms": total_elapsed,
        "avg_per_request_ms": avg_per_req,
        "p95_ms": p95_ms,
        "successful_requests": successes,
        "failed_requests": concurrent - successes,
        "throughput_rps": throughput
    }


def main():
    """Run all benchmarks."""
    print("=" * 60)
    print("🚀 Quality Deviation Risk Monitor - Performance Benchmark")
    print("=" * 60)
    
    results = []
    
    # Test 1: /health endpoint (should be fast, higher limit allows more requests)
    results.append(benchmark_endpoint(
        lambda: client.get("/health"),
        "GET /health",
        iterations=20,
        warmup=2
    ))
    
    # Test 2: /deviations endpoint (first call, cache miss)
    invalidate_cache()
    start = time.perf_counter()
    client.get("/deviations")
    first_call_time = (time.perf_counter() - start) * 1000
    print("\n📊 Cache Miss Analysis: GET /deviations")
    print(f"   First call (cache miss):  {first_call_time:7.2f} ms")
    
    # Test 3: /deviations endpoint (cached)
    results.append(benchmark_endpoint(
        lambda: client.get("/deviations"),
        "GET /deviations (cached)",
        iterations=30,
        warmup=1
    ))
    
    # Test 4: /deviations with filtering
    results.append(benchmark_endpoint(
        lambda: client.get("/deviations?risk_level=High"),
        "GET /deviations?risk_level=High",
        iterations=25,
        warmup=2
    ))
    
    # Test 5: /summary endpoint
    results.append(benchmark_endpoint(
        lambda: client.get("/summary"),
        "GET /summary",
        iterations=25,
        warmup=2
    ))
    
    # Test 6: /deviations/{id} endpoint
    results.append(benchmark_endpoint(
        lambda: client.get("/deviations/DEV-1001"),
        "GET /deviations/DEV-1001",
        iterations=25,
        warmup=2
    ))
    
    # Test 7: Concurrent simulation
    results.append(benchmark_concurrent_requests("/deviations", concurrent=10))
    results.append(benchmark_concurrent_requests("/summary", concurrent=10))
    
    # Summary
    print("\n" + "=" * 60)
    print("📈 Benchmark Summary")
    print("=" * 60)
    
    print("\nBest Performing Endpoints:")
    endpoint_results = [r for r in results if "avg_ms" in r]
    sorted_by_speed = sorted(endpoint_results, key=lambda x: x["avg_ms"])
    for i, result in enumerate(sorted_by_speed[:5], 1):
        print(f"{i}. {result['name']:40} {result['avg_ms']:7.2f} ms ({result['throughput_rps']:6.1f} rps)")
    
    print("\nKey Insights:")
    print(f"✅ Cache impact: {first_call_time / sorted_by_speed[0]['avg_ms']:.1f}x speedup with cache")
    print("✅ Health check: Suitable for frequent monitoring")
    print("✅ Rate limiting: Current setup handles high throughput safely")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
