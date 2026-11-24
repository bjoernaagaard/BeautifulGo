---
name: go-best-practices
description: >-
  Write idiomatic, correct, maintainable Go. Use whenever you write, review, refactor,
  debug, or explain Go code: packages, functions, types, interfaces, errors, goroutines,
  channels, context, generics, iterators, go.mod, or tests. Trigger on Go, golang, .go
  files, gofmt, go vet, go fix, golangci-lint, context, goroutines, or channels, even
  without the words "best practices".
---

# Go best practices

Follow Effective Go, the Go Code Review Comments wiki, and the Google and Uber style
guides. This file holds the rules where they disagree, where models drift, and what
changed through Go 1.27.

## 1. Before you hand back code

From the module root, run:

```bash
go fix -diff ./...      # modern idioms for the go version in go.mod
gofmt -l .              # must print nothing
go vet ./...
golangci-lint run       # the repo's config, else --config <go-review skill>/assets/golangci.yml
go test -race ./...
govulncheck ./...       # when dependencies or security-relevant code changed
```

- Install [golangci-lint](https://golangci-lint.run/docs/welcome/install/) 2.15 or later, and
  install govulncheck with `go install golang.org/x/vuln/cmd/govulncheck@latest`. If a tool
  is missing, say which one and skip it.
- Fix a finding rather than silencing it. To suppress one line, name the linter and the
  reason: `//nolint:gosec // G404: jitter, not a secret`.
- Let `go fix ./...` do modernization instead of editing by hand.
- A race report is a bug, never noise.

## 2. Versions and modules

Read the `go` line in `go.mod` before you use a feature below. A new module declares the
current release, as `go mod init` writes it. A library declares the oldest release it
tests, because the line is a minimum for every importer.

| Since | Use | Instead of |
|---|---|---|
| 1.21 | `min`, `max`, `clear`; `slices`, `maps`, `cmp`; `log/slog`; `context.AfterFunc`, `WithoutCancel` | hand loops, `sort.Slice`, `log.Printf` |
| 1.22 | a fresh loop variable per iteration; `for i := range n`; `http.ServeMux` patterns `"GET /items/{id}"` | `x := x` copies, third-party routers for simple routing |
| 1.23 | iterators: `iter.Seq`, `slices.Collect`, `maps.Keys`, `slices.Sorted` | building a slice only to range over it |
| 1.24 | generic type aliases; `t.Context()`, `b.Loop()`, `t.Chdir`; `os.Root`; `omitzero`; `tool` lines in `go.mod`; `strings.SplitSeq`; `runtime.AddCleanup`; `crypto/rand.Text`; `slog.DiscardHandler` | `context.WithCancel` in tests, `for i := 0; i < b.N; i++`, `tools.go`, `SetFinalizer` |
| 1.25 | `sync.WaitGroup.Go`; `testing/synctest`; `http.CrossOriginProtection`; container-aware `GOMAXPROCS` | `wg.Add(1)` plus `defer wg.Done()`, sleeping in tests, hand-rolled CSRF checks |
| 1.26 | `new(expr)`; `errors.AsType[*T]`; the modernizers in `go fix` | `ptr(v)` helpers, `var target *T; errors.As(err, &target)` |
| 1.27 | generic methods; `encoding/json/v2`; the `uuid` package; the `goroutineleak` profile | free functions that exist only to add a type parameter, third-party UUID modules |

- Pin tools with `go get -tool <path>` and run them with `go tool <name>`.
- Commit `go.sum` and run `go mod tidy` after import changes. Add a `toolchain` line only
  when the build needs a newer toolchain than the `go` line.
- Check the standard library before adding a dependency. Add no framework, ORM, assertion
  library, or dependency-injection container unless the module already uses one. Replace
  `golang.org/x/exp` packages the standard library now provides.

## 3. Names and declarations

- Package names supply context, so don't repeat them: `http.Client`, `user.Load`. No
  `util`, `common`, `helpers`, `models`, or `misc` packages.
- No `Get` prefix on getters. Use `Fetch` or `Load` when the call does I/O.
- Initialisms keep one case: `userID`, `HTTPClient`. Receivers are one or two letters,
  the same on every method.
- Don't shadow predeclared names (`len`, `new`, `min`, `max`, `clear`) or package names.
- An enum is a named type with `iota` constants and a `String` method. Start at
  `iota + 1` when the zero value is never valid. When the zero value is a real state that
  code stores, prints, or compares, such as "not checked yet", name it
  (`StatusUnknown Status = iota`) and never compare against a bare `0`. The parser
  accepts every name that `String` returns.

## 4. Functions and control flow

- **Return early.** Keep the happy path at the left margin, with no `else` after `return`.
- **No Boolean parameters in exported signatures.** Use a named type, an options struct,
  or two functions.
- **Options structs** for three or more optional settings, passed by value, with a zero
  value that means "defaults". Use functional options only in a library whose constructor
  must stay compatible.
- **Check `Close` on anything you wrote to:**

```go
func writeReport(path string, data []byte) (err error) {
	f, err := os.Create(path)
	if err != nil {
		return err
	}
	defer func() { err = errors.Join(err, f.Close()) }()
	_, err = f.Write(data)
	return err
}
```

- **Iterators** (`iter.Seq[T]`) when the caller may stop early or the data is large; stop
  calling `yield` once it returns false. Return a slice when the caller needs `len`,
  indexing, or a second pass.

## 5. Types, interfaces, and generics

- **Accept interfaces, return concrete types.**
- **Declare an interface beside its consumer,** only once a second implementation or a
  real test double exists. Keep it small, and never use a pointer to
  an interface. Application code stays concrete, with no dependency-injection framework.
  Libraries follow the API rules strictly.
- **Receivers:** use pointer receivers when any method needs one, and don't mix kinds on
  one type.
- **Never embed `sync.Mutex` in an exported struct**, because `Lock` joins your API.
- **Strong types for units and IDs:** `time.Duration` and `type OrderID string`.
- **Generics** when several types repeat one algorithm. Don't use type parameters to dodge
  an interface that has methods. Since Go 1.27 a method can take its own type parameters,
  as in `func (l List[T]) Map[U any](f func(T) U) List[U]`. Interface methods still
  can't be generic, and a generic method can't satisfy an interface method.

## 6. Errors and panics

- **Handle an error once.** Return it with context, or log it and stop, never both.
- **Add context the caller lacks**, lowercase, without "failed to", and skip what the
  wrapped error already says, such as the path in an `*fs.PathError` from `os.Open`.
  A parser that reads bytes, such as `json.Unmarshal`, never saw the path, so add it:
  `fmt.Errorf("parse config %s: %w", path, err)`.
- **`%w` makes the cause part of your API.** Use `%v` when the cause is an internal
  detail you may change.
- **Match with `errors.Is` and `errors.AsType`**, never by error text or `==` on a
  wrapped error:

```go
func describe(err error) string {
	if pe, ok := errors.AsType[*fs.PathError](err); ok {
		return "path problem: " + pe.Path
	}
	if errors.Is(err, fs.ErrNotExist) {
		return "missing"
	}
	return "other"
}
```

- **Exported functions return the `error` interface**, never `*MyError`, because a nil
  `*MyError` in an `error` is not `nil`.
- **Ignore an error only with a reason.** Where errcheck reports the call, write
  `//nolint:errcheck // why it is safe`, as on the response body in section 7. Where
  errcheck already exempts it, such as `fmt.Println`, write no directive, because
  nolintlint reports an unused one.
- **No in-band sentinels** such as `-1`, `""`, or `nil, nil` for "not found". Return
  `ok bool` or an error, and pick one for all the lookups on a type.
- **`panic` only for programmer errors**, never for caller input, and never `recover` for
  control flow. `os.Exit` and `log.Fatal` only in `main`, which calls `run() error`.

## 7. Context and concurrency

- **`ctx` is the first parameter** of anything that blocks or does I/O. Never store it in
  a struct or replace the caller's with `context.Background()`. `defer cancel()` after
  every derived context.
- **Context values** carry request-scoped data, never optional parameters.
- **Prefer synchronous APIs** and let the caller add concurrency.
- **Cancellation is not a result.** When `ctx.Err()` is set, return it. Don't record,
  cache, or log the canceled call as an outcome such as "down" or "failed".
- **One deadline per operation.** When one call makes several requests, such as a retry
  or a fallback, bound it with one `context.WithTimeout`.
- **Every goroutine has an owner, a wait, and either a predictable finish or a stop
  signal.** Document when it ends only when the code does not make that evident. Start
  goroutines with `wg.Go`. Use `errgroup` from `golang.org/x/sync` only when you need the
  first error, cancellation of the rest, or `SetLimit`:

```go
func fetchAll(ctx context.Context, urls []string) ([][]byte, error) {
	g, ctx := errgroup.WithContext(ctx)
	g.SetLimit(8)
	bodies := make([][]byte, len(urls))
	for i, u := range urls {
		g.Go(func() error {
			b, err := fetch(ctx, u)
			if err != nil {
				return fmt.Errorf("fetch %s: %w", u, err)
			}
			bodies[i] = b
			return nil
		})
	}
	return bodies, g.Wait()
}

var client = &http.Client{Timeout: 10 * time.Second}

func fetch(ctx context.Context, url string) ([]byte, error) {
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, url, nil)
	if err != nil {
		return nil, err
	}
	resp, err := client.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close() //nolint:errcheck // the result comes from ReadAll, and a Close error cannot change it
	return io.ReadAll(resp.Body)
}
```

- **Locks:** keep the mutex beside the fields it guards, and never call caller code or
  block on I/O while holding it. When a caller needs several values that must agree,
  such as a total and its parts, return them from one method that holds the lock once.
- **Channels:** the sender closes, once. Declare direction in signatures. Buffer size is
  zero or one unless you state a reason. Every blocking send or receive also selects on
  `ctx.Done()`.
- Use typed atomics (`atomic.Int64`) for a lone counter and `sync.OnceValue` for lazy
  initialization. No goroutines in `init`.
- When goroutine counts grow, inspect `pprof.Lookup("goroutineleak")`.

## 8. Data, I/O, and boundaries

- Clone a slice or map at an API boundary when keeping it would share mutable state.
- Sort map keys before output, hashing, or golden files.
- Spans are `time.Duration` and instants are `time.Time`. If a wire format forces a bare
  number, put the unit in the name.
- **JSON:** give every request and response body a struct type, not `map[string]any`.
  Use `omitzero` for structs, `time.Time`, and values whose zero value is meaningful, and
  keep `omitempty` for empty strings, slices, and maps. New code that needs strict decoding uses
  `encoding/json/v2`. Since Go 1.27, `encoding/json` runs on the v2 engine, so don't
  assert on its error text.
- Open files with untrusted names through `os.OpenRoot(dir)`.
- `crypto/rand` for secrets (`rand.Text()` for tokens), `math/rand/v2` for the rest.
- **HTTP servers:** set `ReadHeaderTimeout`, shut down with `srv.Shutdown(ctx)`, route with
  `mux.HandleFunc("GET /items/{id}", h)` and `r.PathValue("id")`, and wrap state-changing
  browser endpoints in `http.NewCrossOriginProtection()`.
- **HTTP clients:** set a timeout, build requests with `http.NewRequestWithContext`, and
  close every response body.
- Read configuration once in `main` and pass it down.
- Never use a cleanup or finalizer for work `Close` should do.

## 9. Logging

- `log/slog` with a constant message and data in attributes:
  `logger.InfoContext(ctx, "order shipped", "order_id", id)`.
- Libraries mostly return errors and don't log.
- Never log secrets. Implement `slog.LogValuer` on types that hold them.
- Tests and benchmarks that don't inspect logs use `slog.New(slog.DiscardHandler)`.

## 10. Tests

- Prefer `package foo_test`, so tests use the public API.
- Table-driven tests with named cases and `t.Run`.
- Failure messages read `Parse(%q) = %v, want %v`. Compare structs with `go-cmp`'s
  `cmp.Diff`, and add no assertion library.
- Use `t.TempDir()`, `t.Setenv`, `t.Cleanup`, and `t.Helper()`.
- Run code that waits on timers inside `synctest.Test`. Keep real network I/O out of the
  bubble, and don't call `t.Run` or `t.Parallel` inside it.
- Test handlers with `httptest`, not a mocked `http.Client`. Prefer a real temp directory or
  in-process server over an interface added for mocking.
- Benchmarks use `for b.Loop()`. Fuzz parsers of untrusted input.

## 11. Documentation and layout

- Every exported name has a doc comment, a full sentence that starts with the name and
  says what the signature can't: errors callers can match, concurrency safety, and
  ownership of returned slices and maps.
- Mark retired APIs with `// Deprecated:`, and add `//go:fix inline` to a one-line
  wrapper so `go fix` rewrites callers.
- Start with one package at the module root, which is `package main` for a single
  command. When a module holds commands beside importable packages, commands go in
  `cmd/<name>/`. Private packages go in `internal/`. Don't create `pkg/` or layer packages such as `services`.
- No package-level variable that code reassigns or mutates after start-up, except a
  private cache behind a lock whose hits and misses callers can't tell apart. No `init`
  side effects beyond standard registration.

## Look up the rest

- Language idioms, embedding, goroutines → `references/effective-go.md`
- The Go team's review checklist → `references/code-review-comments.md`
- Choosing clarity over abstraction, naming, test messages → `references/google-go-style.md`
- Defensive API design, time, goroutine lifetime, performance → `references/uber-go-style.md`
- Pipelines, worker pools, cancellation, shutdown → `references/concurrency-patterns.md`
- What each release from Go 1.21 to 1.27 added, and what `go fix` rewrites → `references/modern-go.md`
- Each rule's id, the tool that checks it, and its source → `references/rules.md`
