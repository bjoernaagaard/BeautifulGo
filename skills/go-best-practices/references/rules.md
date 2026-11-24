# Rule index

One row per rule in `SKILL.md`. The id is the section number and a short name, and
`SKILL.md` holds the authoritative wording. The check column names what reports a
violation: `lint:` a golangci-lint linter in the go-review configuration, `vet:` a
`go vet` analyzer, `fix:` a `go fix` analyzer, `compiler` for code that does not
build, and `reader` for a rule only a reader can check. The source column names the
guides that state the rule: E Effective Go, W Go Code Review Comments, G the Google
style guide, U the Uber style guide, L the module layout guide at
https://go.dev/doc/modules/layout, R the release notes or package documentation, and
ours when every source is silent. Where the guides disagree, the parentheses name
the side taken.

A tool in the check column reports only the forms of a violation it detects, with the
go-review configuration. A row that also says `reader` has forms the tool misses, so a
reader checks those too. When the tools did not run, or ran with another configuration,
check every row by reading.

| id | rule | check | source |
|---|---|---|---|
| 1.fix-diff | Preview modernizations before handoff | lint:modernize fix:minmax reader | ours |
| 1.format | Run gofmt and leave no unformatted Go files | lint:gofmt | E W G |
| 1.vet | Run go vet before handoff | lint:govet vet:printf reader | U |
| 1.lint | Run golangci-lint with the repository config | reader | U |
| 1.race-run | Run the race detector before handoff | reader | ours |
| 1.vulncheck | Run govulncheck after dependency or security changes | reader | ours |
| 1.tool-install | Install the tools, or report a missing one | reader | ours |
| 1.fix-findings | Fix findings rather than suppress them | reader | ours |
| 1.suppress | Explain a line suppression and name the linter | lint:nolintlint | ours |
| 1.go-fix-modernize | Apply available modernizations with go fix | lint:modernize fix:rangeint reader | ours |
| 1.race-bug | Treat race reports as bugs | reader | ours |
| 2.read-version | Read the go line before using a feature | compiler | ours |
| 2.new-module | Declare the current release in a new module | reader | ours |
| 2.library-minimum | Declare the oldest tested release in a library | reader | ours |
| 2.min-max | Use min and max for simple comparisons | lint:modernize fix:minmax | R |
| 2.clear | Use clear for clearing maps or slices | reader | R |
| 2.slices | Use slices helpers over hand loops and `sort.Slice` | lint:modernize fix:slicessort | R |
| 2.maps | Use maps helpers over hand loops | lint:modernize fix:mapsloop | R |
| 2.cmp | Use cmp for standard ordering comparisons | reader | R |
| 2.slog | Prefer `log/slog` to `log.Printf` | reader | R |
| 2.after-func | Use `context.AfterFunc` for a cancellation callback | reader | R |
| 2.without-cancel | Use `context.WithoutCancel` to detach only cancellation | reader | G |
| 2.loop-copy | Remove redundant copies of fresh range variables | lint:modernize fix:forvar | R |
| 2.range-int | Use range over integers for simple loops | lint:modernize fix:rangeint | R |
| 2.mux | Use ServeMux method and wildcard patterns | reader | R |
| 2.iterator-helpers | Use iterator helpers instead of collecting to range | reader | R |
| 2.generic-alias | Use generic aliases where aliases are needed | reader | R |
| 2.test-context | Use `t.Context` in tests | lint:modernize fix:testingcontext reader | G |
| 2.b-loop | Use `b.Loop` in benchmarks | reader | R |
| 2.test-chdir | Use `t.Chdir` for temporary directory changes in tests | lint:usetesting | R |
| 2.os-root | Use `os.Root` for untrusted paths | lint:gosec reader | R |
| 2.omitzero | Use omitzero for relevant JSON fields | lint:modernize fix:omitzero | R |
| 2.tools-directive | Use tool directives in place of `tools.go` | reader | R |
| 2.split-seq | Use `strings.SplitSeq` when ranging over split results | lint:modernize fix:stringsseq | R |
| 2.add-cleanup | Prefer `runtime.AddCleanup` to SetFinalizer where appropriate | reader | R |
| 2.rand-text | Use `crypto/rand.Text` for a token | reader | R |
| 2.discard-handler | Use `slog.DiscardHandler` when logs are immaterial | lint:sloglint | R |
| 2.wg-go | Use `WaitGroup.Go` over Add and Done | lint:modernize fix:waitgroupgo | R |
| 2.synctest | Use `testing/synctest` instead of real timers | reader | R |
| 2.origin-protection | Use CrossOriginProtection for CSRF checks | reader | R |
| 2.gomaxprocs | Trust container aware GOMAXPROCS | reader | R |
| 2.new-expr | Use `new(expr)` instead of a pointer helper | lint:modernize fix:newexpr | R |
| 2.errors-astype | Use `errors.AsType` instead of an `errors.As` target pointer | lint:modernize fix:errorsastype | R |
| 2.modernizers | Use the go fix modernizers where applicable | lint:modernize fix:any | R |
| 2.generic-methods | Use generic methods instead of helper free functions | reader | R |
| 2.json-v2 | Use `encoding/json/v2` where its new API is appropriate | reader | R |
| 2.uuid | Use the standard uuid package | reader | R |
| 2.leak-profile | Use the goroutineleak profile when diagnosing leaks | reader | R |
| 2.pin-tools | Pin tools with go get `-tool` | reader | ours |
| 2.sum | Commit `go.sum` | reader | ours |
| 2.tidy | Run go mod tidy after import changes | reader | ours |
| 2.toolchain | Add a toolchain line only when needed | reader | ours |
| 2.stdlib-first | Check the standard library before adding a dependency | reader | ours |
| 2.dependencies | No new framework, ORM, assertion library, or container | reader | ours |
| 2.no-framework | Add no framework unless already used | reader | ours |
| 2.no-orm | Add no ORM unless already used | reader | ours |
| 2.no-di | Add no DI container unless already used | reader | ours |
| 2.no-assertion-dependency | Add no assertion dependency unless already used | reader | G |
| 2.exp | Replace `x/exp` packages the standard library provides | lint:exptostd | ours |
| 3.stutter | Avoid names that repeat the package name | lint:revive reader | E G |
| 3.package-name | No util, common, helpers, models, or misc packages | reader | W G U |
| 3.package-common | Avoid generic common, helpers, models, and misc names | reader | W G U |
| 3.getter | Use no Get prefix on getters | reader | E G |
| 3.io-verb | Use Fetch or Load for I/O | reader | ours |
| 3.initialism | Keep initialisms in a single case | lint:revive | W G |
| 3.receiver-name | Short receiver names, the same on every method | lint:revive lint:staticcheck | W G |
| 3.receiver-consistency | The same receiver name on every method | lint:revive | W G |
| 3.receiver-length | One or two letter receiver names | reader | ours (W and G say usually; kept as a limit so receivers stay uniform) |
| 3.shadow-builtin | Do not shadow predeclared names | lint:revive | ours |
| 3.shadow-import | Do not shadow a package name | reader | G (Google allows shadowing with a rename; a ban keeps the package reachable) |
| 3.enum-type | Use a named enum type | reader | U |
| 3.enum-iota | Use iota for enum constants | reader | E U |
| 3.enum-string | Implement String for an enum | reader | ours |
| 3.enum-invalid-zero | Start at `iota+1` when zero is invalid | reader | U |
| 3.enum-valid-zero | Name a zero state that code uses | reader | U |
| 3.enum-no-literal-zero | Use the named zero constant in comparisons | reader | ours |
| 3.enum-roundtrip | Accept every String name in the enum parser | reader | ours |
| 4.early-return | Return early, with no else after return | lint:revive reader | E W G U |
| 4.early-return-indent | Leave the successful path unindented | reader | E W G U |
| 4.bool-param | Avoid Boolean parameters in exported signatures | lint:revive reader | ours (Google allows Boolean options and Uber call site comments; a named type reads at the call site) |
| 4.options-count | Options struct for three or more optional settings | reader | ours (G and U leave the form open; one threshold keeps APIs alike) |
| 4.options-value | Pass options structs by value | reader | ours |
| 4.options-zero | Make the options zero value mean defaults | reader | ours |
| 4.functional-options | Reserve functional options for compatible library constructors | reader | ours (G and U allow them more widely; an options struct is less code) |
| 4.close-write | Check Close after writing to a resource | lint:errcheck reader | ours |
| 4.iterator-vs-slice | Choose an iterator or a slice by use | reader | ours |
| 4.stop-yield | Stop calling yield after it returns false | reader | ours |
| 4.index-slice | Return a slice for indexing or second passes | reader | ours |
| 5.accept-interface | Accept interfaces when behavior is sufficient | reader | E G |
| 5.return-concrete | Return concrete types where possible | reader | W G (Effective Go returns an interface that adds nothing; the wiki default wins) |
| 5.consumer-interface | Declare an interface next to its consumer | reader | W G (Google allows producer interfaces for protocols; consumer ownership is the default) |
| 5.defer-interface | Wait for a second implementation or test double | reader | W G (Google also allows interfaces that hide complexity; the skill waits for a real second use) |
| 5.small-interface | Keep interfaces small | reader | G (Google's wording, with no fixed method count) |
| 5.interface-pointer | Never take a pointer to an interface | reader | W U |
| 5.concrete-app | Keep application code concrete and avoid DI frameworks | reader | ours |
| 5.receiver-kind | Pointer receivers throughout once one method needs one | lint:recvcheck | W G U (Uber only illustrates mixed method sets) |
| 5.embed-mutex | Never embed `sync.Mutex` in an exported struct | reader | E U (scoped to exported structs, where Lock joins the API) |
| 5.strong-types | Use strong types for units and identifiers | reader | ours |
| 5.generics-duplication | Use generics to share an algorithm between types | reader | G |
| 5.generics-interface | No type parameter where an interface fits | reader | ours |
| 5.generic-interface-method | Interface methods cannot have their own type parameters | compiler | R |
| 5.generic-method-satisfy | A generic method cannot implement an interface method | compiler | R |
| 6.handle-once | Handle an error once | reader | G U (Uber also allows logging and degrading; the skill keeps one handling path) |
| 6.error-context | Add operation or ID context the caller lacks | reader | E G U |
| 6.error-case | Use lowercase error text | lint:staticcheck | W G |
| 6.error-failed | No "failed to" in error context | reader | G U |
| 6.error-redundancy | Avoid repeating data the wrapped error already carries | reader | G U |
| 6.wrap-public | Use `%w` when callers match the cause | lint:errorlint | G U |
| 6.hide-private | Use `%v` for a private cause | reader | G U |
| 6.error-text | Never match errors by message text | reader | G U |
| 6.error-is | Use `errors.Is` when an error might be wrapped | lint:errorlint | G U |
| 6.error-as | Use `errors.AsType` for matching concrete error types | lint:modernize fix:errorsastype | ours |
| 6.exported-error | Return the error interface from exported APIs | reader | G U |
| 6.ignore-comment | Ignore an error only with a stated reason | lint:errcheck lint:nolintlint reader | G (E and W say never discard; Google's explained exception, enforced by nolintlint) |
| 6.in-band | No in band sentinel for not found | reader | E W G |
| 6.lookup-consistent | One not found convention per type | reader | ours |
| 6.panic | Never panic for invalid caller input | reader | W G (E, G and U allow internal or startup panics; caller input never panics) |
| 6.recover | Do not use recover for control flow | reader | U (E and G show recover inside a package; Uber's stricter route) |
| 6.exit-main | Use `os.Exit` and `log.Fatal` only in main | reader | U (E and G allow exit in init; exit only in main keeps cleanup and reuse) |
| 6.run-error | main calls run, which returns error | reader | ours |
| 7.ctx-required | Take context on blocking or I/O functions | reader | ours |
| 7.ctx-first | Put context first and name it ctx | lint:revive | W G (the wiki says most functions; Google's always first rule wins) |
| 7.ctx-struct | Do not store context in a struct | lint:containedctx reader | W G (both allow it to match a fixed signature; the skill bans it) |
| 7.ctx-name | Name the context argument ctx | reader | ours |
| 7.ctx-propagate | Do not replace a caller context with Background | lint:contextcheck reader | W G (Google admits another root when the caller's is wrong; the skill keeps the normal rule) |
| 7.cancel-defer | Defer cancel after deriving a context | lint:gosec lint:govet vet:lostcancel | ours |
| 7.cancel-prompt-defer | Defer cancel at once, not later by hand | reader | ours |
| 7.ctx-values | Context values only for request scoped data | reader | ours |
| 7.sync-api | Prefer synchronous APIs and let callers add concurrency | reader | W G |
| 7.cancel-return | Return `ctx.Err` when the operation was canceled | lint:nilerr reader | ours |
| 7.cancel-outcome | Cancellation is not a result to record | reader | ours |
| 7.deadline-once | Put one timeout around retries or fallbacks | reader | ours |
| 7.goroutine-lifetime | Every goroutine has an owner and a wait | reader | W G U (Uber's exception for work that ends on its own) |
| 7.start-wg | Start owned goroutines with `WaitGroup.Go` when applicable | lint:modernize fix:waitgroupgo | ours |
| 7.owner-wait | Wait for owned goroutines | reader | U |
| 7.owner-stop | Stop signal unless the work ends on its own | reader | U |
| 7.errgroup-need | errgroup only for first error, cancellation, or limits | reader | ours |
| 7.mutex-location | Keep the mutex alongside the fields it guards | reader | ours |
| 7.lock-callback | No caller code while holding a lock | reader | ours |
| 7.lock-io | No blocking I/O while holding a lock | reader | ours |
| 7.lock-snapshot | Read related values under one acquisition | reader | ours |
| 7.channel-close | The sender closes a channel, once | reader | ours |
| 7.channel-direction | Declare channel direction in signatures when possible | reader | G |
| 7.channel-cap | Use channel capacity zero or one unless justified | reader | E U (Effective Go sizes buffers to the work; Uber's zero or one, larger with a reason) |
| 7.channel-cancel | Blocking sends and receives select on `ctx.Done` | reader | ours |
| 7.typed-atomic | Use typed atomics for a lone counter | lint:modernize fix:atomictypes | ours (Uber's atomic module replaced by the standard typed atomics) |
| 7.once-value | Use `sync.OnceValue` for lazy initialization | reader | ours |
| 7.no-init-go | Do not start goroutines in init | reader | U |
| 7.pprof | Inspect the goroutineleak profile when goroutine counts grow | reader | ours |
| 8.clone-boundary | Clone shared slices and maps at API boundaries | reader | G U |
| 8.sort-map | Sort map keys before output or hashing | reader | ours |
| 8.time-types | Use `time.Duration` for spans and `time.Time` for instants | reader | U |
| 8.wire-unit | Put the unit in a bare number's name | reader | U |
| 8.json-struct | Use structs for JSON request and response bodies | reader | ours |
| 8.omitzero | omitzero for structs, `time.Time,` and meaningful zeros | lint:modernize fix:omitzero | ours |
| 8.omitempty | Keep omitempty for empty strings, slices and maps | reader | ours |
| 8.json-strict | Use `encoding/json/v2` for new strict decoding | reader | ours |
| 8.json-error-text | Do not assert exact `encoding/json` error text | reader | ours (Uber asserts error text; the json v2 engine changes the wording) |
| 8.root | Use `os.OpenRoot` for untrusted file names | lint:gosec reader | ours |
| 8.rand-secret | Use `crypto/rand` and `rand.Text` for secrets or tokens | lint:gosec reader | W G |
| 8.rand-nonsecret | Use `math/rand/v2` for nonsecret randomness | reader | ours |
| 8.rand-token | Use `crypto/rand.Text` for generated tokens | reader | ours (Google uses the reader plus an encoding; rand.Text drops that step) |
| 8.readheader-timeout | Set ReadHeaderTimeout on HTTP servers | lint:gosec | ours |
| 8.shutdown | Shut servers down with Shutdown and a context | reader | ours |
| 8.routes | Route with ServeMux method patterns and PathValue | reader | ours |
| 8.csrf | CrossOriginProtection on state changing browser endpoints | reader | ours |
| 8.client-timeout | Set a timeout on HTTP clients | reader | ours |
| 8.client-context | Use NewRequestWithContext for HTTP client requests | lint:noctx | ours |
| 8.body-close | Close every HTTP response body | lint:bodyclose | G |
| 8.client-timeout-std | No default HTTP client without a timeout | reader | ours |
| 8.config-main | Read configuration once in main | reader | ours |
| 8.close-not-finalizer | Close, not a finalizer or cleanup | reader | ours |
| 9.structured-logger | Use `log/slog` and put dynamic data in attributes | reader | ours (Google log and glog not taken; slog is the standard library) |
| 9.static-message | Use a constant slog message | lint:sloglint | ours |
| 9.library-logging | Libraries generally return errors without logging | reader | G U |
| 9.secrets | Never log secrets | reader | ours |
| 9.log-valuer | Implement `slog.LogValuer` for types holding secrets | reader | ours |
| 9.test-discard | DiscardHandler in tests that ignore logs | reader | ours |
| 10.external-package | Prefer an external test package | reader | ours (Google also allows same package tests; external tests keep to the public API) |
| 10.table-tests | Use named table cases and `t.Run` | reader | G U (Uber rejects complex tables; the skill gives the plain recipe) |
| 10.failure-message | Failure messages give input, got, then want | reader | W G |
| 10.cmp-diff | Use go-cmp `cmp.Diff` to compare structs | reader | G |
| 10.no-assertion-lib | Add no assertion library | reader | W G (Uber allows assertion helpers; Google's failure messages win) |
| 10.tempdir | Use `t.TempDir` in tests | lint:usetesting | ours |
| 10.setenv | Use `t.Setenv` to set test environment variables | lint:usetesting | ours |
| 10.cleanup | Use `t.Cleanup` to register test resource cleanup | reader | ours |
| 10.helper | Use `t.Helper` in test helpers | lint:thelper | G |
| 10.timer-bubble | Use `synctest.Test` for tests that wait on timers | reader | ours |
| 10.bubble-network | No real network I/O in a synctest bubble | reader | ours |
| 10.bubble-run | Do not call `t.Run` inside a synctest bubble | reader | ours |
| 10.bubble-parallel | Do not call `t.Parallel` inside a synctest bubble | reader | ours |
| 10.httptest | Test handlers with httptest, not a mocked client | reader | ours |
| 10.real-resource | A real temp directory or server over mocks | reader | ours (Google uses real transports and Uber mocks; a real resource tests more) |
| 10.benchmark-loop | Use `b.Loop` in benchmarks | reader | ours |
| 10.fuzz-parser | Fuzz parsers for untrusted input | reader | ours |
| 11.doc-present | Add a doc comment for every exported name | lint:revive reader | E W G |
| 11.doc-sentence | Doc comments start with the name | reader | E W G |
| 11.doc-contract | Document what the signature cannot say | reader | G U |
| 11.doc-errors | Document errors callers can match | reader | G U |
| 11.doc-concurrency | Document concurrency safety when it matters | reader | G |
| 11.deprecated | Use a Deprecated: paragraph for retired APIs | reader | ours |
| 11.fix-inline | Use go:fix inline on retired one-line wrappers | reader | ours |
| 11.module-root | Start with one root package | reader | L |
| 11.cmd | Put commands under cmd when the module also has importable packages | reader | L |
| 11.internal | Put private packages under internal | reader | L |
| 11.no-pkg | Do not create a pkg directory | reader | ours |
| 11.no-layer | Avoid generic layer packages such as services | reader | ours |
| 11.no-mutable-global | No package variables mutated after startup | reader | E G U (Google's private cache that callers cannot observe is the one exception) |
| 11.no-init-effects | No init side effects beyond registration | reader | ours (E and U allow more in init; only standard registration kept) |
