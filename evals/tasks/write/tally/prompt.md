Write a Go command line program named tally in its own module in {ARM}/write/tally/. Put go.mod in that folder and the main package at its root, so that `go build .` in that folder builds the program. The Go toolchain on this machine is 1.27.

Usage: `tally [-top K] < events`

Each input line holds three fields separated by one or more spaces or tabs: an id, a category and an amount. The program ignores blank lines and lines whose first character after any spaces or tabs is `#`.

- The id is a UUID in the 36 character form with hyphens, such as `0f8e2a52-6c1d-4b8e-9a51-3c2d7e9b1a04`, with hex digits in either letter case. Two ids are the same when they differ only in letter case.
- The category is any text without spaces.
- The amount is a base 10 integer that fits in a signed 64 bit integer. It may be negative.

The program prints one line per category to stdout:

```text
<category> count=<lines> total=<sum of amounts> min=<smallest amount> max=<largest amount> ids=<distinct ids in the category>
```

Sort the lines by total, largest first, and break ties by category in byte order. With `-top K`, print only the first K lines. K is 0 by default, which prints them all. After the category lines, print one line `distinct=<distinct ids across all lines>`.

A line that does not follow this format: print a message that names the line number to stderr, print nothing to stdout, and exit 1. A command line argument, an unknown flag, or a negative `-top`: exit 2.
