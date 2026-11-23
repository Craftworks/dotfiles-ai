"""One translator call, shared by translate-rules and translate-skills.

The model, the prompt, and the JSON shape are defined here and nowhere
else. One call is one description plus one body: the shape measured on
2026-11-23, when a single rule kept the line contract in 18 of 18 runs.
"""

import json
import os
import re
import signal
import subprocess
import tempfile
import threading

# Sonnet over Haiku, measured on 2026-11-23 with the JSON shape below: both
# kept the line contract in 18 of 18 runs; Sonnet kept the source's emphasis
# and added no trailing period (Haiku added 2), at about 1.7 yen per rule.
MODEL = "claude-sonnet-5-5"
# The request and the answer are JSON: a description string and a body array
# with one string per line. Measured on 2026-11-23 with Haiku, plain lines
# kept the line contract in 13 of 18 runs (the description was merged into or
# swapped with the "# Title" heading); this JSON shape kept it in 18 of 18.
PROMPT = (
    "Translate the Japanese in the JSON object on standard input into English. "
    'Output only a JSON object with the same keys: "description" (a string) '
    'and "body" (an array of strings). The body array must have exactly as '
    "many elements as the input, element i translating element i. Keep empty "
    "strings empty, keep each element's Markdown marker (heading level, list "
    "marker, table row, code fence), keep text already in English and "
    "identifiers unchanged, and add no trailing period where the Japanese has "
    "none. No code fence around the JSON."
)

NEXT_ACTION = "make claude -p succeed, then rerun"

# Kana, CJK ideographs, and CJK and full-width punctuation. Any of these in the
# output means a line was not translated.
JAPANESE = re.compile(r"[\u3000-\u303f\u3040-\u30ff\u4e00-\u9fff\uff00-\uffef]")
MARKER = re.compile(r"^(\s*)(#{1,6}\s|[-*+]\s|\d+\.\s|>|\||```)")

_live_lock = threading.Lock()
_live: set[subprocess.Popen] = set()
_cancel = threading.Event()


class TranslatorFailed(Exception):
    """A translator call failed; the message is the cause, for the error line."""


class TranslatorCancelled(TranslatorFailed):
    """This call was stopped because another call in the run already failed."""


def reset_translation() -> None:
    """Clear a previous run's cancel flag. Each command calls this at start."""
    _cancel.clear()
    with _live_lock:
        _live.clear()


def cancel_translation() -> None:
    """Stop calls that have not finished. The run writes nothing after this."""
    _cancel.set()
    with _live_lock:
        procs = list(_live)
    for process in procs:
        kill_tree(process)


def marker(line: str) -> str:
    """The Markdown marker a line starts with: what the line contract keeps."""
    if not line.strip():
        return "blank"
    found = MARKER.match(line)
    if not found:
        return "text"
    indent, mark = found.groups()
    if mark[0].isdigit():
        mark = "1."
    return f"{len(indent)}:{mark.strip()}"


def _reject_line(where: str, ja_line: str, en_line: str) -> None:
    if marker(ja_line) != marker(en_line):
        raise TranslatorFailed(
            f"translator output {where} does not keep "
            "the Markdown marker of the Japanese"
        )
    if JAPANESE.search(en_line):
        raise TranslatorFailed(f"translator output {where} still contains Japanese")


def parse_answer(output: str) -> tuple[str, list[str]]:
    """The description and body of a translator answer, or TranslatorFailed."""
    if not output.strip():
        raise TranslatorFailed("translator output is empty")
    try:
        answer = json.loads(output)
    except json.JSONDecodeError:
        answer = None
    if (not isinstance(answer, dict)
            or not isinstance(answer.get("description"), str)
            or not isinstance(answer.get("body"), list)
            or not all(isinstance(line, str) for line in answer["body"])):
        raise TranslatorFailed(
            "translator output is not a JSON object with a description string "
            "and a body array of strings"
        )
    return answer["description"], answer["body"]


def check_output(ja: list[str], output: str) -> list[str]:
    """The answer as lines ([description] + body), if it keeps the line contract.

    ja[0] is the description and ja[1:] are the body lines. Raises
    TranslatorFailed naming the first way the answer breaks the contract.
    Body line numbers are 1-based.
    """
    description, body = parse_answer(output)
    if len(body) != len(ja) - 1:
        raise TranslatorFailed(
            f"translator output body has {len(body)} lines "
            f"for {len(ja) - 1} Japanese lines"
        )
    en = [description] + body
    for index, (ja_line, en_line) in enumerate(zip(ja, en)):
        where = "description" if index == 0 else f"body line {index}"
        _reject_line(where, ja_line, en_line)
    return en


def check_body(ja_body: list[str], output: str) -> list[str]:
    """The body of an answer whose description is not a line of the file.

    The description must still be a string without Japanese. The body must
    have one line per Japanese body line and keep each line's marker.
    """
    description, body = parse_answer(output)
    if JAPANESE.search(description):
        raise TranslatorFailed("translator output description still contains Japanese")
    if len(body) != len(ja_body):
        raise TranslatorFailed(
            f"translator output body has {len(body)} lines "
            f"for {len(ja_body)} Japanese lines"
        )
    for index, (ja_line, en_line) in enumerate(zip(ja_body, body), start=1):
        _reject_line(f"body line {index}", ja_line, en_line)
    return body


def splice(prev_ja: list[str], prev_en: list[str], ja: list[str],
           new_en: list[str]) -> list[str]:
    """Keep the previous English for every Japanese line that did not change.

    prev_ja and prev_en are a base pair of equal length (line i of one is the
    translation of line i of the other); new_en has one line per line of ja.
    """
    import difflib
    matcher = difflib.SequenceMatcher(None, prev_ja, ja, autojunk=False)
    result: list[str] = []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            result.extend(prev_en[i1:i2])
        else:
            result.extend(new_en[j1:j2])
    return result


def kept_pairs(prev_ja: list[str], prev_en: list[str], ja: list[str]) -> list[list[str]]:
    """[Japanese, English] for each non-blank line kept unchanged from the
    base pair: the only previous English the translator is shown.

    The English of a changed line is left out on purpose: shown it, Haiku
    copied the old line instead of translating the new Japanese.
    """
    import difflib
    matcher = difflib.SequenceMatcher(None, prev_ja, ja, autojunk=False)
    pairs = []
    for tag, i1, i2, _j1, _j2 in matcher.get_opcodes():
        if tag == "equal":
            pairs.extend(
                [prev_ja[i], prev_en[i]] for i in range(i1, i2) if prev_ja[i].strip()
            )
    return pairs


def kill_tree(process: subprocess.Popen) -> None:
    # claude may start children of its own; a timeout must not leave them.
    try:
        if os.name == "nt":
            subprocess.run(
                ["taskkill", "/T", "/F", "/PID", str(process.pid)],
                capture_output=True,
            )
        else:
            os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    process.wait()


def call_translator(translator: str, ja: list[str], reference: list[list[str]],
                    timeout: float) -> str:
    """Run one translator call and return its standard output (LF line endings).

    ja[0] is the description and ja[1:] are the body lines, which is the JSON
    sent on standard input. Raises TranslatorFailed when the command is
    missing, exits non-zero, or does not finish within timeout seconds.
    Raises TranslatorCancelled when this run was already cancelled.
    """
    if _cancel.is_set():
        raise TranslatorCancelled("cancelled")
    prompt = PROMPT
    if reference:
        prompt += (
            "\n\nFor consistent terms, these [Japanese, English] pairs are "
            "lines translated before:\n\n" + json.dumps(reference, ensure_ascii=False)
        )
    request = json.dumps({"description": ja[0], "body": ja[1:]}, ensure_ascii=False)
    command = [
        translator, "-p",
        "--model", MODEL,
        "--tools", "",
        "--strict-mcp-config",
        "--setting-sources", "",
        "--disable-slash-commands",
        "--no-session-persistence",
        "--system-prompt", prompt,
    ]
    # The translator starts in an empty directory with every source of
    # context switched off, so CLAUDE.md, rules, hooks, MCP servers and
    # skills cannot leak into the translation, and it has no tools.
    with tempfile.TemporaryDirectory(prefix="translate-") as workdir:
        try:
            process = subprocess.Popen(
                command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, cwd=workdir,
                start_new_session=os.name != "nt",
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0,
            )
        except FileNotFoundError:
            raise TranslatorFailed(f'translator "{translator}" was not found') from None
        with _live_lock:
            _live.add(process)
        try:
            try:
                stdout, stderr = process.communicate(
                    request.encode("utf-8"), timeout=timeout
                )
            except subprocess.TimeoutExpired:
                kill_tree(process)
                raise TranslatorFailed(
                    f"translator did not finish within {timeout:g} seconds"
                ) from None
        finally:
            with _live_lock:
                _live.discard(process)
    if _cancel.is_set():
        raise TranslatorCancelled("cancelled")
    if process.returncode != 0:
        detail = stderr.decode("utf-8", "replace").strip().splitlines()
        reason = f" ({detail[0]})" if detail else ""
        raise TranslatorFailed(
            f"translator exited with status {process.returncode}{reason}"
        )
    return stdout.decode("utf-8").replace("\r\n", "\n")


def write_atomically(path, data: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.")
    with os.fdopen(fd, "wb") as handle:
        handle.write(data.encode("utf-8"))
    os.replace(tmp, path)
