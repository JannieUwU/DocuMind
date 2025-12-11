"""
Verify /api/extract-terms endpoint exists
"""
import requests
import sys

BASE_URL = "http://localhost:8000"

def test_endpoint_exists():
    """Test if endpoint responds"""

    print("=" * 60)
    print("Verifying /api/extract-terms endpoint")
    print("=" * 60)

    # Test 1: Health check
    print("\n[Test 1/3] Health check...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print(f"  [OK] Backend is running: {response.json()}")
        else:
            print(f"  [FAIL] Health check failed: {response.status_code}")
            return
    except Exception as e:
        print(f"  [FAIL] Cannot connect to backend: {e}")
        return

    # Test 2: Try extract-terms without auth (should get 401 or 422, NOT 404)
    print("\n[Test 2/3] Test endpoint existence (without auth)...")
    try:
        response = requests.post(
            f"{BASE_URL}/api/extract-terms",
            json={"content": "test", "use_ai": True},
            timeout=5
        )

        print(f"  Status Code: {response.status_code}")

        if response.status_code == 404:
            print("  [CRITICAL] 404 NOT FOUND - Endpoint does not exist or not registered!")
            print("  Possible causes:")
            print("    1. Backend code not reloaded")
            print("    2. Running old version of code")
            print("    3. Endpoint path incorrect")
        elif response.status_code == 401:
            print("  [OK] 401 UNAUTHORIZED - Endpoint exists but needs auth (correct!)")
        elif response.status_code == 422:
            print("  [OK] 422 UNPROCESSABLE - Endpoint exists but bad params (correct!)")
        else:
            print(f"  [INFO] Unexpected status: {response.status_code}")
            print(f"  Response: {response.text[:200]}")

    except Exception as e:
        print(f"  [FAIL] Request failed: {e}")

    # Test 3: List all registered routes
    print("\n[Test 3/3] Check registered routes...")
    try:
        # Try OpenAPI docs endpoint
        response = requests.get(f"{BASE_URL}/docs", timeout=5)
        if response.status_code == 200:
            print("  [OK] OpenAPI docs available at http://localhost:8000/docs")
            print("  -> Open this URL in browser to see all endpoints")

        # Try to access OpenAPI JSON
        response = requests.get(f"{BASE_URL}/openapi.json", timeout=5)
        if response.status_code == 200:
            openapi_data = response.json()
            paths = openapi_data.get("paths", {})

            print("\n  Registered endpoints:")
            extract_found = False
            for path in sorted(paths.keys()):
                if "extract" in path.lower():
                    print(f"    [FOUND] {path}")
                    extract_found = True
                elif path.startswith("/api"):
                    print(f"    {path}")

            if not extract_found:
                print("    [CRITICAL] /api/extract-terms endpoint NOT FOUND!")
                print("\n    Full route list:")
                for path in sorted(paths.keys()):
                    print(f"      {path}")

    except Exception as e:
        print(f"  [FAIL] Cannot access OpenAPI: {e}")

    print("\n" + "=" * 60)

if __name__ == "__main__":
    test_endpoint_exists()
