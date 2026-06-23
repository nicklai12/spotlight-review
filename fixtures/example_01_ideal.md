# Session Summary

## What Changed

A new `helpers.py` module was introduced under `src/utils/` containing two small utility functions, `format_timestamp` and `slugify`. `src/main.py` was updated to import and use `format_timestamp` so the startup message prints a readable UTC date/time instead of a raw Unix timestamp, and the shutdown log now includes elapsed runtime.

## Why (Inferred)

The change improves the readability of log/output messages by formatting timestamps in a human-friendly way, and it centralizes commonly needed string/date helpers so they can be reused elsewhere in the project.

## Files Touched

- `src/utils/helpers.py`
- `src/main.py`
