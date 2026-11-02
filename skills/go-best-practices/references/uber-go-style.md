# Uber Go Style Guide

Read this for defensive API and concurrency details.
Source: <https://github.com/uber-go/guide/blob/master/style.md>.

- Use `%w` only when callers should match the wrapped error.
- Start enumerated constants at one when zero must mean unset.
- Prefer `time.Time` and `time.Duration` at API boundaries.
- Copy retained slices and maps when ownership crosses a boundary.
- Avoid goroutines whose termination is not visible to their caller.
- Use field names in struct literals except in very small test tables.
