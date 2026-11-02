#!/usr/bin/env python3
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

root = Path(__file__).resolve().parents[1]
examples = []
for skill in (root / "skills").glob("*/SKILL.md"):
    text = skill.read_text()
    for index, block in enumerate(re.findall(r"```go\n(.*?)```", text, re.S), 1):
        examples.append((skill, index, block))

if not examples:
    print("no Go examples found")
    sys.exit(0)

with tempfile.TemporaryDirectory(prefix="beautifulgo-examples-") as temp:
    module = Path(temp)
    (module / "go.mod").write_text("module examplecheck\n\ngo 1.27\n")
    source = ["package examplecheck"]
    for number, (_, _, block) in enumerate(examples, 1):
        source.append(f"func example{number}() {{\n{block}\n}}")
    (module / "examples.go").write_text("\n\n".join(source) + "\n")
    result = subprocess.run(["gofmt", "-e", str(module / "examples.go")], text=True, capture_output=True)
    if result.returncode != 0:
        print(result.stderr, file=sys.stderr)
        sys.exit(result.returncode)

print(f"formatted {len(examples)} Go examples")
shutil.rmtree(temp, ignore_errors=True)
