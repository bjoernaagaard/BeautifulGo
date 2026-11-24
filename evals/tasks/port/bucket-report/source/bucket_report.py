"""Group timed events into fixed-width buckets and summarize them by tag.

Usage: python3 bucket_report.py WIDTH [LABEL_WIDTH] < events

Each input line is OFFSET<TAB>TAG<TAB>LABEL, where OFFSET is a whole number of
minutes from an anchor time and may be negative. Blank lines are skipped.
"""

import sys


class InputError(Exception):
    """A line of input that does not follow the format."""


def parse_line(number, line):
    parts = line.split("\t")
    if len(parts) != 3:
        raise InputError(f"line {number}: want 3 tab-separated fields, got {len(parts)}")
    offset_text, tag, label = parts
    try:
        offset = int(offset_text)
    except ValueError:
        raise InputError(f"line {number}: bad offset {offset_text!r}") from None
    tag = tag.strip().lower()
    if not tag:
        raise InputError(f"line {number}: empty tag")
    return {"offset": offset, "tag": tag, "label": label.strip()}


def read_events(stream):
    events = []
    for number, raw in enumerate(stream, start=1):
        line = raw.rstrip("\n")
        if not line.strip():
            continue
        events.append(parse_line(number, line))
    return events


def initials(label):
    return "".join(word[0].upper() for word in label.split())


def shorten(label, width):
    if len(label) <= width:
        return label
    return label[: width - 1] + "~"


def bucket_lines(events, width, label_width):
    ordered = sorted(events, key=lambda e: e["offset"] // width)
    lines = []
    current = None
    for event in ordered:
        bucket = event["offset"] // width
        if bucket != current:
            current = bucket
            start = bucket * width
            count = sum(1 for e in events if e["offset"] // width == bucket)
            lines.append(f"[{start},{start + width}) n={count}")
        position = event["offset"] % width
        label = shorten(event["label"], label_width)
        last = event["label"][-1] if event["label"] else "-"
        lines.append(
            f"  +{position:<3} {label:<{label_width}} {initials(event['label']) or '-'} {last} #{event['tag']}"
        )
    return lines


def tag_summary(events):
    tags = {}
    for event in events:
        # ast-grep-ignore: python/setdefault-without-defaultdict, port fixture whose expected outputs are fixed; a plain dict keeps the dict order the port must match
        tags.setdefault(event["tag"], []).append(event["offset"])
    lines = []
    for tag, offsets in tags.items():
        mean = round(sum(offsets) / len(offsets))
        lines.append(f"{tag}: n={len(offsets)} mean={mean} span={max(offsets) - min(offsets)}")
    return lines, tags


def busiest(tags, limit):
    ranked = sorted(tags.items(), key=lambda item: len(item[1]), reverse=True)
    return [tag for tag, _ in ranked[:limit]]


def report(events, width, label_width):
    lines = bucket_lines(events, width, label_width)
    summary, tags = tag_summary(events)
    lines.append("tags:")
    lines.extend("  " + line for line in summary)
    lines.append("busiest: " + ", ".join(busiest(tags, 3)))
    return lines


def parse_args(argv):
    if len(argv) not in (1, 2):
        raise InputError("usage: bucket_report.py WIDTH [LABEL_WIDTH]")
    try:
        width = int(argv[0])
        label_width = int(argv[1]) if len(argv) == 2 else 8
    except ValueError:
        raise InputError("WIDTH and LABEL_WIDTH must be integers") from None
    if width < 1 or label_width < 2:
        raise InputError("WIDTH must be at least 1 and LABEL_WIDTH at least 2")
    return width, label_width


def main(argv):
    try:
        width, label_width = parse_args(argv)
    except InputError as err:
        print(err, file=sys.stderr)
        return 2
    try:
        events = read_events(sys.stdin)
    except InputError as err:
        print(err, file=sys.stderr)
        return 1
    if not events:
        print("no events")
        return 0
    print("\n".join(report(events, width, label_width)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
