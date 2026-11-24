{ARM}/port/bucket-report/bucket_report.py is a Python 3 command line program. Port it to a Go command line program in its own module in that same folder. Put go.mod in {ARM}/port/bucket-report/ and the main package at its root, so that `go build .` in that folder builds the program. The Go toolchain on this machine is 1.27. Leave bucket_report.py in place.

The Go program takes the same arguments and reads the same stdin as `python3 bucket_report.py`. For every input it must print the same bytes to stdout and exit with the same code. Text on stderr may differ.
