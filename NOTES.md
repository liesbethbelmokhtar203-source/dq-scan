# Notes

Edge cases for the null detector:

- empty string vs actual null — csv.DictReader gives "" for an empty cell, not None.
- trailing comma on the last row produces a phantom empty column. Skip it.
- BOM at the start of an export breaks the first header. Strip \ufeff.

## Large files

Reading the whole file into memory is fine up to ~50MB. Past that, stream row by
row and aggregate per-column counters instead of holding the list. The numeric
check (float() per cell) is the expensive part — skip it once a column shows more
than a few non-numeric values.
