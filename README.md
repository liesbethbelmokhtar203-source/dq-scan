<div align="center">

# dq-scan

**Scan a table and print the data-quality findings a human would have to eyeball otherwise.**

[![license](https://img.shields.io/badge/license-MIT-green?style=flat-square)](LICENSE)

</div>

## About

The scan is deliberately read-only and single-pass: null density per
column, cardinality, duplicate keys, and values that fall outside the observed
range of a numeric column. It reports findings with a severity and never
"fixes" anything.

## Quick start

```bash
git clone https://github.com/liesbethbelmokhtar203-source/dq-scan
cd dq-scan
python3 -m unittest -v
```

## Configuration

| Key | Description |
| --- | --- |
| `--table` | table or CSV to scan |
| `--null-threshold` | fraction of nulls that counts as a finding |
## Roadmap

- [ ] CSV and Postgres sources
- [ ] JSON report schema
- [ ] Threshold configuration file

## Contributing

Issues and pull requests are welcome. Please keep changes small and focused,
and add a test for any behaviour change — every repository here ships with a
runnable test suite and no third-party dependencies, so CI is just
`python3 -m unittest` / `bash test_*.sh`.

## License

[MIT](LICENSE)
