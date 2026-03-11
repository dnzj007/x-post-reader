from __future__ import annotations

import argparse
import json
import sys

from .reader import XPostReaderError, read_post


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Read public X/Twitter post text through the oEmbed API.")
    parser.add_argument("url", help="A public x.com or twitter.com status URL")
    parser.add_argument("--expand-links", action="store_true", help="Resolve t.co links to their final destination")
    parser.add_argument("--timeout", type=int, default=20, help="HTTP timeout in seconds")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        result = read_post(args.url, expand_links=args.expand_links, timeout=args.timeout)
    except XPostReaderError as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False, indent=2), file=sys.stderr)
        return 1

    print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
