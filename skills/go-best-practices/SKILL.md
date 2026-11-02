---
name: go-best-practices
description: >-
  Write idiomatic, robust, maintainable Go. Use whenever you write, review, refactor,
  debug, or explain Go code: packages, functions, types, interfaces, errors, goroutines,
  channels, context, generics, go.mod, or tests. Trigger on Go, golang, .go files,
  gofmt, go vet, golangci-lint, context, goroutines, or channels, even without the
  words "best practices".
---

# Go best practices

Distilled from Effective Go, the Go Code Review Comments wiki, the Google Go Style
Guide, and the Uber Go Style Guide. Where they disagree, this file chooses and says why.
Read a digest in `references/` only when a task needs its reasoning.

The current floor is Go 1.21 or newer. Use `slog`, `any`, and the `slices`, `maps`, and
`cmp` packages. Check `go.mod` before using a newer API. Do not add a framework, ORM, or
dependency-injection library unless the existing module already uses it.

## 1. Mindset

- Write Go-shaped code. Return errors as values, represent absence with `nil` or the
  comma-ok result, and use small interfaces only where a caller needs one.
- Application code stays direct: concrete types, explicit parameters, and no interface
  created for one implementation. Library code follows the API rules below.
- `gofmt` owns formatting, `go vet` and the configured `golangci-lint` own mechanical
  checks, and review owns design.

## 2. Before handing code back

From the module root, run:

```bash
gofmt -l .
go vet ./...
golangci-lint run
go test ./...
```

Add `-race` when the change touches goroutines or shared state. Fix the finding. A
suppression names one linter and gives its reason: `//nolint:errcheck // reason`.

## 3. Names, declarations, and functions

- Use `MixedCaps` and `mixedCaps`. Keep initialisms consistent: `userID`, `HTTPClient`.
- Do not stutter (`user.Name`, not `user.UserName`) or prefix a getter with `Get`.
- Name packages for what they provide. Avoid `util`, `common`, and `misc`.
- Use short names in small scopes and one- or two-letter receivers. Never use `this`.
- Declare the zero value with `var` and an explicit value with `:=`. Keep scope small.
- Name composite-literal fields. Use `any`, not `interface{}`.
- Do not shadow predeclared names such as `error`, `len`, or `new`.
- Order a file as types, constructors, exported methods, unexported methods, then helpers.
- A function that formats like `fmt.Printf` has a name ending in `f`.
- Return early for errors and uncommon cases. Use a naked return only in a short function
  whose named results are obvious.

## 4. Types and interfaces

- Accept the narrow interface a function needs and return the concrete type.
- Define that interface beside its consumer, not beside its first implementation.
- Do not declare an interface before a second implementation or a real test double needs it.
- Keep interfaces small, normally one to three methods, and use the `er` form for one method.
- Use pointer receivers when a method mutates state, contains synchronization, or wraps a
  large struct. Do not mix receiver forms on one type.
- Do not pass or store pointers to interfaces.
- Verify an important implementation with `var _ Consumer = (*Implementation)(nil)`.
- Use an options struct for several related settings. Use functional options only when
  construction has at least three independent optional settings or must remain extensible.
- Use generics only when several concrete types otherwise repeat the same logic and an
  interface loses needed type information.

## 5. Errors and panics

- Return the `error` interface from an exported function, never a concrete error type.
- Error strings are lowercase and have no trailing punctuation.
- Check every error. If ignoring one is sound, write the reason beside the blank identifier.
- Handle an error once: return it with context or log it at the boundary, not both.
- Wrap with `%w` when the caller may inspect the cause. Use `%v` when exposing that cause
  would make an internal dependency part of the API.
- Use `errors.Is` for sentinels and `errors.As` for typed causes. Do not compare error text.
- A sentinel starts with `Err`. A custom error type ends with `Error`.
- Do not use `-1`, `""`, or another in-band sentinel when an `error` or comma-ok result can
  describe the outcome.
- `panic` reports a programmer bug or impossible state. `main` may exit. Other functions return
  an error. `Must` helpers belong only to known-valid initialization.

## 6. Context and concurrency

- Put `context.Context` first and name it `ctx`. Pass it through; do not store it in a struct.
- Cancel every derived context with `defer cancel()`.
- Every goroutine has an owner, a way to stop, and a way for its caller to wait.
- Do not start goroutines in `init`. Expose `Close`, `Stop`, or `Shutdown` instead.
- Prefer a synchronous function and let its caller add concurrency.
- Use a channel to transfer ownership and a mutex to protect shared state.
- The sender closes its channel, and it closes that channel once. Specify channel direction.
- An unbuffered channel is the default. A buffer larger than one needs a stated reason.
- Use typed atomics in `sync/atomic` for one counter or flag.
- Document concurrency when a read changes state or an API is safe for concurrent callers.

## 7. Data, performance, and boundaries

- A nil slice is empty. Use `len(s) == 0`, and use `make` when capacity is known.
- Copy a slice or map at an API boundary when retaining it would expose mutable shared state.
- Do not copy a value that contains a lock or an atomic.
- Measure before optimizing. Use `strings.Builder` for repeated string construction and
  `strconv` for primitive conversions in a measured hot path.
- Use `time.Time` and `time.Duration`, not bare integers whose unit exists only in a name.
- Use `crypto/rand` for secrets and `defer` to release files, response bodies, rows, and locks.
- Keep `http.Server` shutdown bounded with `Shutdown` and a timeout. Do not read environment
  variables inside request handling; inject configuration from `main`.

## 8. Logging, tests, and documentation

- Use `log/slog` for operational logs. Keep the message stable and put variable data in
  attributes. Never log credentials or personal data.
- Write table-driven tests when cases share one flow. Use `t.Run`, `t.Helper`, and `t.Cleanup`.
- Failure text names the operation, input, actual result, and expected result, with actual
  before expected.
- Test error identity with `errors.Is` or `errors.As`, not error text.
- Use `httptest` and real local handlers for HTTP behavior. Do not add an assertion library
  by default; `go-cmp` is appropriate for structured comparisons.
- Document every exported name with a complete comment beginning with that name.
- Put the package comment directly above the package clause. Add runnable `Example` functions
  for behavior users need to see.

## 9. Final checklist

- Formatting, `go vet`, lint, and tests pass, with `-race` for concurrent changes.
- Errors are checked, intentionally ignored errors have reasons, and wrapping matches the API.
- Context flows from callers, and every goroutine can stop and be awaited.
- Interfaces are small, consumed where they are declared, and not speculative.
- Public behavior has tests for success, failure, and relevant boundaries.
- Exported names have useful documentation.

## References

- `references/effective-go.md`: language idioms, names, interfaces, and concurrency.
- `references/code-review-comments.md`: the Go wiki review checklist.
- `references/google-go-style.md`: readability, package design, and when not to abstract.
- `references/uber-go-style.md`: defensive API, error, time, and concurrency rules.
- `references/concurrency-patterns.md`: goroutine lifetime, channels, mutexes, and shutdown.
