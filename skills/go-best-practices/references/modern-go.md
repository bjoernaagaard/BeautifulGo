# Modern Go, 1.21 to 1.27 (digest)

Source: https://go.dev/doc/go1.21 through https://go.dev/doc/go1.27 (the release notes), checked
with `go doc` and `go tool fix help`. Each release adds a few
things that change how you write everyday code. Read this when the `go` line in `go.mod`
moves up, when you review code that looks older than the toolchain, or when you pick between
a library function and a hand-written loop. Every section lists "use X instead of Y".

## Using this digest

- The `go` line decides which language features compile, and `go vet` (run by `go test` since
  Go 1.27) reports library symbols newer than the line. `go fix` respects it.
  Raise the line first, then run `go fix -diff ./...`, read the diff, and apply it.
- A library declares the oldest release it tests against. An application declares the
  current release.
- Run `go test` after every `go fix`. Some fixes enable others, so run it twice.

## Go 1.21

- Use the built-ins `min`, `max`, and `clear` instead of `if` ladders and delete loops.
  `clear(m)` empties a map. `clear(s)` zeroes a slice but keeps its length.
- Use `slices` (`Contains`, `Index`, `Sort`, `SortFunc`, `BinarySearch`, `Reverse`, `Max`,
  `Clone`, `Equal`, `Insert`, `Delete`, `Compact`) instead of `sort.Slice` and hand loops.
- Use `maps` (`Clone`, `Copy`, `DeleteFunc`, `Equal`) instead of copy loops.
- Use `cmp.Compare` and `cmp.Ordered` instead of local ordered constraints and
  `golang.org/x/exp/constraints`.
- Use `log/slog` for structured logs instead of `log.Printf` with formatted data.
- Use `context.WithoutCancel` for work that must outlive a request, `context.AfterFunc` to
  run cleanup when a context ends, and `context.WithTimeoutCause` or `WithDeadlineCause`
  when the reason for the timeout matters.
- Use `sync.OnceFunc`, `sync.OnceValue`, and `sync.OnceValues` instead of a `sync.Once` plus
  a result variable.
- The `go` line is now a strict minimum. A toolchain older than the line refuses to build
  and can download the right one (the `toolchain` line).

## Go 1.22

- Each loop iteration has its own variable. Delete `x := x` and `tc := tc` copies. This
  applies only when the module's `go` line is 1.22 or higher. The `forvar` analyzer removes
  the copies.
- Use `for i := range n` instead of `for i := 0; i < n; i++`. The `rangeint` analyzer does it.
- Use `net/http.ServeMux` patterns such as `"GET /items/{id}"`, `"/files/{path...}"`, and
  `"/{$}"`, and read values with `r.PathValue("id")`. A third-party router is no longer
  needed for simple routing.
- Use `math/rand/v2` instead of `math/rand`. It has `rand.N`, `rand.IntN`, and no global seed.
  Use `crypto/rand` for anything secret.
- Use `cmp.Or(a, b, c)` to pick the first non-zero value instead of a chain of `if`s.

## Go 1.23

- Range over functions. A function of type `iter.Seq[V]` or `iter.Seq2[K, V]` can be used
  in `for ... range`. Return an iterator when callers stream or may stop early. Return a
  slice when callers need `len`, indexing, or a second pass.
- Use `slices.Collect`, `slices.Sorted`, `slices.SortedFunc`, `slices.Values`, `slices.All`,
  `slices.Backward`, `slices.Chunk`, `maps.Keys`, `maps.Values`, `maps.All`, and
  `maps.Collect` instead of building temporary slices.
- Use `slices.Sorted(maps.Keys(m))` instead of collecting keys and sorting them by hand.
- Timers and tickers: an unreferenced `Timer` or `Ticker` is now garbage collected without
  `Stop`, and the channel is unbuffered, so `Reset` and `Stop` never leave a stale value.
  Delete the drain-the-channel code before `Reset`. In Go 1.27 this holds for every module;
  before 1.27 it applied only when the `go` line was 1.23 or higher.

## Go 1.24

- Generic type aliases are fully supported since Go 1.24, and a module needs go 1.23 or higher
  to declare one: `type Set[T comparable] = map[T]struct{}`.
- Use `testing.T.Context()` (and `B.Context`) instead of `context.WithCancel` plus
  `t.Cleanup(cancel)`. The context is canceled just before cleanup functions run. The
  `testingcontext` analyzer rewrites the `defer cancel()` form only, so edit the
  `t.Cleanup(cancel)` form by hand.
- Use `for b.Loop() { ... }` instead of `for i := 0; i < b.N; i++`. Setup before the loop is
  not timed and the compiler keeps the loop body alive.
- Use `t.Chdir(dir)` instead of `os.Chdir` with manual restore.
- Use `omitzero` instead of `omitempty` on struct, `time.Time`, and other fields where the
  zero value is the thing to omit. A type with an `IsZero() bool` method is honored.
- Use `os.Root` (`os.OpenRoot(dir)`) to open files by untrusted names without escaping the
  directory through `..` or symlinks.
- Use `strings.SplitSeq`, `strings.FieldsSeq`, `strings.Lines`, and the `bytes` versions in a
  `for range` instead of `strings.Split` when you only iterate. The `stringsseq` analyzer
  does it.
- Use `runtime.AddCleanup(ptr, cleanup, arg)` instead of `runtime.SetFinalizer`. It allows
  several cleanups per object and does not delay freeing the object. Use `weak.Make` for a
  pointer that must not keep an object alive.
- Use a `tool` directive in `go.mod` (`go get -tool pkg`, `go tool name`) instead of a
  `tools.go` file with blank imports.

## Go 1.25

- Use `wg.Go(func() { ... })` instead of `wg.Add(1)`, `go func() { defer wg.Done() ... }()`.
  The function must not panic. The `waitgroupgo` analyzer rewrites it, and `go vet` reports
  `Add` called inside the goroutine.
- Use `testing/synctest` (`synctest.Test(t, func(t *testing.T) { ... })`) instead of real
  sleeps and flaky timeouts. Inside the bubble the clock is fake and `synctest.Wait()` waits
  until every other goroutine in the bubble is durably blocked. The Go 1.24 `synctest.Run` experiment is
  gone.
- `GOMAXPROCS` follows the cgroup CPU limit on Linux and updates when the limit changes.
  Delete `automaxprocs`. Setting `GOMAXPROCS` yourself turns this off.
- Use `http.NewCrossOriginProtection()` to reject cross-site browser requests that change
  state instead of a hand-written CSRF check.
- `encoding/json/v2` is available behind `GOEXPERIMENT=jsonv2`. Use 1.27 for the final form.

## Go 1.26

- `new` takes an expression: `new(10)`, `new("x")`, `new(time.Second)`. Delete `ptr(v)` and
  `intPtr` helpers. The `newexpr` analyzer rewrites calls to such helpers.
- Use `errors.AsType[*T](err)` instead of `var target *T; errors.As(err, &target)`. It is
  type safe, allocates less, and fails to compile when `T` is not an error. The
  `errorsastype` analyzer rewrites it.
- A generic type may refer to itself in its type parameter list, so recursive constraints
  such as `type Adder[A Adder[A]] interface { Add(A) A }` work (Go 1.26 lifted the
  restriction, and the compiler does not check the go line for it).
- `go fix` is rewritten as the place for modernizers and the `//go:fix inline` directive.
  Run `go fix -diff ./...` on every upgrade. The old obsolete fixers are removed.
- Use `testing.T.ArtifactDir()` to write files a test produces (logs, diffs, screenshots)
  instead of `t.TempDir()` when you want to keep them. Run `go test -artifacts` to save them in `-outputdir`.

## Go 1.27

- Methods can declare their own type parameters: `func (l List[T]) Map[U any](f func(T) U) List[U]`.
  Use them instead of a free function that exists only to add a type parameter. A generic
  method cannot satisfy an interface method, and an interface method cannot be generic.
- A struct literal may use any valid field selector as a key, including a promoted field of an
  embedded struct. The `embedlit` analyzer simplifies the old nested form.
- Use `encoding/json/v2` and `encoding/json/jsontext` for new code that needs strict
  decoding. Defaults reject invalid UTF-8 and duplicate names. Options such as
  `json.RejectUnknownMembers(true)` replace `Decoder.DisallowUnknownFields`.
- `bytes.CutLast` and `strings.CutLast` split around the last separator, replacing
  `LastIndex` plus slicing.
- `encoding/json/v2` marshals a nil slice as `[]`, not `null`, unless you pass
  `json.FormatNilSliceAsNull(true)`.
- `encoding/json` now runs on the v2 engine, so decoding is faster. Do not match on its error
  text.
- Use the `uuid` package (`uuid.New`, `uuid.Parse`) instead of a third-party UUID module.
- Use the `goroutineleak` profile (`pprof.Lookup("goroutineleak")` or
  `/debug/pprof/goroutineleak`) to find goroutines blocked forever on unreachable channels and
  locks. It can miss leaks that hang on a global or a runnable goroutine.
- `go test` runs the `stdversion` vet check by default, so a file that uses an API newer than
  its `go` line fails the test run.

```go
type List[T any] []T

func (l List[T]) Map[U any](f func(T) U) List[U] {
	out := make(List[U], 0, len(l))
	for _, v := range l {
		out = append(out, f(v))
	}
	return out
}

func headAndExt(name string) (string, string) {
	head, ext, _ := strings.CutLast(name, ".")
	return head, ext
}
```

## Analyzers in `go fix`

Run `go fix -diff ./...` to preview and `go fix ./...` to apply. All analyzers run by default,
and the fixes respect the `go` line and build tags. Run `go tool fix help` for the current list,
and `go tool fix help NAME` for what one analyzer checks or rewrites.
