English | [日本語](README.ja.md)

# scripts

Scripts that process the language editions of the rules and skills in this repository. The canonical sources are `rules.ja/` and `skills.ja/`; other editions (such as `rules.en/` and `skills.en/`) are generated from them by the translate scripts. Run everything from the repository root.

The contract of each script (options, error messages, reporting, tests) is in [SPEC.md](SPEC.md). This README does not repeat it.

## Scripts

| Script | What it does | Basic invocation |
|---|---|---|
| `build-rules` | Generates the Cursor and Claude rule files from one rule edition | `scripts/build-rules --lang en` |
| `install-rules` | Links the generated rule files into `~/.cursor/rules/` and `~/.claude/rules/` | `scripts/install-rules --lang en` |
| `install-skills` | Links the skills of one edition into the home skill directories | `scripts/install-skills --lang en` |
| `translate-rules` | Translates `rules.<from>/` into `rules.<to>/` (default `ja` into `en`) | `scripts/translate-rules` |
| `translate-skills` | Translates `skills.<from>/` into `skills.<to>/` (default `ja` into `en`) | `scripts/translate-skills` |

`build-rules`, `install-rules`, and `install-skills` accept `--check`, which reports drift and writes nothing. The translate scripts call `claude -p`, so you must be logged in to Claude Code.

## Typical workflow

1. Edit the canonical source (`rules.ja/` or `skills.ja/`) and commit it
2. Translate: `scripts/translate-rules` and `scripts/translate-skills`, then review and commit the changes under `rules.en/` and `skills.en/`
3. Build the rule files: `scripts/build-rules --lang en`
4. Install: `scripts/install-rules --lang en` and `scripts/install-skills --lang en`
5. Verify: run `build-rules`, `install-rules`, and `install-skills` again with `--check`

Build and install a rule edition back to back with the same `--lang`.

## Running the tests

```sh
python3 -m unittest discover -s scripts/tests -p 'test_*.py'
```

The tests use a temporary repository and a fake translator, so they do not call `claude` and do not touch your home directory.
