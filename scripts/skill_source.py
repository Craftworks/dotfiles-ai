"""Read and validate one canonical skill under skills.ja.

Shared by install-skills and translate-skills so a skill is valid for both
or for neither, with the same error lines.
"""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SkillMd:
    """SKILL.md: frontmatter fields in file order, and the body after it.

    body uses LF and has no trailing newline. fields include name and
    description. The body is everything after the closing ---.
    """

    fields: tuple[tuple[str, str], ...]
    body: str

    @property
    def description(self) -> str:
        return dict(self.fields)["description"]


def load_skill_md(skill_dir: Path) -> SkillMd | str:
    """The SKILL.md in skill_dir, or the error line (name, cause, next action)."""
    name = skill_dir.name
    path = skill_dir / "SKILL.md"
    if not path.is_file():
        return f"{name}: missing SKILL.md. create SKILL.md"
    return parse_skill_md(path.read_text(encoding="utf-8"), name)


def parse_skill_md(text: str, name: str) -> SkillMd | str:
    """SKILL.md text, or the error line. name is the skill directory name."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return f"{name}: missing name. add a non-empty name"
    fields: list[tuple[str, str]] = []
    end = None
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            end = index
            break
        if not line.strip():
            continue
        if ":" not in line:
            return (f"{name}: SKILL.md line {index + 1} has no colon. "
                    "write it as key: value")
        key, value = line.split(":", 1)
        key, value = key.strip(), value.strip()
        if any(key == seen for seen, _value in fields):
            return (f'{name}: duplicate key "{key}" in SKILL.md. '
                    f"keep one {key} line")
        fields.append((key, value))
    if end is None:
        return (f"{name}: SKILL.md frontmatter has no closing ---. "
                "add --- after the frontmatter")
    meta = dict(fields)
    name_value = meta.get("name")
    if name_value is None:
        return f"{name}: missing name. add a non-empty name"
    if name_value == "":
        return f"{name}: name is empty. set name to {name}"
    if name_value != name:
        return (
            f'{name}: name "{name_value}" does not match the directory. '
            f"set name to {name}"
        )
    if "description" not in meta:
        return f"{name}: missing description. add a non-empty description"
    if meta["description"] == "":
        return (
            f"{name}: description is empty. "
            "set description to a non-empty string"
        )
    return SkillMd(tuple(fields), "\n".join(lines[end + 1:]))
