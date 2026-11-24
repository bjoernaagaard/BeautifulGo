Write a Go command line program named probe in its own module in {ARM}/write/probe/. Put go.mod in that folder and the main package at its root, so that `go build .` in that folder builds the program. The Go toolchain on this machine is 1.27.

Usage: `probe [-workers N] [-timeout D] < urls`

The program reads URLs from stdin, one per line, and ignores blank lines and spaces around a URL. It checks every URL with a GET request.

- `-workers` is the most requests in flight at once. The default is 4.
- `-timeout` bounds the whole run. The default is 5s. Durations use Go duration syntax, such as 500ms or 1s.
- Checks start in input order. Each line is checked on its own, so a URL that appears twice is checked twice.

When every check has finished, or the deadline has passed, the program prints one line per input URL to stdout, in input order:

- `<url> up <status>` for a response with a status below 400
- `<url> down <status>` for a response with a status of 400 or higher
- `<url> down error` for a request that failed without a response, such as a refused connection
- `<url> unknown` for a check that had not finished when the deadline passed, including a check that had not started

When the deadline passes, the program prints its lines at once and does not wait for checks that are still running.

Exit 3 when any line is unknown, else 1 when any line is down, else 0. A command line argument, an unknown flag, or a `-workers` below 1: exit 2.
