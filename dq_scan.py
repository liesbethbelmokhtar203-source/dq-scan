#!/usr/bin/env python3
"""dq-scan: per-column data-quality scan for a CSV. No dependencies."""
import csv
import math
import sys
from collections import Counter
from fractions import Fraction


def scan(path, delim=","):
    with open(path, newline="", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f, delimiter=delim)
        counts = {c: Counter() for c in reader.fieldnames or []}
        cols = list(counts)
        row_count = 0
        for row in reader:
            row_count += 1
            for c in counts:
                counts[c][row[c]] += 1
    if not row_count:
        print("empty file (no rows / no header)")
        return 1

    print(f"{row_count} rows, {len(cols)} columns\n")

    for c in cols:
        values = counts[c]
        nonempty = Counter({v: n for v, n in values.items() if v not in ("", None)})
        nulls = values[""] + values[None]
        unique = len(values)
        dupes = row_count - unique

        nums = []
        for v, n in nonempty.items():
            try:
                nums.append((float(v), n))
            except (ValueError, TypeError):
                pass

        print(f"• {c:24} nulls={nulls:<6} dupes={dupes:<6} unique={unique}")
        if len(nums) == len(nonempty) and nums:
            numbers = [v for v, n in nums]
            if all(math.isfinite(v) for v in numbers):
                # Group exact float ratios to preserve statistics.mean precision.
                partials = {}
                for v, n in nums:
                    numerator, denominator = v.as_integer_ratio()
                    partials[denominator] = partials.get(denominator, 0) + numerator * n
                total = sum((Fraction(n, d) for d, n in partials.items()), Fraction())
                mean = float(total / sum(nonempty.values()))
            else:
                mean = sum(v for v in numbers if not math.isfinite(v))
            print(f"{'':28}numeric: min={min(numbers)} max={max(numbers)} "
                  f"mean={mean:.2f}")
        else:
            top = nonempty.most_common(3)
            print(f"{'':28}top: {top}")
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: dq-scan <file.csv>")
        sys.exit(1)
    sys.exit(scan(sys.argv[1]))
