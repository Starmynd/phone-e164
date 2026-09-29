# phone-e164

Normalize human-formatted phone numbers to E.164 (`+CCnnnnnnn`).
Single file, pure standard library.

Supported input shapes:

- `+`-prefixed numbers pass through (formatting is stripped)
- `00` international prefix (`00 44 20 ...` -> `+4420...`)
- local formats anchored by a default country: `us`, `ca`, `ru`, `kz`
- trunk prefixes are dropped: `8-912-345-67-89` (ru/kz) -> `+7912...`,
  `1-415-...` (us) -> `+1415...`
- separators: spaces, dashes, dots, parentheses

The checks are structural, not a carrier database: plausible national
number length (min per country code, E.164 cap of 15 digits) and digits
only. Anything else raises `ValueError`.

## CLI

```console
$ phone-e164 "+7 (912) 345-67-89" -c us "(415) 555-2671"
+79123456789
+14155552671

$ echo "8 701 123 45 67" | phone-e164 -c kz
+77011234567
```

Bad numbers print an error to stderr and make the CLI exit 1, so it can
be used for batch cleanup pipelines.

## Python API

```python
from phone_e164 import parse

parse("+7 (912) 345-67-89")            # "+79123456789"
parse("(415) 555-2671", "us")          # "+14155552671"
parse("00 44 20 7946 0958")            # "+442079460958"
parse("8-912-345-67-89", "ru")         # "+79123456789"
```

`parse(raw, default_country=None)` is the whole API (`format_number` is
an alias). `COUNTRY_CODES` is a small dict - extend it for more
countries; the trunk-drop rule applies to codes 1 and 7 automatically
and to leading zeros elsewhere.

## Testing

```console
$ python3 phone_e164.py --test
selftest: failures=0
```

Covers US/RU/KZ normalization, trunk dropping, the `00` prefix,
pass-through of valid E.164, separator handling and six invalid-input
paths.

## License

MIT
