# scripts Directory Specification (SPEC)

This SPEC is the specification of the scripts directory.

It holds the scripts that process the language editions of the rules and skills. The canonical sources are `rules.ja/` and `skills.ja/`; further editions (for example `rules.en/` and `skills.en/`) are generated from them by the translate scripts. `build-rules`, `install-rules`, `install-skills`, `translate-rules`, and `translate-skills` are implemented.

| Script | Job |
|---|---|
| `build-rules` | Deterministically generates the deliverables (Cursor and Claude formats) from the rule edition selected by `--lang` |
| `install-skills` | Installs the skills of the edition selected by `--lang` into the home skill directories as symbolic links |
| `install-rules` | Links the deliverables `build-rules` already wrote into the home rule directories |
| `translate-rules` | Translates the rule edition `rules.<from>/` into `rules.<to>/` (by default the canonical sources into English) |
| `translate-skills` | Translates the skill edition `skills.<from>/` into `skills.<to>/` (by default the canonical sources into English) |

Common to every script (the sections below do not repeat it):

- Each script is a Python 3 standard-library file with no extension and works on the repository that contains it. build-rules and the translate scripts run on Mac and Windows; the install scripts are macOS only (they use symbolic links)
- `--lang <language>` (build-rules, install-*; default `en`) selects the edition `rules.<language>/` or `skills.<language>/`. `--from` (default `ja`) and `--to` (default `en`) do the same for the translate scripts, and must name different languages. Any language whose edition directory exists can be used. A language code is letters, digits, `-` and `_` only, so a value cannot leave the repository. An invalid code, a repeated option, or `--from` equal to `--to` is an error raised before anything is read or written
- `--tool <cursor|claude>` (install-*) narrows the run to one destination (`<home>/.cursor/...` or `<home>/.claude/...`); omitted means both. The unselected destination is not created, read, or reported, and a conflict, stale link, or missing deliverable there does not affect the run. An unknown or repeated value is an error before anything is changed
- `--check` (build-rules, install-*) writes nothing and reports drift. `--home` (install-*) and `--translator` (translate-*) exist so tests can use a temporary home and a fake translator
- Every error names the unit (rule, skill, or file), the cause, and the next action, and the exit code reports success or failure. A run that fails writes, creates, repairs, and removes nothing: all inputs are validated before the first change. Exact wording is fixed by the tests
- Reporting is part of the contract: a normal run prints a summary line and every path it wrote or linked; a successful `--check` says what it checked and that it wrote nothing. Silent success is a defect because it looks like nothing happened. A failed `--check` names each problem at the unit the operator acts on (`differs`, `missing`, `stale`, `conflict`); when a whole directory is missing or empty it names the directory once
- Rerunning a script on its own output changes nothing (idempotent)
- Building and installing rules are done back to back with the same `--lang`, because deliverables do not record which language they were built from
- The tests under `scripts/tests/` are the canonical source of behavior details (error text, report format, cases). They run each script as a subprocess inside a temporary repository; the automated tests never call the real `claude`

## build-rules

Purpose: generate `.cursor/rules/<name>.mdc` and `.claude/rules/<name>.md` from `body.md` and `meta.json` in `rules.<lang>/<name>/`, where `<lang>` is the language selected by `--lang`.

Input/output contract:

- The input is the selected edition only. The output is a pure function of the input: the same input always produces the same bytes
- Generated files carry no marker header. Drift from the canonical sources is detected by `--check`, not by text inside the file
- A missing or differing file is named individually. A directory that exists and holds anything, including an unrelated file, is not empty: each missing deliverable is named

Non-goals: translation, installation into the home directory, git operations, watch mode, incremental processing.

Conversion table (the canonical `meta.json` has a top-level `description` and a `cursor` namespace):

| meta.json | Cursor format (.mdc) | Claude format (.md) |
|---|---|---|
| `cursor.alwaysApply: true` | `alwaysApply: true` in frontmatter | No frontmatter |
| `cursor.globs` present | `globs` in frontmatter | Emitted as `paths` in frontmatter |
| Otherwise (description only) | Description only in frontmatter | No frontmatter |

Frontmatter values are unquoted plain scalars, with keys ordered description, globs, alwaysApply.

Note: Claude Code's rule loading reads only `paths` in frontmatter; it does not read `alwaysApply`. Files placed in `~/.claude/rules/` are loaded resident. How auto rules (description only) are handled on the home side is an open question for the install design (pending verification by measurement).

Validation:

- All rules are validated first, by `scripts/rule_source.py` (shared with translate-rules, so a rule is valid for both or for neither). `meta.json` must be an object with a string `description` and an object `cursor`. Unknown keys are rejected at the top level and inside `cursor`. `cursor.globs`, when present, is a string or null (null means no globs). `cursor.alwaysApply`, when present, is a boolean. `body.md` must exist. A missing `rules.<lang>` is an error

Done conditions:

1. Against the frozen snapshot of the real rules (`scripts/tests/fixtures/real/`, which holds the Japanese sources), the generated files match the expected outputs byte for byte
2. Running it twice in a row produces zero diff on the second run
3. `--check` exits successfully when the outputs match the selected edition, and exits with an error when a generated file has been edited by hand, a file is missing, or an output directory is missing or empty — naming the drifted file, or the directory alone when the directory itself is missing or has no entries. A directory that still contains an unrelated file is not that case: each missing deliverable is named
4. On invalid input it exits with an error and writes no output files at all
5. On a fixture with globs, the Claude format carries a correct `paths` frontmatter

## install-skills

Purpose: install the skills in `skills.<lang>/<name>/` into the home skill directories (`~/.claude/skills/` and `~/.cursor/skills/`) as one symbolic link per skill, pointing at the skill directory in this repository. Skills need no format conversion, so installation creates links, never copies: the edition in the repository stays the only real files, and editing a skill takes effect without reinstalling.

Input/output contract:

- The unit of installation is the skill directory. A link covers everything in it; only adding or removing a whole skill needs a reinstall
- Link targets are absolute paths under the repository. If the repository moves, the links break; `--check` reports them and a normal run repairs them
- The script manages only symbolic links that point into one of this repository's skill editions (a `skills.<lang>/` directory, for any language). It never creates, overwrites, or deletes a real file or directory, and never touches a link that points elsewhere. Entries owned by others (for example `~/.claude/skills/synced/`, where Claude Code keeps skills downloaded from the user's claude.ai account) are outside its management
- A link that points into a different edition of this repository than the selected one is a wrong target: a normal run repairs it, and `--check` reports it as `differs`
- A destination entry that blocks a skill — a real file or directory, or a link pointing outside this repository — is a conflict. Conflicts are detected before anything is changed
- A link at a selected destination that points into one of this repository's skill editions, for a skill that does not exist in the selected edition, is stale. A normal run removes it; `--check` reports it. Only links into this repository are ever removed

Non-goals: copying skill files, installing rules (`install-rules` links them), deleting real files or directories, managing plugin skills or claude.ai-synced skills, watch mode, Windows support.

Validation:

- `skills.<lang>` must exist. Every subdirectory of it is a skill: it must contain a `SKILL.md` whose frontmatter, read as simple `key: value` lines (no YAML library), has a non-empty `name` equal to the directory name and a non-empty `description`. A non-blank frontmatter line without a colon, a frontmatter with no closing `---`, and a key given twice are errors, not lines to skip or overwrite. Other frontmatter keys are allowed. A skill named `synced` (in any capitalisation) is rejected when `claude` is a selected destination, because Claude Code reserves that name under `~/.claude/skills/`; with `--tool cursor` only, it is an ordinary skill

Done conditions:

1. Into an empty home, with `--tool` omitted, every skill in the selected edition (`skills.en` by default) is linked at both destinations, and every link resolves to that skill's directory in the repository
2. Running it twice in a row creates, repairs, and removes nothing on the second run
3. `--check` exits successfully on the installed state, and exits with an error naming the path when a link is missing, points at the wrong target, or is stale, when a blocking entry conflicts, and naming the directory alone when a destination directory itself is missing
4. On invalid input or any conflict, it exits with an error and changes nothing: no link is created, repaired, or removed
5. Entries the script does not own — real files and directories, links pointing outside this repository, and `synced/` — are identical before and after every run, including failed runs
6. With `--tool cursor` or `--tool claude`, only that destination is linked, checked, repaired, or cleaned. The other destination is identical before and after, including when the run fails. An unknown or repeated `--tool` changes nothing

## install-rules

Purpose: link the deliverables `build-rules` already wrote (`.cursor/rules/<name>.mdc` and `.claude/rules/<name>.md`) into the home rule directories (`~/.cursor/rules/` and `~/.claude/rules/`), one symbolic link per file. Installation does not generate or copy those files; they stay under `.cursor/` and `.claude/` in the repository.

Input/output contract:

- The set of rules is the subdirectories of `rules.<lang>/`. For each selected destination that rule's deliverable must already exist; a missing one is an error that says to run `build-rules`, and the run changes nothing. Deliverable files are never modified
- Link targets are absolute paths under the repository. If the repository moves, the links break; `--check` reports them and a normal run repairs them
- The script manages only symbolic links that point at a deliverable under `.cursor/rules/` or `.claude/rules/`. It never creates, overwrites, or deletes a real file or directory, and never touches a link that points elsewhere
- A destination entry that blocks a rule file — a real file or directory, or a link that does not point at a deliverable — is a conflict. Conflicts are detected before anything is changed
- A link at a selected destination that points at a deliverable for a rule no longer in `rules.<lang>/` is stale. A normal run removes the link; `--check` reports it. Only such links are removed; the deliverable in the repository stays

Non-goals: generating the deliverables (`build-rules` does that), copying bytes into the home directory, deleting real files or directories, deleting deliverables from the repository, translation, watch mode, Windows support.

Done conditions:

1. Into an empty home, with `--tool` omitted, every rule in the selected edition (`rules.en` by default) is linked at both destinations, and every link resolves to that rule's deliverable in the repository
2. Running it twice in a row creates, repairs, and removes nothing on the second run
3. `--check` exits successfully on the installed state, and exits with an error naming the path when a link is missing, points at the wrong deliverable, or is stale, when a blocking entry conflicts, and naming the directory alone when a destination directory itself is missing
4. On a missing `rules.<lang>`, a missing deliverable, or any conflict, it exits with an error and changes nothing: no link is created, repaired, or removed, and no deliverable is modified
5. Entries the script does not own — real files and directories, and links that do not point at a deliverable — are identical before and after every run, including failed runs
6. With `--tool cursor` or `--tool claude`, only that destination is linked, checked, repaired, or cleaned, and only that destination's deliverable is required. The other destination is identical before and after, including when the run fails. An unknown or repeated `--tool` changes nothing

## translate-rules

Purpose: translate the rule edition `rules.<from>/` into `rules.<to>/`. The defaults are `--from ja` and `--to en`: the Japanese canonical sources into the English edition. Which editions exist and which one the agents follow are separate choices (`build-rules` and the install scripts select one with `--lang`); this script only translates.

Input/output contract:

- The scope is `body.md` and the `description` in `meta.json`. `basis.md` (the rationale) is a document for the approver and is out of scope
- The output is `rules.<to>/<name>/body.md` and `rules.<to>/<name>/meta.json` only
- `description` is translated. The `cursor` namespace is copied as the same JSON, never translated: when only `cursor` changed, `meta.json` is rewritten with the new `cursor` and the previous target description, without a translator call. Headings and identifiers that are already in the target language stay as written
- Line contract: the target text has exactly one line for each source line, in the same order. A blank line stays blank, and each line keeps its Markdown marker (heading level, list marker, table row, code fence). Punctuation follows the source: no trailing period is added where the source has none. Source-language text inside a code fence, including a comment, is translated; code tokens and string literals stay. This contract is what makes keeping the previous target text mechanical
- The baseline is taken from git, not from a stored copy. For each rule, the base commit is the last commit that changed `rules.<to>/<name>/body.md`. The previous source is `rules.<from>/<name>/` at that commit and the previous target is `rules.<to>/<name>/` at that same commit (not the working tree), so the pair always matches line for line. The target edition must be committed after it is translated, which is also when it is reviewed
- A rule is a target when its current source (`body.md` or `description`) differs from the previous source, or when `rules.<to>/<name>/` does not exist (it is then translated in full). Rule names on the command line narrow the run to those rules; an unknown name is an error
- Where the source is unchanged, the previous target is kept byte for byte: each unchanged line takes the previous target line at the same position, and only changed or added lines take the new translation. The translator receives the whole current source and, for consistent terms, the previous target of the unchanged lines only, as [source, target] pairs. The old target of a changed line is never shown, because the model then copies the old line instead of translating the new source
- A rule whose `rules.<to>/<name>/` has uncommitted changes is an error (commit or discard, then rerun), and so is a base pair whose line counts differ; deleting `rules.<to>/<name>/` makes the rule a full translation. Nothing is retranslated in full silently
- The translator is the Claude Code command `claude -p` with the Sonnet model, using the login already on the machine (`--bare` is not used: it reads only `ANTHROPIC_API_KEY`, never the login). The model and the prompt are constants in `scripts/translator.py`, shared with translate-skills; that module is their only definition
- The translator runs isolated: its working directory is an empty temporary directory, and it is started with `--tools "" --strict-mcp-config --setting-sources "" --disable-slash-commands --no-session-persistence --system-prompt <prompt>`. CLAUDE.md, rules, hooks, MCP servers, and skills are not loaded, and it has no tool with which to touch files
- One rule is one translator call, and calls run one at a time. The request on standard input and the answer on standard output are a JSON object with a `description` string and a `body` array holding one string per line (plain lines let the model merge the description into the title heading). A rule that is not a target makes no call
- A call fails when the command is missing, exits non-zero, exceeds the timeout (120 seconds by default, `--timeout <seconds>`), or prints output that breaks the contract: empty output, output that is not a JSON object of that shape, a different line count or Markdown marker, source-language characters left in the text, or an empty description. A failed call is not retried; the run is all or nothing, so rerunning is safe. A timed-out translator is killed together with its children; if that kill fails, the error names the process
- All targets are translated and validated before anything is written. If any rule fails, `rules.<to>/` is left as it was. Files are written through a temporary file and replaced, so an interrupted run leaves no half-written file. The source edition is validated by the shared `rule_source.py` before any call
- Progress is reported as it goes, one line per rule (translating, copying `cursor`, or unchanged), because a run of several rules takes a minute or more. A run with no targets says so and writes nothing

Non-goals: Google Translate, DeepL, and any translator that requires an API key; removing `rules.<to>/<name>/` when a rule is removed from `rules.<from>/` (done by hand); git operations that change the repository (the script only reads history; committing is the user's); parallel calls; watch mode.

Done conditions:

1. A changed rule produces a target text in which every unchanged source line keeps its previous target byte for byte
2. With no change under `rules.<from>/`, a run makes no translator call and writes nothing
3. On any failed call or invalid input, it exits with an error naming the rule, the cause, and the next action, and `rules.<to>/` is identical before and after
4. The translator starts without CLAUDE.md, rules, hooks, MCP servers, skills, or tools
5. It runs on both Mac and Windows

## translate-skills

Purpose: translate the skill edition `skills.<from>/` into `skills.<to>/`. The defaults are `--from ja` and `--to en`: the Japanese canonical sources into the English edition. Which edition `install-skills` links is that script's own `--lang` choice; this script only translates.

Input/output contract:

- One translator call is one Markdown file, using the same JSON shape, model, prompt, and isolation flags as translate-rules (`scripts/translator.py`). A skill is not one call: a long combined request is outside the line contract
- `SKILL.md` translates `description` and the body. `name` stays the directory name and is not sent. Other frontmatter keys are copied. `basis.md` is not part of the edition. A file that is not Markdown is copied byte for byte and makes no call
- Every line of a Markdown file is sent, including a line inside a code fence. Source-language text there is translated, including a comment; code tokens and string literals stay; a fence marker stays a fence marker; text already in the target language stays (the line contract in `scripts/translator.py`)
- The line contract, the git baseline, and the splice are per file. The baseline is the last commit that changed `skills.<to>/<skill>/<path>`. Unchanged lines keep the previous target byte for byte. The old target of a changed line is not sent. Uncommitted changes under `skills.<to>/<skill>/` are an error and the run writes nothing
- Calls run `--jobs` at a time (default 4; below 1 is an error). The first line reports the file count and the job count; then one line per file (translating, copying, or unchanged). A failed call stops the calls still running, starts no new call, and leaves `skills.<to>/` unchanged. A process that could not be stopped is named on its own line with the next action (stop it by hand)
- `SKILL.md` is validated with `scripts/skill_source.py`, the same lines install-skills uses, before any call

Non-goals: installing an edition (`install-skills` does that), translating `basis.md`, one request that holds every file, removing `skills.<to>/<skill>/` when a skill is removed from `skills.<from>/` (done by hand), parallel calls inside translate-rules (that command stays one call at a time).

## How this specification is kept

It records the "why" and the contracts. The details of behavior have their canonical source in the tests, and the method of implementation in the code.
