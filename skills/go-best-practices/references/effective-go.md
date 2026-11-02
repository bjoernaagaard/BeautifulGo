# Effective Go

Read this for the reasoning behind a naming, interface, or concurrency choice.
Source: <https://go.dev/doc/effective_go>.

- Names are concise because package names supply context.
- Interfaces are usually one to three methods and are discovered from use.
- Embedding composes behavior. It is not inheritance.
- Zero values should be useful when that can be done safely.
- Concurrency is explicit. A goroutine without a stop condition leaks.
- `defer` ties resource release to the acquisition path.
