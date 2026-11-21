# scripts Directory Specification

This README is the specification of the scripts directory.

It holds the scripts that process the canonical sources in `rules/`. Both scripts are currently unimplemented (design only).

| Script | Job |
|---|---|
| `build-rules` | Deterministically generates the deliverables (Cursor and Claude formats) from the canonical sources |
| `translate-rules` | Generates the English edition `rules.en/` for publication from the canonical sources |

## build-rules

Purpose: generate `.cursor/rules/<name>.mdc` and `.claude/rules/<name>.md` from `body.md` and `meta.json` in `rules/<name>/`.

Input/output contract:

- The input is the canonical sources only. The output is a pure function of the input: the same input always produces the same bytes (idempotent)
- Generated files carry no marker header. Drift from the canonical sources is detected by `--check`, not by text inside the file
- `--check` writes nothing; it only verifies that the generated files match the canonical sources, and exits with an error naming any file that has drifted

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

Implementation: Python 3, standard library only, a single file (no extension). JSON is read with the standard `json` module, and frontmatter strings are emitted as YAML double-quoted scalars using JSON-style quoting. It must run on both Mac and Windows.

Tests: built test-first. Golden-file comparison on three fixtures (alwaysApply / globs / description only), a regression run over the real 11 rules (the generated output must match the current `.mdc` files byte for byte), and error cases (missing file, invalid JSON, unknown key — verifying that nothing is written).

Done conditions:

1. On the real repository, the generated `.cursor/rules/*.mdc` match the current files byte for byte
2. Running it twice in a row produces zero diff on the second run
3. `--check` exits successfully when the outputs match the canonical sources, and exits with an error naming the file when a generated file has been edited by hand
4. On invalid input it exits with an error and writes no output files at all
5. On a fixture with globs, the Claude format carries a correct `paths` frontmatter

## translate-rules

Purpose: generate the English edition `rules.en/` for publication from `rules/` (the Japanese canonical sources). This repository is published openly, so an English edition is provided; the canonical sources stay in Japanese, the language the approver can verify directly, and the English edition is a generated artifact.

- The scope is `body.md` and the `description` in `meta.json`. `basis.md` (the rationale) is a document for the approver and is out of scope
- The output is `rules.en/` only. Distribution is performed by build-rules from the Japanese canonical sources
- It runs when the canonical sources have been updated. Targets are identified from the changed files under `rules/` via `git diff`; rule names can also be given explicitly
- Translation is non-deterministic: within a changed file, the wording of unchanged paragraphs may also shift. Review is done per changed file

## How this specification is kept

It records the "why" and the contracts. The details of behavior have their canonical source in the tests, and the method of implementation in the code.
