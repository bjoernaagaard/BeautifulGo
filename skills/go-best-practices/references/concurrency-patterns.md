# Go concurrency patterns (digest)

Source: https://go.dev/blog/pipelines, https://go.dev/blog/context,
https://pkg.go.dev/golang.org/x/sync/errgroup, https://go.dev/blog/synctest, and the
concurrency section of https://go.dev/doc/effective_go. The two blog posts on pipelines and
context are from 2014 and 2016. Effective Go says "Do not communicate by sharing memory;
instead, share memory by communicating." Read this digest before you add a goroutine, a
pipeline, a worker pool, or a background loop, and before you write a test that waits on time.
Where a source predates a newer release, the section says what changed.

## Start synchronous

- Write the function so it does its work and returns. Let the caller decide to run it in a
  goroutine. A function that starts a goroutine and returns hides a lifetime the caller cannot
  see or stop.

## Goroutine lifetime

- Every goroutine has an owner, a way to be told to stop, and a place where its end is awaited.
  Fire-and-forget goroutines leak and lose errors.
- Start goroutines with `sync.WaitGroup.Go` (Go 1.25) or `errgroup.Group.Go`. Both pair the
  start with the wait. Before 1.25 the pattern was `wg.Add(1)` and `defer wg.Done()` inside
  the goroutine, and forgetting either one hung or raced. `go fix` rewrites the old form.
- The function passed to `wg.Go` must not panic. It cannot return an error, so use `errgroup`
  when the work can fail.
- Since Go 1.22 each loop iteration has its own variable, so a goroutine started in a loop
  captures the right value. The older `x := x` copy is no longer needed.
- Never start goroutines in `init` or in a package-level variable. Expose `Start` and `Close`
  or take a context.
- A goroutine blocked forever on a channel is a leak. Since Go 1.27 the `goroutineleak` profile
  (`pprof.Lookup("goroutineleak")`, or `/debug/pprof/goroutineleak`) reports goroutines blocked
  on channels, locks, or condition variables that nothing can reach any more. It can miss a
  leak when the primitive is reachable from a global or a runnable goroutine.

```go
func runAll(jobs []func()) {
	var wg sync.WaitGroup
	for _, job := range jobs {
		wg.Go(job)
	}
	wg.Wait()
}
```

## Channels

- The sender closes a channel, once. A receiver never closes. Closing is a signal that no more
  values come. It is not needed to free the channel.
- Receiving from a closed channel returns the zero value at once. Use `v, ok := <-ch` or
  `for v := range ch` to see the end.
- Declare direction in signatures: `<-chan T` for receive only, `chan<- T` for send only.
- Use no buffer, or a buffer of one, unless you can say why a larger number is right. A buffer
  hides a slow consumer until memory runs out.
- Every send and receive that can block also selects on `ctx.Done()`. Otherwise the goroutine
  outlives the request.

## Pipelines

The pipelines post defines a pipeline as stages connected by channels. Each stage receives
from an inbound channel, does work, and sends on an outbound channel. The first stage is a
source and the last is a sink.

- A stage closes its outbound channel when its inbound channel is closed or when it stops.
  Use `defer close(out)` at the top of the stage goroutine.
- A stage keeps receiving until the inbound channel closes or it is told to stop. If a
  downstream stage quits early, upstream senders block forever. The post first uses a `done`
  channel for this. Today, pass a `context.Context` and select on `ctx.Done()` in every send.
- Fan out by starting several goroutines reading the same inbound channel. Fan in by merging
  their outputs into one channel, with a `WaitGroup` that closes the merged channel after
  every worker is done.
- Prefer a plain loop over a pipeline when there is one step. Stages cost goroutines and
  hand-offs.
- Since Go 1.23, an iterator (`iter.Seq`) is often simpler than a channel for a single
  producer and consumer in one goroutine, because it needs no goroutine and no close. Use
  channels when the stages truly run at the same time.

## Context

The context post introduced `context.Context` for cancellation, deadlines, and request-scoped
values across API boundaries and goroutines.

- Pass `ctx` as the first parameter, named `ctx`, to every function that blocks, does I/O, or
  calls something that does. Do not store it in a struct, except in a type that represents one
  call such as an `*http.Request`.
- Always call the cancel function from `WithCancel`, `WithTimeout`, and `WithDeadline`, usually
  with `defer cancel()`. Skipping it leaks the timer and the child registration.
- Cancel flows down to children, never up. A child can have a shorter deadline than its
  parent but not a longer one.
- `ctx.Err()` returns `context.Canceled` or `context.DeadlineExceeded`. `context.Cause(ctx)`
  returns the reason given to `WithCancelCause` or `WithTimeoutCause` (Go 1.20 and 1.21).
- Use `context.WithoutCancel` (Go 1.21) for work that must finish after the request ends, such
  as an audit write. It keeps the values and drops the cancellation.
- Use `context.AfterFunc(ctx, f)` (Go 1.21) to run cleanup when a context ends, instead of a
  goroutine that waits on `ctx.Done()`. The returned `stop` function cancels it.
- Use `t.Context()` (Go 1.24) in tests for a context that ends just before cleanup runs.
- Context values carry request-scoped data such as a trace ID, not optional parameters. Key
  them with an unexported type, and expose typed accessor functions.

## errgroup

`golang.org/x/sync/errgroup` runs a group of goroutines that work on parts of one task.

- `g, ctx := errgroup.WithContext(ctx)` returns a group and a context that is canceled when a
  function passed to `g.Go` returns a non-nil error or when `g.Wait` returns. Use the derived
  `ctx` inside the functions.
- `g.Wait()` blocks until all functions return and gives the first non-nil error. Later errors
  are dropped. Join your own errors if you need all of them.
- `g.SetLimit(n)` caps the number of active goroutines, and `g.Go` blocks when the limit is
  reached. Call it before any `Go`. Use it instead of a hand-made semaphore or worker pool for
  a known list of jobs.
- `g.TryGo(f)` starts the function only when a slot is free and reports whether it did.
- Write results into a slot you own, such as `results[i]`, or send them on a channel the group
  waits for. Do not append to a shared slice without a lock.

```go
func fetchAll(ctx context.Context, urls []string, get func(context.Context, string) ([]byte, error)) ([][]byte, error) {
	g, ctx := errgroup.WithContext(ctx)
	g.SetLimit(8)
	out := make([][]byte, len(urls))
	for i, u := range urls {
		g.Go(func() error {
			b, err := get(ctx, u)
			if err != nil {
				return fmt.Errorf("fetch %s: %w", u, err)
			}
			out[i] = b
			return nil
		})
	}
	return out, g.Wait()
}
```

## Shared state

- Use a mutex when goroutines share state, and a channel when ownership of a value moves. Pick
  the one that makes the code shorter and easier to check.
- Keep the mutex next to the fields it guards, and say so in a comment. Keep critical sections
  short. Do not call a caller's function, send on a channel, or do I/O while holding a lock.
- Never copy a value that holds a `sync.Mutex`, `WaitGroup`, or atomic. `go vet` copylocks
  finds it. Use pointer receivers on such types.
- Use `sync/atomic` typed values (`atomic.Int64`, `atomic.Bool`, `atomic.Pointer[T]`) for a
  single counter or flag. Prefer them to the old `atomic.AddInt64(&x, 1)` calls.
- Run `go test -race` on every package with goroutines. A race report is a bug.

## Testing concurrent code

The synctest post (Go 1.24 experiment, standard in Go 1.25) removes sleeps and flakiness from
tests that depend on time.

- Wrap the test body in `synctest.Test(t, func(t *testing.T) { ... })`. Goroutines started
  inside run in a bubble with a fake clock that starts at midnight UTC on 2000-01-01.
- Time moves only when every goroutine in the bubble is durably blocked, such as on a
  `time.Sleep`, a channel, or a `sync.WaitGroup.Wait`. Then the clock jumps to the next timer.
  A test of a one-hour timeout takes microseconds.
- `synctest.Wait()` returns when every other goroutine in the bubble is durably blocked. Call
  it before you assert on state that a goroutine should have reached.
- `Test` waits for all bubble goroutines to exit and fails with a deadlock panic if they are
  all blocked and no timer is pending. A goroutine leak in the code under test fails the test.
- Do not sleep to wait for a goroutine in a test. Use `synctest.Wait()` or a channel.

```go
func TestTimeout(t *testing.T) {
	synctest.Test(t, func(t *testing.T) {
		ctx, cancel := context.WithTimeout(t.Context(), time.Hour)
		defer cancel()
		time.Sleep(time.Hour)
		synctest.Wait()
		if ctx.Err() != context.DeadlineExceeded {
			t.Fatalf("ctx.Err() = %v, want DeadlineExceeded", ctx.Err())
		}
	})
}
```

## Shutdown

- Stop accepting work, cancel the shared context, wait for workers with a deadline, then
  release resources. Use `srv.Shutdown(ctx)` with a timeout for an `http.Server`.
- `signal.NotifyContext(ctx, os.Interrupt)` gives a context that ends on a signal. Call its
  stop function.
- Have `main` call `run(ctx) error` so deferred cleanup runs before `os.Exit`.
