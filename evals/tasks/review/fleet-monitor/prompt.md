{ARM}/review/fleet-monitor/ holds a Go module, a library package named fleet that checks the health of HTTP endpoints. The Go toolchain on this machine is 1.27. Review it, and list every problem you would ask its author to fix.

Write the list to {ARM}/review/fleet-monitor/findings.json as a JSON array with one object per problem:

```json
[{"file": "monitor.go", "line": 42, "summary": "one sentence that says what is wrong"}]
```

"file" is the path relative to {ARM}/review/fleet-monitor/, and "line" is the line where the problem is. Do not change any other file in that folder.
