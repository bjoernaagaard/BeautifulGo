---
name: go-review
description: >-
  Review existing Go code for correctness, API design, errors, concurrency, and
  maintainability. Use for a review, audit, critique, grade, or check of a .go file,
  package, module, diff, or pull request, including gofmt, go vet, and golangci-lint
  output. The report cites every finding and shows its fix.
---

# Go review

Review against `go-best-practices` and report what to change. Do not rewrite the code
unless the user asks for the change.

## 1. Set the scope

- Review the file, package, or diff the user named. For a diff, inspect the enclosing
  function or declaration, not only the changed hunk.
- Read the `go` line in `go.mod` before recommending a newer API.
- Treat a published library strictly. Favor direct concrete code in an application.
- State those assumptions at the top of the report.

## 2. Run the tools

From the module root, run:

```bash
gofmt -l .
go vet ./...
golangci-lint run
go test ./...
```

Use `go test -race ./...` when concurrency is in scope. Group repeated findings, ignore
pedantic noise, and say which command could not run.

## 3. Look in this order

**Correctness**

- A reachable panic, unchecked type assertion, nil-map write, or missing length check.
- An ignored actionable error, an error returned without its cause, or an error both
  logged and returned.
- `%s` or `%v` where `%w` is required, or `%w` where it exposes an internal dependency.
- A data race, copied lock, leaked goroutine, or missing `WaitGroup` or `errgroup` wait.
- A lost `cancel`, request context replaced by `context.Background`, or blocked shutdown.
- A file, row set, or response body closed late or not closed at all.

**API and design**

- A public library error that callers cannot inspect safely, or a concrete error type
  returned directly.
- A speculative interface, pointer to an interface, or large interface with one caller.
- A Boolean parameter that selects distant behavior.
- A stuttering name, `Get` prefix, mixed receivers, or leaked third-party type.
- Context stored in a struct or omitted from a blocking function.

**Tests and documentation**

- Behavior without tests, tests coupled to implementation details, or assertions that
  compare error strings.
- Exported API without a useful doc comment.
- Missing race coverage for concurrent behavior.

## 4. Write the report

Use the sections in `assets/review-template.md`.

- **Must fix:** a bug, race, leak, reachable panic, swallowed error, or breaking API mistake.
- **Should fix:** code that works but makes errors, tests, or maintenance materially worse.
- **Consider:** naming and local polish.
- Cite `file:line`, or `whole file` when there is no line.
- Name the rule and its source, such as `go-best-practices`, `errorlint`, or `go vet`.
- Show only the changed lines in the fix.
- Group repeated findings and preserve deliberate documented behavior.
- Include at least two specific things the code already does well.

## 5. Offer lint configuration

If the module has no `.golangci.yml`, point to `lints/golangci.yml` in this project.
Name two or three findings from the review that the configuration would catch.
