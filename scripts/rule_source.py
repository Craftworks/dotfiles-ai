"""Read and validate one canonical rule under rules.ja.

Shared by build-rules and translate-rules so a rule is valid for both or for
neither, with the same error lines. Both scripts import it from their own
directory (Python puts a script's directory first on sys.path).
"""

import json
from dataclasses import dataclass
from pathlib import Path

MISSING_RULES_JA = "rules.ja: missing rules.ja. create rules.ja"


@dataclass(frozen=True)
class Rule:
    """A valid rule: rules.ja/<name>/meta.json and body.md.

    cursor holds only the keys meta.json gives it (globs: str | None,
    alwaysApply: bool). body is the bytes of body.md as written.
    """

    name: str
    description: str
    cursor: dict
    body: bytes


def load_rule(rule_dir: Path) -> Rule | str:
    """The rule in rule_dir, or the error line (name, cause, next action)."""
    name = rule_dir.name
    meta_path = rule_dir / "meta.json"
    if not meta_path.is_file():
        return f"{name}: missing meta.json. create meta.json"
    try:
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return f"{name}: invalid JSON in meta.json. fix meta.json"
    if not isinstance(meta, dict):
        return f"{name}: meta.json is not an object. replace meta.json with an object"
    unknown = [key for key in meta if key not in {"description", "cursor"}]
    if unknown:
        return (f'{name}: unknown key "{unknown[0]}". '
                "remove the unknown key or extend the schema")
    if "description" not in meta:
        return f"{name}: missing description. add a string description"
    if not isinstance(meta["description"], str):
        return f"{name}: description is not a string. set description to a string"
    if "cursor" not in meta:
        return f"{name}: missing cursor. add a cursor object"
    cursor = meta["cursor"]
    if not isinstance(cursor, dict):
        return f"{name}: cursor is not an object. set cursor to an object"
    cursor_unknown = [key for key in cursor if key not in {"globs", "alwaysApply"}]
    if cursor_unknown:
        return (f'{name}: unknown key "{cursor_unknown[0]}" in cursor. '
                "remove the unknown key or extend the schema")
    globs = cursor.get("globs")
    if globs is not None and not isinstance(globs, str):
        return f"{name}: globs is not a string. set globs to a string or null"
    if "alwaysApply" in cursor and not isinstance(cursor["alwaysApply"], bool):
        return f"{name}: alwaysApply is not a boolean. set alwaysApply to true or false"
    body_path = rule_dir / "body.md"
    if not body_path.is_file():
        return f"{name}: missing body.md. create body.md"
    return Rule(name, meta["description"], cursor, body_path.read_bytes())
