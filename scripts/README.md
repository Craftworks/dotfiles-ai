# scripts Directory Specification

This README is the specification of the scripts directory.

It holds the scripts that process the canonical sources in `rules.ja/` and `skills.ja/`. `build-rules` and `build-skills` are implemented. `translate-rules` is currently unimplemented (design only).

| Script | Job |
|---|---|
| `build-rules` | Deterministically generates the deliverables (Cursor and Claude formats) from the canonical sources |
| `build-skills` | Installs the skills from the canonical sources into the home skill directories as symbolic links |
| `translate-rules` | Generates the English edition `rules.en/` for publication from the canonical sources |

## build-rules

Purpose: generate `.cursor/rules/<name>.mdc` and `.claude/rules/<name>.md` from `body.md` and `meta.json` in `rules.ja/<name>/`.

Input/output contract:

- The input is the canonical sources only. The output is a pure function of the input: the same input always produces the same bytes (idempotent)
- Generated files carry no marker header. Drift from the canonical sources is detected by `--check`, not by text inside the file
- `--check` writes nothing; it only verifies that the generated files match the canonical sources, and exits with an error naming any file that has drifted
- Reporting is part of the contract. A normal run prints what it did on stdout: a summary line (`wrote <count> files from rules.ja under <root>`) followed by the path of every file written. A successful `--check` prints `checked <count> files from rules.ja under <root>; all match; wrote nothing` followed by every path checked. Silent success is a defect: it is indistinguishable from nothing happening
- A failed `--check` prints a summary line, one line per problem, and the next action (`run without --check to write them.`) on stderr. A differing or missing file is named individually (`differs: <path>`, `missing: <path>`); when a whole output directory is missing or empty, the directory is named once (`missing: <dir>`, `empty: <dir>`) and the files under it are not listed. Empty means the directory has no entries. A directory that exists and contains anything, including an unrelated file, is not empty: each missing deliverable is named with `missing: <path>`. Problems are reported at the unit the operator acts on

Non-goals: translation, installation into the home directory, git operations, watch mode, incremental processing.

Conversion table (the canonical `meta.json` has a top-level `description` and a `cursor` namespace):

| meta.json | Cursor format (.mdc) | Claude format (.md) |
|---|---|---|
| `cursor.alwaysApply: true` | `alwaysApply: true` in frontmatter | No frontmatter |
| `cursor.globs` present | `globs` in frontmatter | Emitted as `paths` in frontmatter |
| Otherwise (description only) | Description only in frontmatter | No frontmatter |

Note: Claude Code's rule loading reads only `paths` in frontmatter; it does not read `alwaysApply`. Files placed in `~/.claude/rules/` are loaded resident. How auto rules (description only) are handled on the home side is an open question for the install design (pending verification by measurement).

Validation and errors:

- All rules are validated first. `meta.json` must be an object with a string `description` and an object `cursor`. Unknown keys are rejected at the top level and inside `cursor`. `cursor.globs`, when present, is a string or null; null means no globs. `cursor.alwaysApply`, when present, is a boolean. `body.md` must exist. Writing starts only after every rule passes. If any rule is invalid, the script exits with an error and no output files are written
- If `rules.ja` itself is missing, the script exits with an error and writes nothing
- Error messages take the form: rule name, cause, next action. A missing `rules.ja` is named `rules.ja` in that same form. The exit code reports success or failure

Implementation: Python 3, standard library only, a single file (no extension). JSON is read with the standard `json` module. Frontmatter values are emitted as unquoted plain scalars, with keys ordered description, globs, alwaysApply, matching the current .mdc files. It must run on both Mac and Windows.

Tests: built test-first. Golden-file comparison on three fixtures (alwaysApply / globs / description only); a regression run over a frozen snapshot of the real rules (inputs and expected outputs captured on 2026-11-21 under `scripts/tests/fixtures/real/` — the snapshot is the oracle, never the live outputs); assertions on the output reporting (the full summary line and every path a run says it wrote or checked); `--check` cases (clean, tampered, one missing file while a sibling remains, missing or empty output directories, and a directory that contains only unrelated files); and error cases (missing file, invalid JSON, unknown key, `meta.json` that is not an object, `description` missing or not a string, `cursor` missing or not an object, an unknown key under `cursor`, `globs` that is not a string, `alwaysApply` that is not a boolean, a missing `rules.ja` directory, and a mix of valid and invalid rules — verifying that nothing is written).

Done conditions:

1. Against the frozen snapshot of the real rules, the generated files match the expected outputs byte for byte
2. Running it twice in a row produces zero diff on the second run
3. `--check` exits successfully when the outputs match the canonical sources, and exits with an error when a generated file has been edited by hand, a file is missing, or an output directory is missing or empty — naming the drifted file, or the directory alone when the directory itself is missing or has no entries. A directory that still contains an unrelated file is not that case: each missing deliverable is named
4. On invalid input it exits with an error and writes no output files at all
5. On a fixture with globs, the Claude format carries a correct `paths` frontmatter

## build-skills

Purpose: install the skills in `skills.ja/<name>/` into the home skill directories (`~/.claude/skills/` and `~/.cursor/skills/`) as one symbolic link per skill, pointing at the skill directory in this repository. Skills need no format conversion, so installation creates links, never copies: the canonical source stays the only real files, and editing a skill takes effect without reinstalling.

Input/output contract:

- The unit of installation is the skill directory. A link covers everything in it (SKILL.md and any auxiliary files); files added inside a skill need no reinstall. Only adding or removing a whole skill does
- Link targets are absolute paths under the repository root given by `--root`. If the repository moves, the links break; `--check` reports them and a normal run repairs them
- The script manages only symbolic links that point into this repository's `skills.ja/`. It never creates, overwrites, or deletes a real file or directory, and never touches a link that points elsewhere. Entries owned by others (for example `~/.claude/skills/synced/`, where Claude Code keeps the skills it downloads from the user's claude.ai account) are outside its management
- A destination entry that blocks a skill — a real file or directory, or a link pointing outside this repository — is a conflict. Conflicts are detected before anything is changed: if any skill is invalid or any conflict exists on a selected destination, the run exits with an error and no link is created, repaired, or removed
- A link at a selected destination that points into `skills.ja/` for a skill that no longer exists is stale. A normal run removes it; `--check` reports it. Only links into this repository are ever removed
- Reporting is part of the contract. A normal run prints a summary line (`installed <count> skills from skills.ja under <home>`) followed by the path of every link in place, and one `removed: <path>` line for each stale link it removed. A successful `--check` prints `checked <count> links from skills.ja under <home>; all match; wrote nothing` followed by every path checked. Silent success is a defect: it is indistinguishable from nothing happening
- A failed `--check` prints a summary line, one line per problem, and the next action (`run without --check to install the links; conflicting entries must be removed by hand.`) on stderr. Problems are named at the unit the operator acts on: `missing: <path>` when no entry exists, `differs: <path>` when a link points at the wrong target or is broken, `stale: <path>` for a link whose skill is gone, `conflict: <path>` for a blocking entry the script must not touch. When a destination directory itself is missing, the directory is named once (`missing: <dir>`) and the links under it are not listed
- Running it twice in a row changes nothing on the second run (idempotent)
- `--tool <cursor|claude>` narrows the run to one destination. `cursor` is `<home>/.cursor/skills`; `claude` is `<home>/.claude/skills`. Omit `--tool` and both destinations are selected, which is every case above. The unselected destination is not part of the run: the script does not create it, does not look inside it, and does not report it. A conflict or a stale link there does not affect the run, and the entries there are identical before and after, including when the run fails. `--tool` with a value other than `cursor` or `claude` exits with `tool: unknown tool "<value>". pass --tool cursor or --tool claude`. `--tool` given more than once exits with `tool: --tool was given more than once. pass it once`. Either error is printed before any destination is read or written, and nothing is changed. The summary still counts skills on a normal run and links on `--check`; with one destination those two numbers are equal, and every path printed is under the selected destination

Non-goals: copying skill files, installing rules (build-rules generates them; their home installation is separate), translation and the English edition of skills, deleting real files or directories, managing plugin skills or claude.ai-synced skills, watch mode, Windows support (symbolic links there need privileges this setup does not assume).

Validation and errors:

- All skills are validated first. `skills.ja` must exist. Every subdirectory of `skills.ja/` is a skill: it must contain a `SKILL.md` whose frontmatter, read as simple `key: value` lines, has a `name` and a `description`, both non-empty strings, and the `name` must equal the directory name. Other frontmatter keys are allowed (the skill format is an open standard with optional keys such as `disable-model-invocation`). A skill named `synced` (in any capitalisation) is rejected when `claude` is a selected destination: Claude Code reserves that name under `~/.claude/skills/` for synced skills. When the run is `--tool cursor` only, that name is an ordinary skill. Linking starts only after every skill passes and no conflict exists on a selected destination
- Error messages take the form: skill name, cause, next action. A missing `skills.ja` is named `skills.ja` in that same form. The exit code reports success or failure

Implementation: Python 3, standard library only, a single file (no extension), the same conventions as build-rules. The command line is `build-skills [--root <repository root>] [--home <home directory>] [--tool <cursor|claude>] [--check]`; `--home` defaults to the user's home directory and exists so tests can install into a temporary home. `--tool` is specified and not yet implemented. Frontmatter is read as simple `key: value` lines; no YAML library is used. macOS is the target platform.

Tests: built test-first, in the style of the build-rules tests (the script is invoked as a subprocess against temporary `--root` and `--home` directories). Cases: a fresh install links every skill at both destinations with the correct targets; a second run changes nothing; `--check` passes on the installed state and fails, naming the path, for a missing link, a wrong-target link, a stale link, and a conflict, and names the directory alone when a destination directory is missing; a normal run removes a stale link and repairs a link broken by moving the repository; a conflict (a real directory at a destination) blocks the whole run and nothing is linked; invalid inputs (missing SKILL.md, missing or empty description, a name that differs from the directory name, a skill named `synced`, a missing `skills.ja`, and a mix of valid and invalid skills) exit with an error and change nothing; entries the script does not own (a real `synced/` directory, a foreign link, a real file) are unchanged by every run, including failed ones; assertions on the output reporting (the full summary line and every path a run says it installed or checked); a run over the real `skills.ja` into a temporary home, where every current skill ends up linked and every link resolves to a directory containing a SKILL.md (the oracle is `skills.ja` itself: the output is links, not bytes, so there is no golden snapshot); and `--tool` cases (cursor only and claude only each link just that destination and leave the other untouched, a conflict or stale link on the unselected side does not block and stays, repair and stale removal apply only to the selected side, `--check` names only the selected destination, a skill named `synced` is rejected for claude and accepted for cursor only, and an unknown or repeated `--tool` exits with the sentence above and changes nothing).

Done conditions:

1. Into an empty home, with `--tool` omitted, every skill in `skills.ja` is linked at both destinations, and every link resolves to that skill's directory in the repository
2. Running it twice in a row creates, repairs, and removes nothing on the second run
3. `--check` exits successfully on the installed state, and exits with an error naming the path when a link is missing, points at the wrong target, or is stale, when a blocking entry conflicts, and naming the directory alone when a destination directory itself is missing
4. On invalid input or any conflict, it exits with an error and changes nothing: no link is created, repaired, or removed
5. Entries the script does not own — real files and directories, links pointing outside this repository, and `synced/` — are identical before and after every run, including failed runs
6. With `--tool cursor` or `--tool claude`, only that destination is linked, checked, repaired, or cleaned. The other destination is identical before and after, including when the run fails. An unknown or repeated `--tool` changes nothing

## translate-rules

Purpose: generate the English edition `rules.en/` for publication from `rules.ja/` (the Japanese canonical sources). This repository is published openly, so an English edition is provided for people reading the repository. The canonical sources stay in Japanese, the language the approver can verify directly. Agents follow the Japanese deliverables that build-rules generates from those sources. The English edition is a generated artifact.

Contract:

- The scope is `body.md` and the `description` in `meta.json`. `basis.md` (the rationale) is a document for the approver and is out of scope
- The output is `rules.en/<name>/body.md` and `rules.en/<name>/meta.json` only. Distribution is performed by build-rules from the Japanese canonical sources
- `description` is translated. The `cursor` namespace is copied as the same JSON. Headings and identifiers that are already English stay as written
- The translator is the Claude Code command `claude -p`. The script passes the Japanese source and, when that rule already exists under `rules.en/`, the previous English. It writes the translation that the command prints on stdout. Authentication is the Claude Code login already on the machine
- It runs when the canonical sources have been updated. Targets are identified from the changed files under `rules.ja/` via `git diff`; rule names can also be given explicitly
- Where the Japanese is unchanged, the previous English is kept. Only the Japanese that changed is retranslated. Review is the diff of the targeted files under `rules.en/`
- If `claude` is missing or the command fails, the run writes nothing and leaves `rules.en/` as it was. It exits with an error that names the rule, the cause, and the next action: make `claude -p` succeed, then rerun

Non-goals: Google Translate, DeepL, and any translator that requires an API key.

## How this specification is kept

It records the "why" and the contracts. The details of behavior have their canonical source in the tests, and the method of implementation in the code.
