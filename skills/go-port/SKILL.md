---
name: go-port
description: >-
  Port C, C++, Python, Java, JavaScript, TypeScript, Rust, or older Go into idiomatic
  Go while preserving observable behavior. Use for port, translate, convert, migrate,
  rewrite, or modernize requests. Port tests first and prove the result with gofmt,
  go vet, and go test.
---

# Go port

Write the Go a Go developer would write for the same observable behavior. Do not
transliterate the source language's structure.

## 1. Record the behavior

Read the implementation, its tests, and its callers. List every public operation, its
inputs and outputs, failure behavior, ordering, ties, empty input, case, whitespace, and
numeric limits. Keep an unclear or buggy behavior and flag it in `PORTING.md`.

## 2. Port the tests first

Translate each source test into a Go test before writing its implementation. Use the
source test name in the Go test name. If no test exists, write a characterization test
from the behavior list. Run the tests and keep them failing until the implementation is
ported. Do not add stubs merely to make the build pass.

## 3. Map the source into Go

Use `go-best-practices` for the resulting style.

- C and C++ ownership becomes Go values and garbage-collected memory. Use `Close` only
  for real resources.
- `NULL` and `None` become `nil` or a comma-ok result.
- Error codes, exceptions, and thrown values become `error` values.
- Closed sets of strings become typed constants or a named type with a parser.
- Records become structs. Ordered maps remain ordered with an explicit slice when order
  is observable.
- Pointer-plus-length data becomes a slice. Fixed buffers grow unless the limit itself
  is observable behavior.
- Rust `Result` and `Option` become `error` and `nil` or comma-ok results. Do not copy
  lifetimes, ownership annotations, or `unsafe` into the port.
- Java streams and utility classes become slices, `range`, and package functions.
- Replace `io/ioutil`, `interface{}`, and old context imports when modernizing Go.

## 4. Use jscpd as a map

The installed command is `jscpd` 5.4.2. Its similarity report does not prove behavior.
Run the same paths, options, and model every time:

```bash
jscpd --compare source/ target/
jscpd --compare source/ target/ -r json -o .jscpd-compare --silent
```

Console, console-full, JSON, and Markdown are the verified compare reporters. Do not
claim an HTML compare report. Start with the source and then the target. Ignore vendored
dependencies and build output. Port tests before code, then port functions whose
callees already exist. A `high` pair only says two functions look alike. `go test` and
direct comparison decide whether they behave alike.

Do not use jscpd dead-code detection for Go. It does not support Go.

## 5. Keep the port proportionate

Match realistic and relevant edge-case inputs, not every exotic input. Use `strconv`,
`strings`, `time`, and `unicode` instead of reimplementing the source runtime. Keep the
source algorithm unless it has a demonstrated performance or correctness problem. Record
every deliberate difference.

## 6. Verify

Run:

```bash
gofmt -l .
go test ./...
go vet ./...
```

Run `golangci-lint run` when configuration exists, and `go test -race ./...` when the
port adds goroutines. Compare the port and source on the same inputs whenever both can
run. Every ported test must pass.

## 7. Write PORTING.md

Include the API mapping, test mapping, deliberate differences, preserved quirks, and the
exact commands and results. State plainly when a command could not run.
