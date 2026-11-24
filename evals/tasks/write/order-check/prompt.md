Write a Go command line program named order-check in its own module in {ARM}/write/order-check/. Put go.mod in that folder and the main package at its root, so that `go build .` in that folder builds the program. The Go toolchain on this machine is 1.27.

Usage: `order-check FILE`, or `order-check -` to read stdin.

The input is one JSON object that describes an order:

```json
{
  "id": "A-17",
  "customer": "Ada",
  "lines": [{"sku": "pen", "qty": 2, "unitCents": 1250}],
  "coupon": "SAVE10",
  "placedAt": "2026-05-01T12:30:00+02:00"
}
```

- "id" and "customer" are strings. "lines" is an array of objects, each with a string "sku", an integer "qty" and an integer "unitCents".
- "coupon" is optional and may be null or an empty string, which all mean no coupon. "SAVE10" takes 10 percent off the subtotal, rounded down to whole cents. "FLAT500" takes 500 cents off the subtotal, but never more than the subtotal.
- "placedAt" is optional and may be null. When present it is an RFC 3339 timestamp.

The program prints one JSON object to stdout and exits 0. Its members are "id", "customer", "items" (the sum of all qty), "subtotalCents" (the sum of qty times unitCents), "discountCents", "totalCents" (subtotal minus discount), and "placedAt" (the same instant in UTC, in RFC 3339 form). "discountCents" is present whenever a coupon applies, even when it is 0, and absent when there is no coupon. "placedAt" is absent when the input has no timestamp. Member order and spacing in the output are free.

Errors, which print nothing to stdout and a message to stderr in any wording:

- Exit 3 when the input cannot be read, such as a file that does not exist.
- Exit 4 when the input is not one JSON object of the shape above. That includes malformed JSON, data after the object, a member the shape does not name, a member name given twice in one object, a member name that matches only when letter case is ignored, a value of the wrong type such as a qty of 2.5 or "2", and a placedAt that is not RFC 3339.
- Exit 5 when the shape is right but the order is not valid: an empty id or customer, no lines, an empty sku, a qty below 1, a negative unitCents, or an unknown coupon.
- Exit 2 when the program does not get exactly one argument.
