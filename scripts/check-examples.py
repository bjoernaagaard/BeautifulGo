#!/usr/bin/env python3
"""Type-check every ```go block under skills/ as its own package."""
import re
import subprocess
import sys
import tempfile
from pathlib import Path

GOIMPORTS = "golang.org/x/tools/cmd/goimports@v0.52.0"
REQUIRES = ["golang.org/x/sync@v0.25.0", "github.com/google/go-cmp@v0.7.0"]

root = Path(__file__).resolve().parents[1]
examples = []
for doc in sorted((root / "skills").rglob("*.md")):
    if "assets" in doc.parts:
        continue
    for block in re.findall(r"^```go\n(.*?)^```", doc.read_text(), re.S | re.M):
        examples.append((doc.relative_to(root), block))

if not examples:
    sys.exit("no Go examples found")


def run(*args, cwd):
    result = subprocess.run(args, cwd=cwd, text=True, capture_output=True)
    if result.returncode != 0:
        sys.exit(f"{' '.join(args)} failed:\n{result.stdout}{result.stderr}")


with tempfile.TemporaryDirectory(prefix="beautifulgo-examples-") as temp:
    module = Path(temp)
    (module / "go.mod").write_text("module examplecheck\n\ngo 1.27\n")
    run("go", "get", *REQUIRES, cwd=module)
    owners = {}
    for number, (doc, block) in enumerate(examples, 1):
        name = f"ex{number:03d}"
        owners[name] = doc
        (module / name).mkdir()
        source = block if block.startswith("package ") else f"package {name}\n\n{block}"
        (module / name / "example.go").write_text(source)
    unformatted = subprocess.run(["gofmt", "-l", "."], cwd=module, text=True, capture_output=True).stdout.split()
    if unformatted:
        sys.exit("not gofmt-clean: " + ", ".join(f"{owners[Path(f).parent.name]} ({Path(f).parent.name})" for f in unformatted))
    run("go", "run", GOIMPORTS, "-w", ".", cwd=module)
    run("go", "mod", "tidy", cwd=module)
    result = subprocess.run(["go", "vet", "./..."], cwd=module, text=True, capture_output=True)
    if result.returncode != 0:
        for name, doc in owners.items():
            result.stderr = result.stderr.replace(f"{name}/example.go", f"{doc} ({name})")
        sys.exit(result.stderr)

print(f"type-checked {len(examples)} Go examples")
