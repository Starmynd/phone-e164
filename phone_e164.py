#!/usr/bin/env python3
"""phone-e164 - normalize phone numbers to E.164 (+CCnnnnnnn).

Handles common human formatting: spaces, dashes, dots, parentheses and
a leading trunk prefix. Country rules are minimal but explicit:
US/CA (country 1), RU (7) and KZ (7) drop a national trunk "8" or "0"
prefix; an existing "+", a default country, or a "00" international
prefix anchor the country code. Nothing here validates that a number is
actually assigned - only that it is structurally plausible.

Pure standard library; importable functions plus a CLI.
"""

from __future__ import annotations

import argparse
import re
import sys

# country calling code by ISO-ish name
COUNTRY_CODES = {
    "us": "1",
    "ca": "1",
    "ru": "7",
    "kz": "7",
}

# minimal plausible national significant number lengths per code
MIN_NSN = {"1": 10, "7": 10, "default": 7}


def _digits(raw: str) -> str:
    return re.sub(r"[^\d+]", "", raw)


def _strip_trunk(national: str, code: str) -> str:
    """Drop a trunk prefix (8 for 1/7 countries, 0 elsewhere) or a
    redundantly repeated country code."""
    if code in ("1", "7"):
        if national.startswith("8") and len(national) >= 10:
            national = national[1:]
        elif national.startswith(code) and len(national) > 10:
            national = national[len(code):]
    elif national.startswith("0"):
        national = national.lstrip("0")
    return national


def parse(raw: str, default_country: str | None = None) -> str:
    """Normalize `raw` to E.164; raise ValueError when implausible.

    default_country: "us", "ca", "ru" or "kz" - used when the input has
    no "+" and no "00" international prefix.
    """
    text = raw.strip()
    has_plus = text.startswith("+")
    digits = _digits(text)
    if not digits:
        raise ValueError(f"no digits in {raw!r}")

    if has_plus:
        return _assemble("", digits[1:])

    if digits.startswith("00"):  # international prefix
        return _assemble("", digits[2:])

    if default_country is None:
        raise ValueError(
            f"no country information in {raw!r}; pass default_country")
    if default_country not in COUNTRY_CODES:
        raise ValueError(f"unknown country: {default_country!r}")

    code = COUNTRY_CODES[default_country]
    national = _strip_trunk(digits, code)
    return _assemble(code, national)


def _assemble(code: str, nsn: str) -> str:
    if not nsn:
        raise ValueError("empty national number")
    if not nsn.isdigit():
        raise ValueError("national number must be digits only")
    minimum = MIN_NSN.get(code[:1] if code else "default", MIN_NSN["default"])
    if len(nsn) < minimum:
        raise ValueError(f"national number too short: {nsn!r}")
    if len(nsn) > 15:  # E.164 hard cap on the whole number
        raise ValueError(f"national number too long: {nsn!r}")
    return "+" + code + nsn


def format_number(raw: str, default_country: str | None = None) -> str:
    """Convenience alias for parse()."""
    return parse(raw, default_country)


def _selftest() -> int:
    failed = 0

    def check(cond: bool, label: str) -> None:
        nonlocal failed
        print(("PASS " if cond else "FAIL ") + label)
        if not cond:
            failed += 1

    def raises(raw: str, country: str | None = None, label: str = "") -> None:
        try:
            parse(raw, country)
            check(False, label or f"raises on {raw!r}")
        except ValueError:
            check(True, label or f"raises on {raw!r}")

    check(parse("+7 (912) 345-67-89") == "+79123456789",
          "russian +7 with formatting")
    check(parse("(415) 555-2671", "us") == "+14155552671",
          "us local number with default country")
    check(parse("1-415-555-2671", "us") == "+14155552671",
          "us number with leading 1")
    check(parse("8-912-345-67-89", "ru") == "+79123456789",
          "russian trunk 8 dropped")
    check(parse("8 701 123 45 67", "kz") == "+77011234567",
          "kazakhstan trunk 8 dropped")
    check(parse("00 44 20 7946 0958") == "+442079460958",
          "00 international prefix")
    check(parse("+442079460958") == "+442079460958",
          "already E.164 passes through")
    check(parse("415.555.2671", "us") == "+14155552671", "dot formatting")

    raises("12345")                       # too short, no country
    raises("(415) 555-2671")              # no default country given
    raises("+7 123")                      # too short
    raises("abc", "us")                   # no digits
    raises("9876543210987654321", "us")   # absurdly long
    raises("(415) 555-2671", "xx", "unknown country raises")

    print(f"selftest: failures={failed}")
    return 1 if failed else 0


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--test" in argv:
        return _selftest()

    ap = argparse.ArgumentParser(
        prog="phone-e164", description="Normalize phone numbers to E.164.")
    ap.add_argument("numbers", nargs="*")
    ap.add_argument("-c", "--country", default=None,
                    help="default country for numbers without a prefix "
                         "(us, ca, ru, kz)")
    args = ap.parse_args(argv)

    numbers = args.numbers
    if not numbers:
        numbers = [ln.strip() for ln in sys.stdin if ln.strip()]

    status = 0
    for raw in numbers:
        try:
            print(parse(raw, args.country))
        except ValueError as exc:
            print(f"error: {exc}", file=sys.stderr)
            status = 1
    return status


if __name__ == "__main__":
    sys.exit(main())
