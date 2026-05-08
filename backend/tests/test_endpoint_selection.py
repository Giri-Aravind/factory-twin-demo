"""Run endpoint selection tests against v7's selector — with decomposer-as-gate.

For each test query:
  1. Run the decomposer first.
  2. If it produces a multi-step plan, send STEP 1's standalone_query to the selector.
  3. Otherwise, send the original query to the selector.

This is the behavior the supervisor uses in production for is_multi_step queries.
The test set's expected_endpoint for multi-step queries (D001, D003, D006, etc.)
is the FIRST endpoint of the plan, so this should fix that cluster.

Usage:
  cd backend
  python tests/test_endpoint_selection.py
  python tests/test_endpoint_selection.py --verbose
"""
import sys
import os
import io
import json
import contextlib
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.endpoint_selector import select_endpoint
from agents.query_decomposer import decompose_query


TEST_FILE = Path(__file__).parent / "endpoint_test_cases_relevant_only.txt"


def load_test_cases():
    cases = []
    with open(TEST_FILE, "r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                cases.append(json.loads(line))
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON on line {line_no}: {e}")
    return cases


def run_one(query: str, verbose: bool = False) -> dict:
    """Run decomposer-as-gate, then select_endpoint on the resulting query."""

    def _run():
        state = {
            "user_query": query,
            "conversation_history": [],
            "category": None,
        }

        # Step 1: Decomposer-as-gate.
        # If the query is multi-step, replace user_query with step 1's standalone_query.
        decomp = decompose_query(state)
        plan = decomp.get("query_plan")
        used_decomposer = False
        step1_query = None

        if plan and plan.get("steps"):
            step1 = plan["steps"][0]
            step1_query = step1.get("standalone_query") or query
            state["user_query"] = step1_query
            used_decomposer = True

        # Step 2: Endpoint selection on (possibly rewritten) query.
        sel_result = select_endpoint(state)
        state.update(sel_result)

        selected = state.get("current_endpoint")
        return {
            "endpoint": selected.get("endpoint_name") if selected else None,
            "used_decomposer": used_decomposer,
            "step1_query": step1_query,
        }

    if verbose:
        return _run()
    else:
        with contextlib.redirect_stdout(io.StringIO()):
            return _run()


def main():
    verbose = "--verbose" in sys.argv or "-v" in sys.argv

    cases = load_test_cases()
    total = len(cases)
    passed = 0
    failed_cases = []

    print(f"\nRunning {total} test cases (verbose={verbose})...\n")

    for i, case in enumerate(cases, start=1):
        query = case["query"]
        expected = case["expected_endpoint"]

        try:
            result = run_one(query, verbose=verbose)
            actual = result["endpoint"]
            decomp_used = result["used_decomposer"]
            step1 = result["step1_query"]
        except Exception:
            actual = None
            decomp_used = False
            step1 = None

        if actual == expected:
            passed += 1
        else:
            failed_cases.append({
                "id": case.get("id"),
                "difficulty": case.get("difficulty"),
                "query": query,
                "expected": expected,
                "actual": actual,
                "decomp_used": decomp_used,
                "step1_query": step1,
            })

        if i % 10 == 0 or i == total:
            print(f"  [{i}/{total}]  passed={passed} failed={i-passed}")

    failed = len(failed_cases)
    print("\n" + "=" * 100)
    print("SUMMARY")
    print("=" * 100)
    print(f"Total:   {total}")
    print(f"Passed:  {passed}  ({100*passed/total:.1f}%)")
    print(f"Failed:  {failed}")

    if failed == 0:
        print("\nAll passed.\n")
        return

    by_diff = defaultdict(lambda: [0, 0])
    failed_ids = {f["id"] for f in failed_cases}
    for case in cases:
        diff = case.get("difficulty", "unknown")
        if case["id"] in failed_ids:
            by_diff[diff][1] += 1
        else:
            by_diff[diff][0] += 1
    print("\nBy difficulty:")
    for diff in ("easy", "medium", "complex", "difficult"):
        if diff in by_diff:
            p, f = by_diff[diff]
            t = p + f
            print(f"  {diff:<10s} {p}/{t} passed ({100*p/t:.0f}%)")

    # Count how often decomposer fired in failures
    decomp_fired = sum(1 for f in failed_cases if f["decomp_used"])
    print(f"\nDecomposer fired in {decomp_fired}/{failed} failures")

    print("\n" + "=" * 100)
    print("FAILED CASES")
    print("=" * 100)
    print(f"{'ID':<6}{'DIFF':<11}{'DECOMP':<8}{'EXPECTED':<35}{'ACTUAL':<35}QUERY")
    print("-" * 180)
    for c in failed_cases:
        exp = (c["expected"] or "?")[:33]
        act = (c["actual"] or "?")[:33]
        decomp_flag = "YES" if c["decomp_used"] else "no"
        print(f"{c['id']:<6}{c['difficulty']:<11}{decomp_flag:<8}{exp:<35}{act:<35}{c['query']}")
        if c["decomp_used"] and c["step1_query"]:
            print(f"      step1_query: {c['step1_query']}")


if __name__ == "__main__":
    main()