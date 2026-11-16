"""Correctness tests: every algorithm must match sorted() on random and edge inputs."""

import random
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from algorithms import ALGORITHMS


def final_array(name, data):
    last = None
    for last in ALGORITHMS[name][1](data):
        pass
    return last.array


def edge_cases():
    return [
        [],
        [1],
        [5, 5, 5, 5],
        [1, 2, 3, 4, 5],
        [5, 4, 3, 2, 1],
        [3, -1, 0, 7, -5, 2],
        list(range(50)),
        list(range(50, 0, -1)),
    ]


def test_all():
    rng = random.Random(42)
    failed = 0
    for name in ALGORITHMS:
        cases = edge_cases() + [
            [rng.randint(-100, 100) for _ in range(rng.randint(0, 60))]
            for _ in range(100)
        ]
        for case in cases:
            got = final_array(name, case)
            if got != sorted(case):
                print(f"FAIL {name}: input={case} got={got}")
                failed += 1
        print(f"{name}: {len(cases)} cases passed")
    if failed:
        print(f"{failed} failures")
        sys.exit(1)
    print("All tests passed.")


if __name__ == "__main__":
    test_all()
