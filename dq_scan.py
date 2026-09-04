#!/usr/bin/env python3
"""dq-scan: per-column data-quality scan for a CSV. No dependencies."""
import csv
import sys
import statistics
from collections import Counter


def scan(path, delim=","):
    with open(path, newline="", encoding="utf-8", errors="replace") as f:
        rows = list(csv.DictReader(f, delimiter=delim))
    if not rows:
        print("empty file (no rows / no header)")
        return 1

    cols = list(rows[0].keys())
    print(f"{len(rows)} rows, {len(cols)} columns\n")

    for c in cols:
        vals = [r[c] for r in rows]
        nonempty = [v for v in vals if v not in ("", None)]
        nulls = len(vals) - len(nonempty)
        dupes = len(vals) - len(set(vals))
        unique = len(set(vals))

        nums = []
        for v in nonempty:
            try:
                nums.append(float(v))
            except (ValueError, TypeError):
                pass

        print(f"• {c:24} nulls={nulls:<6} dupes={dupes:<6} unique={unique}")
        if len(nums) == len(nonempty) and nums:
            print(f"{'':28}numeric: min={min(nums)} max={max(nums)} "
                  f"mean={statistics.mean(nums):.2f}")
        else:
            top = Counter(nonempty).most_common(3)
            print(f"{'':28}top: {top}")
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: dq-scan <file.csv>")
        sys.exit(1)
    sys.exit(scan(sys.argv[1]))
