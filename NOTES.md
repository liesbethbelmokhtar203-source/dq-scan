# Notes

Edge cases for the null detector:

- empty string vs actual null — csv.DictReader gives "" for an empty cell, not None.
- trailing comma on the last row produces a phantom empty column. Skip it.
- BOM at the start of an export breaks the first header. Strip \ufeff.
