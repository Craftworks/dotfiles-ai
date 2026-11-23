# scripts Directory Specification

This README is the specification of the scripts directory.

It holds the scripts that process the canonical sources in `rules.ja/`. `build-rules` is implemented. `translate-rules` is currently unimplemented (design only).

| Script | Job |
|---|---|
| `build-rules` | Deterministically generates the deliverables (Cursor and Claude formats) from the canonical sources |
| `translate-rules` | Generates the English edition `rules.en/` for publication from the canonical sources |

## build-rules

Purpose: generate `.cursor/rules/<name>.mdc` and `.claude/rules/<name>.md` from `body.md` and `meta.json` in `rules.ja/<name>/`.

Input/output contract:

- The input is the canonical sources only. The output is a pure function of the input: the same input always produces the same bytes (idempotent)
- Generated files carry no marker header. Drift from the canonical sources is detected by `--check`, not by text inside the file
- `--check` writes nothing; it only verifies that the generated files match the canonical sources, and exits with an error naming any file that has drifted
- Reporting is part of the contract. A normal run prints what it did on stdout: a summary line (`wrote <count> files from rules.ja under <root>`) followed by the path of every file written. A successful `--check` prints `checked <count> files from rules.ja under <root>; all match; wrote nothing` followed by every path checked. Silent success is a defect: it is indistinguishable from nothing happening
- A failed `--check` prints a summary line, one line per problem, and the next action (`run without --check to write them.`) on stderr. A differing or missing file is named individually (`differs: <path>`, `missing: <path>`); when a whole output directory is missing or empty, the directory is named once (`missing: <dir>`, `empty: <dir>`) and the files under it are not listed. Problems are reported at the unit the operator acts on

Non-goals: translation, installation into the home directory, git operations, watch mode, incremental processing.

Conversion table (the canonical `meta.json` has a top-level `description` and a `cursor` namespace):

| meta.json | Cursor format (.mdc) | Claude format (.md) |
|---|---|---|
| `cursor.alwaysApply: true` | `alwaysApply: true` in frontmatter | No frontmatter |
| `cursor.globs` present | `globs` in frontmatter | Emitted as `paths` in frontmatter |
| Otherwise (description only) | Description only in frontmatter | No frontmatter |

Note: Claude Code's rule loading reads only `paths` in frontmatter; it does not read `alwaysApply`. Files placed in `~/.claude/rules/` are loaded resident. How auto rules (description only) are handled on the home side is an open question for the install design (pending verification by measurement).

Validation and errors:

- All rules are validated first (required keys, types, and unknown keys in meta.json; existence of body.md). Writing starts only after every rule passes. If any rule is invalid, the script exits with an error and no output files are written
- Error messages take the form: rule name, cause, next action. The exit code reports success or failure

Implementation: Python 3, standard library only, a single file (no extension). JSON is read with the standard `json` module. Frontmatter values are emitted as unquoted plain scalars, with keys ordered description, globs, alwaysApply, matching the current .mdc files. It must run on both Mac and Windows.

Tests: built test-first. Golden-file comparison on three fixtures (alwaysApply / globs / description only); a regression run over a frozen snapshot of the real rules (inputs and expected outputs captured on 2026-11-21 under `scripts/tests/fixtures/real/` — the snapshot is the oracle, never the live outputs); assertions on the output reporting (what a run says it wrote or checked); `--check` cases (clean, tampered, missing files, missing or empty output directories); and error cases (missing file, invalid JSON, unknown key, and a mix of valid and invalid rules — verifying that nothing is written).

Done conditions:

1. Against the frozen snapshot of the real rules, the generated files match the expected outputs byte for byte
2. Running it twice in a row produces zero diff on the second run
3. `--check` exits successfully when the outputs match the canonical sources, and exits with an error when a generated file has been edited by hand, a file is missing, or an output directory is missing or empty — naming the drifted file, or the directory alone when the whole directory is the problem
4. On invalid input it exits with an error and writes no output files at all
5. On a fixture with globs, the Claude format carries a correct `paths` frontmatter

## translate-rules

Purpose: generate the English edition `rules.en/` for publication from `rules.ja/` (the Japanese canonical sources). This repository is published openly, so an English edition is provided; the canonical sources stay in Japanese, the language the approver can verify directly, and the English edition is a generated artifact.

- The scope is `body.md` and the `description` in `meta.json`. `basis.md` (the rationale) is a document for the approver and is out of scope
- The output is `rules.en/` only. Distribution is performed by build-rules from the Japanese canonical sources
- It runs when the canonical sources have been updated. Targets are identified from the changed files under `rules.ja/` via `git diff`; rule names can also be given explicitly
- Translation is non-deterministic: within a changed file, the wording of unchanged paragraphs may also shift. Review is done per changed file

## How this specification is kept

It records the "why" and the contracts. The details of behavior have their canonical source in the tests, and the method of implementation in the code.
