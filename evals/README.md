# Go skills eval

This eval measures how well an agent writes, ports and reviews Go, so that one arm, such
as the skills before a change, after a change, or no skills at all, can be compared with
another. A machine grades every task.

```text
evals/
├── grade.py                 # prepares an arm folder and grades it
├── triggers.json            # 16 requests and the one skill each should load, or none
└── tasks/
    ├── write/<id>/          # prompt.md and cases.json for a new command line program
    ├── port/<id>/           # prompt.md, cases.json, and source/ with the Python to port
    └── review/<id>/         # prompt.md, key.json with the seeded defects, and module/
```

| Task | What it exercises |
|---|---|
| `write/retry-fetch` | HTTP client, retries under one deadline, error matching |
| `write/probe` | goroutines with a limit, one deadline, cancellation that is not an outcome |
| `write/order-check` | strict JSON decoding, error classes mapped to exit codes |
| `write/tally` | the `uuid`, `slices` and `cmp` packages, sorting and aggregation |
| `port/bucket-report` | floor division on negatives, stable sort, code point indexing, dict order, round half to even |
| `review/fleet-monitor` | 13 seeded defects, of which 4 are golangci-lint findings and 9 need a reader |

## Run it

Each prompt holds `{ARM}`. Replace it with the arm folder before you give the prompt to an
agent. The agent sees only the arm folder, never this one.

```bash
python3 evals/grade.py --prepare /tmp/arm-skills
# give each tasks/*/*/prompt.md to the agent, with {ARM} set to /tmp/arm-skills
python3 evals/grade.py --arm /tmp/arm-skills --lint-config skills/go-review/assets/golangci.yml
```

`--prepare` creates `write/<id>/`, `port/<id>/` and `review/<id>/` in an empty or new
folder, and copies in the Python source and the review module. It never copies
`cases.json`, `key.json` or a reference solution.

`--arm` needs Go and golangci-lint, and a folder that `--prepare` made. It exits 1 when the
folder or one of its task folders is missing. It starts a local HTTP server for the cases that make
requests, and prints one line per task, then one JSON object as its last line:

| Key | Meaning |
|---|---|
| `buildFailures` | written and ported modules that are missing, fail `go build -race`, or give no golangci-lint report |
| `casesPassed`, `casesTotal` | write task cases with the expected stdout and exit code |
| `lintIssues` | golangci-lint issues in the written and ported modules, with the given config |
| `fixDiffLines` | changed lines that `go fix -diff ./...` proposes in those modules |
| `portPassed`, `portTotal` | port task cases with the expected stdout and exit code |
| `reviewFound`, `reviewTotal` | seeded defects that some finding in `findings.json` matches |
| `reviewFalsePositives` | findings that match no seeded defect |

A finding matches a defect when its file is the same, its line is within 3 lines of the
defect's range, and its `summary` is a non-empty string. A case passes when the exit code
matches and stdout matches exactly, or as parsed JSON when the case sets
`"stdoutFormat": "json"`. The port cases compare the Go program with fixed expected
outputs in `cases.json`, which were produced by running the Python source on each case.
Grading never runs the Python.

The grader prints a problem on stderr and exits 1, after the JSON object, when a
`findings.json` is not a JSON list or golangci-lint gives no report for a module. Such a
findings file scores no findings. A missing `findings.json` scores no findings without a
problem. Otherwise the grader exits 0.

`triggers.json` is input for a harness that records which skill an agent loads for each
request. `grade.py` does not read it.
