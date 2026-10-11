#!/usr/bin/env python3
"""Reject DAST targets outside the synthetic loopback/container boundary."""

from __future__ import annotations

import argparse
from urllib.parse import urlsplit


def assert_local_target(value: str) -> None:
    parsed = urlsplit(value)
    if (
        parsed.scheme != "http"
        or parsed.hostname not in {"127.0.0.1", "localhost", "lab-api"}
        or parsed.port is None
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError("target must be explicit http://127.0.0.1|localhost|lab-api:<port>")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("target")
    args = parser.parse_args()
    try:
        assert_local_target(args.target)
    except ValueError as error:
        parser.error(str(error))
    print("PASS: target is inside the synthetic lab boundary")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
