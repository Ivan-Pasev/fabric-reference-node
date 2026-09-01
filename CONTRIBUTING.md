# Contributing

Thanks for helping make governed agent infrastructure more inspectable and interoperable.

## Development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
python -m unittest discover -s tests -v
python scripts/validate_schemas.py
```

## Good first contributions

- additional adversarial fixtures;
- policy-as-code adapters;
- verifiable-credential authority adapters;
- MCP/A2A integration examples;
- provenance export formats;
- fuzz/property tests;
- threat-model improvements;
- reproducible performance baselines;
- documentation and SDK examples.

## Pull request expectations

A PR that changes semantics should include:

- the invariant or problem being addressed;
- tests that fail before and pass after the change;
- claim-boundary impact;
- migration impact if a schema/API changes;
- no hidden authority promotion.

Avoid combining large terminology rewrites with behavior changes.
