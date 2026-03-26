import sys
import time
sys.path.append("..")  # so we can import agent.py from the parent dir

from agent import ask, setup_db

DELAY_SECONDS = 13  # free tier: 5 requests/min → 1 per 12s to be safe

# ── Test cases ────────────────────────────────────────────────────────────────
# Each case: question + a function that checks the rows returned are correct

EVALS = [
    {
        "question": "How many customers are there?",
        "check": lambda rows: rows == [{"count": 3}],
        "description": "total customer count",
    },
    {
        "question": "Which customer spent the most money in total?",
        "check": lambda rows: rows[0]["name"] == "Carol",
        "description": "top spender is Carol",
    },
    {
        "question": "How many orders has Alice placed?",
        "check": lambda rows: rows[0].get("count") == 2,
        "description": "Alice has 2 orders",
    },
    {
        "question": "What is the most expensive product?",
        "check": lambda rows: rows[0]["name"] == "Laptop",
        "description": "most expensive product is Laptop",
    },
    {
        "question": "What is the total revenue across all orders?",
        "check": lambda rows: abs(list(rows[0].values())[0] - 4318.93) < 1,
        "description": "total revenue ≈ 4318.93",
    },
    {
        "question": "What is the weather today?",  # off-topic — should return error
        "check": lambda rows: False,  # should never reach check
        "expect_error": True,
        "description": "off-topic question returns error",
    },
]

# ── Runner ────────────────────────────────────────────────────────────────────

def run():
    conn = setup_db()
    passed = 0

    for i, case in enumerate(EVALS, 1):
        if i > 1:
            time.sleep(DELAY_SECONDS)
        q = case["question"]
        expect_error = case.get("expect_error", False)

        try:
            result = ask(q, conn)
        except Exception as e:
            print(f"[{i}] FAIL (exception) — {case['description']}\n     {e}\n")
            continue

        if "error" in result:
            if expect_error:
                print(f"[{i}] PASS — {case['description']}")
                passed += 1
            else:
                print(f"[{i}] FAIL — {case['description']}\n     error: {result['error']}\n")
            continue

        rows = result["rows"]
        ok = case["check"](rows)

        if ok:
            print(f"[{i}] PASS — {case['description']}")
            passed += 1
        else:
            print(f"[{i}] FAIL — {case['description']}")
            print(f"     SQL:  {result['sql']}")
            print(f"     rows: {rows}\n")

    total = len(EVALS)
    print(f"\n{passed}/{total} passed ({100 * passed // total}%)")

if __name__ == "__main__":
    run()
