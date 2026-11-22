"""
FocusBoard Deployment Smoke Test Suite
Verifies that deployed backend and frontend services are live, healthy,
and responsive to API requests without mutating production database state.
"""
import sys
import time
import argparse
import urllib.request
import json

def test_endpoint(url, expected_code=200, timeout=10, description=""):
    print(f"[*] Testing {description}: {url} ...", end=" ")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "FocusBoard-SmokeTest/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as response:
            status = response.getcode()
            if status == expected_code:
                print(f"PASSED (HTTP {status})")
                return True
            else:
                print(f"FAILED (Expected {expected_code}, got {status})")
                return False
    except urllib.error.HTTPError as e:
        if e.code == expected_code:
            print(f"PASSED (HTTP {e.code})")
            return True
        print(f"FAILED (HTTP {e.code})")
        return False
    except Exception as e:
        print(f"FAILED (Exception: {e})")
        return False

def run_smoke_tests(backend_url, frontend_url):
    print("==================================================")
    print("   FOCUSBOARD PRODUCTION DEPLOYMENT SMOKE TESTS   ")
    print("==================================================")
    print(f"Target Backend:  {backend_url}")
    print(f"Target Frontend: {frontend_url}")
    print("--------------------------------------------------")

    results = []

    # 1. Backend Liveness probe
    results.append(test_endpoint(f"{backend_url}/health", 200, description="Backend Liveness Probe (/health)"))

    # 2. Backend Readiness & Database Connectivity probe
    results.append(test_endpoint(f"{backend_url}/ready", 200, description="Backend Readiness & DB Probe (/ready)"))

    # 3. OpenAPI Documentation probe
    results.append(test_endpoint(f"{backend_url}/docs", 200, description="FastAPI Interactive Docs (/docs)"))

    # 4. Protected API Route rejection test (Verifies authentication gateway is active)
    results.append(test_endpoint(f"{backend_url}/api/v1/tasks", 401, description="Security Gateway Auth Enforcement (/api/v1/tasks)"))

    # 5. Frontend Root Availability test
    results.append(test_endpoint(frontend_url, 200, description="Frontend Single Page Application Root (/)"))

    print("--------------------------------------------------")
    passed_count = sum(1 for r in results if r)
    total_count = len(results)
    print(f"Results: {passed_count}/{total_count} smoke tests passed.")

    if passed_count == total_count:
        print("[SUCCESS] All deployment smoke tests PASSED. Release is operational!")
        return 0
    else:
        print("[ERROR] One or more deployment smoke tests FAILED. Investigate logs.")
        return 1

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="FocusBoard Deployment Smoke Test Runner")
    parser.add_argument("--backend-url", default="http://localhost:8000", help="Base URL of backend API")
    parser.add_argument("--frontend-url", default="http://localhost:5173", help="Base URL of frontend application")
    args = parser.parse_args()

    exit_code = run_smoke_tests(args.backend_url.rstrip("/"), args.frontend_url.rstrip("/"))
    sys.exit(exit_code)
