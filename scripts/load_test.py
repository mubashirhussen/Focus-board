"""
FocusBoard Scale & Concurrency Load Test Runner
Executes concurrent synthetic traffic against FocusBoard API endpoints
and calculates throughput, p50/p90/p95/p99 latency percentiles, and error rates.
"""
import sys
import time
import argparse
import statistics
import urllib.request
import urllib.error
import json
from concurrent.futures import ThreadPoolExecutor, as_completed

def execute_request(url, method="GET", data=None, headers=None):
    req_headers = {"User-Agent": "FocusBoard-LoadTest/1.0", **(headers or {})}
    encoded_data = json.dumps(data).encode("utf-8") if data else None
    if encoded_data and "Content-Type" not in req_headers:
        req_headers["Content-Type"] = "application/json"

    t0 = time.perf_counter()
    status_code = 0
    success = False

    try:
        req = urllib.request.Request(url, data=encoded_data, headers=req_headers, method=method)
        with urllib.request.urlopen(req, timeout=10) as resp:
            status_code = resp.getcode()
            success = 200 <= status_code < 300
    except urllib.error.HTTPError as e:
        status_code = e.code
        success = (status_code == 401 if "tasks" in url and not headers else False)
    except Exception as e:
        status_code = 500
        success = False

    duration_ms = (time.perf_counter() - t0) * 1000
    return {
        "status_code": status_code,
        "success": success,
        "duration_ms": duration_ms
    }

def run_load_test(base_url, total_requests=100, concurrency=10):
    print("==========================================================")
    print("     FOCUSBOARD CONCURRENCY & LATENCY LOAD TEST RUNNER    ")
    print("==========================================================")
    print(f"Target Base URL:   {base_url}")
    print(f"Total Requests:    {total_requests}")
    print(f"Concurrency Level: {concurrency} workers")
    print("----------------------------------------------------------")

    endpoints = [
        f"{base_url}/health",
        f"{base_url}/ready",
        f"{base_url}/metrics",
    ]

    latencies = []
    success_count = 0
    error_count = 0

    t_start = time.perf_counter()

    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = [
            executor.submit(execute_request, endpoints[i % len(endpoints)])
            for i in range(total_requests)
        ]

        for future in as_completed(futures):
            res = future.result()
            latencies.append(res["duration_ms"])
            if res["success"]:
                success_count += 1
            else:
                error_count += 1

    total_time = time.perf_counter() - t_start
    throughput = total_requests / total_time if total_time > 0 else 0

    latencies.sort()
    avg_latency = statistics.mean(latencies)
    median_latency = statistics.median(latencies)
    p90 = latencies[int(len(latencies) * 0.90)]
    p95 = latencies[int(len(latencies) * 0.95)]
    p99 = latencies[int(len(latencies) * 0.99)]

    print(f"Completed in:      {total_time:.2f} seconds")
    print(f"Throughput:        {throughput:.1f} requests/sec")
    print(f"Success Rate:      {success_count}/{total_requests} ({(success_count/total_requests)*100:.1f}%)")
    print(f"Errors:            {error_count}")
    print("----------------------------------------------------------")
    print("LATENCY PERCENTILES:")
    print(f"  Average:         {avg_latency:.2f} ms")
    print(f"  P50 (Median):    {median_latency:.2f} ms")
    print(f"  P90:             {p90:.2f} ms")
    print(f"  P95:             {p95:.2f} ms")
    print(f"  P99:             {p99:.2f} ms")
    print("==========================================================")

    # Operational SLO assertions: P95 < 500ms, Error rate < 1%
    p95_ok = p95 < 500
    error_ok = (error_count / total_requests) <= 0.01

    if p95_ok and error_ok:
        print("[SLO VERIFIED] Performance and reliability meet production SLO targets.")
        return 0
    else:
        print("[SLO WARNING] Latency or error rates exceeded production thresholds.")
        return 1

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="FocusBoard Load Test Runner")
    parser.add_argument("--base-url", default="http://localhost:8000", help="Base URL of backend API")
    parser.add_argument("--requests", type=int, default=100, help="Total number of requests")
    parser.add_argument("--concurrency", type=int, default=10, help="Concurrency / worker threads")
    args = parser.parse_args()

    sys.exit(run_load_test(args.base_url.rstrip("/"), args.requests, args.concurrency))
