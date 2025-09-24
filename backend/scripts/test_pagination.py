#!/usr/bin/env python3
"""
HTTP E2E test for /api/webinars pagination.

Requires API running locally on http://localhost:8000
"""
import sys
import time
import requests

BASE_URL = "http://localhost:8000/api"

def assert_condition(condition: bool, message: str):
    if not condition:
        print(f"❌ {message}")
        sys.exit(1)

def main():
    print("🧪 Testing /api/webinars pagination (HTTP)...")

    # First page
    params1 = {"offset": 0, "limit": 10}
    r1 = requests.get(f"{BASE_URL}/webinars", params=params1, timeout=10)
    assert_condition(r1.status_code == 200, f"Unexpected status for page 1: {r1.status_code}")
    data1 = r1.json()

    total = data1.get("total", 0)
    items1 = data1.get("webinars", [])
    has_more1 = data1.get("hasMore")

    print(f"   Total={total}, page1={len(items1)}, hasMore={has_more1}")
    assert_condition(isinstance(total, int) and total >= 0, "total should be integer >= 0")
    assert_condition(len(items1) <= 10, "page1 should return <= limit items")

    if total == 0:
        print("⚠️  No webinars available to fully test pagination.")
        print("✅ Basic pagination response shape verified.")
        return

    # Second page
    params2 = {"offset": len(items1), "limit": 10}
    r2 = requests.get(f"{BASE_URL}/webinars", params=params2, timeout=10)
    assert_condition(r2.status_code == 200, f"Unexpected status for page 2: {r2.status_code}")
    data2 = r2.json()
    items2 = data2.get("webinars", [])
    has_more2 = data2.get("hasMore")

    # Basic assertions
    assert_condition(data2.get("total") == total, "total must be stable across pages")
    assert_condition(len(items2) <= 10, "page2 should return <= limit items")

    # If both pages non-empty, attempt non-duplication check by ids
    if items1 and items2 and all("id" in it for it in items1 + items2):
        ids1 = {it["id"] for it in items1}
        ids2 = {it["id"] for it in items2}
        assert_condition(ids1.isdisjoint(ids2), "Pages should not overlap by id for offset-based pagination")

    print(f"   page2={len(items2)}, hasMore={has_more2}")

    # hasMore expectation: if offset + returned < total -> hasMore should be True
    expected_has_more1 = (params1["offset"] + len(items1)) < total
    expected_has_more2 = (params2["offset"] + len(items2)) < total
    assert_condition(has_more1 == expected_has_more1, "hasMore on page1 mismatch")
    assert_condition(has_more2 == expected_has_more2, "hasMore on page2 mismatch")

    print("✅ Pagination e2e passed")

if __name__ == "__main__":
    main()


