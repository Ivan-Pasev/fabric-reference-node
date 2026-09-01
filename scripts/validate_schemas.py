from pathlib import Path
import json
from jsonschema import Draft202012Validator

root = Path(__file__).resolve().parents[1] / "schemas"
count = 0
for path in sorted(root.glob("*.json")):
    obj = json.loads(path.read_text())
    # OpenAPI itself is not a JSON Schema document.
    if path.name == "openapi.json":
        assert obj.get("openapi", "").startswith("3.1")
        print(f"PASS {path.name}: OpenAPI {obj['openapi']}")
        count += 1
        continue
    if "$schema" in obj:
        Draft202012Validator.check_schema(obj)
        print(f"PASS {path.name}: Draft 2020-12 schema")
        count += 1
    else:
        print(f"INFO {path.name}: contract JSON (not a schema)")
print(f"validated {count} machine-readable contracts")
