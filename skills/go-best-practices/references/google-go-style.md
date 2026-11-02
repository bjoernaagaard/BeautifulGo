# Google Go Style Guide

Read this when choosing between clarity and an abstraction.
Source: <https://google.github.io/styleguide/go/>.

- Clarity outranks brevity.
- Return concrete types unless callers need to vary the implementation.
- Do not make an interface merely to mock one local concrete type.
- Document what a signature cannot say.
- Keep package APIs small and cohesive.
- Consistency within a package beats introducing a second local idiom.
