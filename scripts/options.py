"""Command-line option rules shared by every script in this directory.

A language flag (--lang, --from, --to) names an edition directory
(rules.<code>, skills.<code>), so its value becomes part of a path. The rules
here are checked before a script reads or writes anything.
"""

import re

# A language code is one path component: letters, digits, "_" and "-" only.
# This is not a list of known languages: any edition directory that exists
# can be selected. It only keeps the value from leaving the repository.
LANGUAGE_CODE = re.compile(r"[A-Za-z0-9_-]+")


class OptionError(Exception):
    """A bad option value; the message is the whole error line."""


def once(values: list[str] | None, flag: str) -> str | None:
    """The single value of a flag declared with action="append", or None when
    it was not passed. Raises OptionError when it was passed more than once."""
    if not values:
        return None
    if len(values) > 1:
        raise OptionError(f"{flag}: --{flag} was given more than once. pass it once")
    return values[0]


def language(values: list[str] | None, flag: str, default: str) -> str:
    """The language code a language flag selects (default when not passed).

    Raises OptionError for a repeated flag or a value that is not a code.
    """
    value = once(values, flag)
    if value is None:
        return default
    if not LANGUAGE_CODE.fullmatch(value):
        raise OptionError(
            f'{flag}: "{value}" is not a language code. '
            f"pass --{flag} with letters, digits, - or _, such as en or ja"
        )
    return value
