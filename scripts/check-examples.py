#!/usr/bin/env python3
"""Type-check every ```go block under skills/ as its own package."""
import re
import subprocess
import sys
import tempfile
from pathlib import Path

GOIMPORTS = "golang.org/x/tools/cmd/goimports@v0.52.0"
REQUIRES = ["golang.org/x/sync@v0.25.0", "github.com/google/go-cmp@v0.7.0"]


def run(*args, cwd):
    result = subprocess.run(args, cwd=cwd, text=True, capture_output=True)
    if result.returncode != 0:
        sys.exit(f"{' '.join(args)} failed:\n{result.stdout}{result.stderr}")


def main():
    root = Path(__file__).resolve().parents[1]
    examples = []
    for doc in sorted((root / "skills").rglob("*.md")):
        if "assets" in doc.parts:
            continue
        for block in re.findall(r"^```go\n(.*?)^```", doc.read_text(), re.S | re.M):
            examples.append((doc.relative_to(root), block))

    if not examples:
        sys.exit("no Go examples found")

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
        # goimports guesses imports for names the block uses, so reject guesses outside the
        # standard library's current packages and the modules this check requires.
        allowed = ("golang.org/x/sync/", "github.com/google/go-cmp/")
        rejected = {"math/rand": "math/rand/v2"}
        listing = subprocess.run(["go", "list", "-f", '{{.Dir}}|{{join .Imports " "}}', "./..."],
                                 cwd=module, text=True, capture_output=True, check=True).stdout
        for line in listing.splitlines():
            directory, _, imports = line.partition("|")
            name = Path(directory).name
            for path in imports.split():
                third_party = "." in path.split("/")[0] and not path.startswith(allowed)
                if third_party or path in rejected:
                    hint = f"; use {rejected[path]}" if path in rejected else ""
                    sys.exit(f"{owners[name]} ({name}): goimports chose {path}{hint}; import it explicitly")
        run("go", "mod", "tidy", cwd=module)
        result = subprocess.run(["go", "vet", "./..."], cwd=module, text=True, capture_output=True)
        if result.returncode != 0:
            for name, doc in owners.items():
                result.stderr = result.stderr.replace(f"{name}/example.go", f"{doc} ({name})")
            sys.exit(result.stderr)

    print(f"type-checked {len(examples)} Go examples")


if __name__ == "__main__":
    main()
