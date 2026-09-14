from tests.benchmark import benchmark_concurrent_requests, benchmark_endpoint


def test_endpoint_benchmark_reports_percentile_and_throughput():
    result = benchmark_endpoint(lambda: None, "no-op", iterations=5, warmup=1)
    assert result["p95_ms"] >= 0
    assert result["throughput_rps"] > 0


def test_concurrent_benchmark_executes_real_requests():
    result = benchmark_concurrent_requests("/summary", concurrent=4)
    assert result["successful_requests"] == 4
    assert result["failed_requests"] == 0
    assert result["p95_ms"] >= 0
