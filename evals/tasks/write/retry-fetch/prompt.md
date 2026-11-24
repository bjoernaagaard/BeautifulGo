Write a Go command line program named retry-fetch in its own module in {ARM}/write/retry-fetch/. Put go.mod in that folder and the main package at its root, so that `go build .` in that folder builds the program. The Go toolchain on this machine is 1.27.

Usage: `retry-fetch [-attempts N] [-timeout D] [-backoff D] URL`

The program sends GET requests to URL until one gives an answer or it gives up.

- `-attempts` is the total number of requests it may send. The default is 3.
- `-timeout` bounds the whole run, all attempts and the waits between them together. The default is 2s.
- `-backoff` is the wait before each retry. The default is 100ms.
- Durations use Go duration syntax, such as 500ms or 1s.

How it handles each response:

- Status 200: the body is a JSON object with an integer member "id", a string member "name" and an array of strings "tags". It may hold other members. Print one line `id=<id> name=<name> tags=<tags joined with commas>` to stdout and exit 0.
- Status 200 with a body that is not valid JSON, or whose members have the wrong types: do not retry, and exit 7.
- Status 404: do not retry, and exit 3.
- Any other status from 400 to 499: do not retry, and exit 4.
- Status 500 to 599, or a request that fails without a response, such as a refused connection: retry. When no attempts are left, exit 5.

When the `-timeout` deadline passes before the program has its answer, it stops at once, also during a wait between attempts, and exits 6.

A missing URL, more than one argument, an unknown flag, or an `-attempts` below 1: exit 2.

Print nothing to stdout except the success line. Messages for the other outcomes go to stderr, in any wording.
