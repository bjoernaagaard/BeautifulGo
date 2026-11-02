# Concurrency patterns

Read this before adding a worker, pipeline, or background loop.
Sources: Effective Go and Go Code Review Comments.

- Start with one synchronous function and add goroutines at the caller.
- Pass `ctx` into every blocking operation and select on `ctx.Done()`.
- Use `errgroup` when several operations return errors and one failure cancels the rest.
- Use `sync.WaitGroup` when the caller only needs completion.
- Close channels from the sender side only.
- Keep mutex sections short and never hold one across a caller-supplied callback.
