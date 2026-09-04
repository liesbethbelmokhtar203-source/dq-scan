# dq-scan

A tiny per-column data-quality scanner for a CSV. No pandas, no dependencies,
starts instantly. The first thing I run on every client export before I trust
it.

## What it tells you

For each column: nulls, duplicates, unique count, and — when the column looks
numeric — min, max, and mean. For non-numeric columns, the three most common
values.

## Use

```
python3 dq_scan.py path/to/export.csv
```

```
45023 rows, 12 columns
• order_id:    nulls=0    dupes=0    unique=45023
• amount:      nulls=12   dupes=3    unique=44991
    numeric: min=-1299.0 max=9821.5 mean=84.12
• currency:    nulls=0    dupes=44000 unique=23
    top: [('EUR', 44000), ('USD', 800), ('GBP', 223)]
```

## Why

pandas takes 2 seconds and 300 MB to tell me a column is 70% null. This takes
150 milliseconds and tells me the same thing. When you open 20 exports a day,
that difference is the difference between doing it and skipping it.

MIT licensed.
