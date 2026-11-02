# Go Code Review Comments

Read this when a review finding needs the wiki's original rule.
Source: <https://go.dev/wiki/CodeReviewComments>.

- Receiver names are short and consistent.
- Do not use a pointer only to save a small copy.
- Context values are for request-scoped data, not optional parameters.
- Import grouping and initialisms follow the examples in the wiki.
- Empty slices are nil by default.
- Examples and useful test output are part of the API.
