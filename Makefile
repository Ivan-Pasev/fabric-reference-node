install:
	pip install -e '.[dev]'

test:
	python -m unittest discover -s tests -v

validate:
	python scripts/validate_schemas.py

verify: test validate

run:
	fabric-reference-node --db ./fabric-reference-node.sqlite --port 8787
