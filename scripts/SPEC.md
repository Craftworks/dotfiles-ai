# scripts Directory Specification (SPEC)

This SPEC is the specification of the scripts directory.

It holds the scripts that process the language editions of the rules and skills: `build-rules`, `install-rules`, `install-skills`, `translate-rules`, and `translate-skills` (all implemented). The canonical sources are `rules.ja/` and `skills.ja/`; further editions (for example `rules.en/` and `skills.en/`) are generated from them by the translate scripts. Each script's purpose and options are in its `--help`.

Common to every script (the sections below do not repeat it):

- Each script is a Python 3 standard-library file with no extension and works on the repository that contains it. build-rules and the translate scripts run on Mac and Windows; the install scripts are macOS only (they use symbolic links)
- Any language whose edition directory exists can be selected (`--lang`, or `--from` and `--to`, which must differ). A language code is letters, digits, `-` and `_` only, so a value cannot leave the repository. An invalid language code, a repeated option, or an unknown option value is an error raised before anything is read or written
- A run that fails writes, creates, repairs, and removes nothing: all inputs are validated before the first change. Each error names the unit (rule, skill, or file), the cause, and the next action. Exact wording is fixed by the tests
- Reporting is part of the contract: a normal run prints a summary and every path it wrote or linked, and a successful `--check` says what it checked and that it wrote nothing. Silent success is a defect because it looks like nothing happened. A failed `--check` names each problem at the unit the operator acts on, and names a missing or empty directory once
- Rerunning a script on its own output changes nothing (idempotent)
- Building and installing rules are done back to back with the same `--lang`, because deliverables do not record which language they were built from
- The details of behavior (error text, report format, cases) are stated in the code, and the tests under `scripts/tests/` check them independently. They run each script as a subprocess inside a temporary repository. A shared module is tested directly. The automated tests never call the real `claude`

## build-rules

Purpose: generate `.cursor/rules/<name>.mdc` and `.claude/rules/<name>.md` from `rules.<lang>/<name>/`.

Contract:

- The input is the selected edition only. The output is a pure function of the input: the same input always produces the same bytes
- Generated files carry no marker header. Drift from the canonical sources is detected by `--check`, not by text inside the file
- All rules are validated first by `scripts/rule_source.py`, shared with translate-rules, so a rule is valid for both or for neither

Non-goals: translation, installation into the home directory, git operations, watch mode, incremental processing.

Note: Claude Code's rule loading reads only `paths` in frontmatter; it does not read `alwaysApply`. Files placed in `~/.claude/rules/` are loaded resident. How auto rules (description only) are handled on the home side is an open question for the install design (pending verification by measurement).

Done conditions:

1. Against the frozen snapshot of the real rules (`scripts/tests/fixtures/real/`, which holds the Japanese sources), the generated files match the expected outputs byte for byte
2. `--check` passes on matching outputs and fails on a hand-edited, missing, or absent output
3. Invalid input exits with an error and writes no output file
4. On a fixture with globs, the Claude frontmatter is `paths` with that globs string as its one list item

## install-skills and install-rules

Purpose: link the skills in `skills.<lang>/<name>/` (install-skills) or the deliverables `build-rules` wrote (install-rules) into the home directories of Cursor and Claude, one symbolic link per skill or file. Installation never copies and never generates, so the repository stays the only real files and editing a source takes effect without reinstalling. `--tool` narrows a run to one destination; the unselected destination is not created, read, or reported, and a problem there does not affect the run.

Contract:

- The script owns only symbolic links that point into this repository: any `skills.<lang>/` for install-skills, a deliverable under `.cursor/rules/` or `.claude/rules/` for install-rules. It never creates, overwrites, or deletes a real file or directory, and never touches a link that points elsewhere. Entries owned by others (for example `~/.claude/skills/synced/`, where Claude Code keeps skills synced from the user's claude.ai account) are outside its management
- Link targets are absolute paths under the repository. If the repository moves, the links break; `--check` reports them and a normal run repairs them
- A destination entry that blocks a link (a real file or directory, or a link pointing at something the script does not own) is a conflict. Conflicts are detected before anything is changed
- A link the script owns whose source no longer exists in the selected edition is stale: a normal run removes it, `--check` reports it. The repository's files stay
- install-skills: a link into a different edition than the selected one is repaired by a normal run and reported as `differs` by `--check`. Every subdirectory of `skills.<lang>` is a skill and is validated by `scripts/skill_source.py` (shared with translate-skills), which reads frontmatter as simple `key: value` lines with no YAML library. A skill named `synced` (any capitalisation) is rejected when `claude` is a selected destination, because Claude Code reserves that name; with `--tool cursor` only, it is an ordinary skill
- install-rules: the set of rules is the subdirectories of `rules.<lang>/`. For each selected destination the deliverable must already exist; a missing one is an error that says to run `build-rules`

Non-goals: copying files, deleting real files or directories, managing plugin skills or claude.ai-synced skills, translation, watch mode, Windows support. install-skills does not install rules; install-rules does not generate or delete deliverables.

Done conditions:

1. Into an empty home, every skill or rule of the selected edition is linked at both destinations, and every link resolves into the repository
2. A second run creates, repairs, and removes nothing
3. `--check` passes on the installed state, and fails naming the path for a missing, wrong, or stale link or a conflict, and naming the directory alone when a destination directory is missing
4. Invalid input, a missing source, or any conflict exits with an error and changes nothing
5. Entries the script does not own are identical before and after every run, including failed runs
6. With `--tool`, the other destination is identical before and after, including when the run fails

## translate-rules and translate-skills

Purpose: translate the edition `rules.<from>/` (or `skills.<from>/`) into `<to>`. Which editions exist and which one the agents follow are separate choices made by `--lang` on build and install; these scripts only translate.

Contract:

- The scope of translate-rules is `body.md` and the `description` in `meta.json`. The `cursor` namespace is copied as the same JSON, never translated; when only `cursor` changed, `meta.json` is rewritten without a translator call. `basis.md` is a document for the approver and is out of scope in both scripts
- translate-skills sends one Markdown file per call (`SKILL.md` translates `description` and the body; `name` stays the directory name; other frontmatter is copied). A long combined request is outside the line contract. A file that is not Markdown is copied byte for byte and makes no call. Lines inside a code fence are sent too
- Line contract: the target has exactly one line for each source line, in the same order, keeping each line's Markdown marker and following the source's punctuation. Source-language text inside a code fence, including a comment, is translated; code tokens and string literals stay. Text, headings, and identifiers already in the target language stay as written. This contract is what makes keeping the previous target text mechanical. It is defined in `scripts/translator.py`, the only definition of the model and prompt
- The baseline comes from git, not a stored copy. The base commit is the last commit that changed the target (`rules.<to>/<name>/body.md`, or `skills.<to>/<skill>/<path>` per file); the previous source and target are both read at that commit, so the pair matches line for line. The target must be committed after it is translated, which is also when it is reviewed
- A rule or file is a target when its source differs from the previous source or its target does not exist (then it is translated in full). Names on the command line narrow the run; an unknown name is an error
- Where the source is unchanged, the previous target is kept byte for byte. The translator receives the whole current source and, for consistent terms, the previous target of the unchanged lines only, as [source, target] pairs. The old target of a changed line is never shown, because the model then copies the old line instead of translating the new source
- Uncommitted changes in the target, or a base pair whose line counts differ, are an error. Deleting the target makes it a full translation. Nothing is retranslated in full silently
- The translator is `claude -p` with the Sonnet model, using the login already on the machine (`--bare` is not used: it reads only `ANTHROPIC_API_KEY`, never the login). It runs isolated: its working directory is an empty temporary directory, and CLAUDE.md, rules, hooks, MCP servers, skills, and tools are not loaded
- The request and the answer are a JSON object with a `description` string and a `body` array of one string per line (plain lines let the model merge the description into the title heading)
- A call fails, and is not retried, when the translator is missing, exits non-zero, times out (a timed-out translator is killed together with its children; if the kill fails, the error names the process), or breaks the contract (empty or malformed output, a different line count or Markdown marker, source-language characters left, an empty description)
- All targets are translated and validated before anything is written. If any call fails, the target edition is left as it was, so rerunning is safe. Files are replaced through a temporary file, so an interrupted run leaves no half-written file. The source is validated before any call
- translate-rules makes one call per rule, one at a time. translate-skills runs `--jobs` calls at a time; a failure stops the running calls and starts no new one, and a process that could not be stopped is named with the next action (stop it by hand)
- Progress is reported as it goes, one line per rule or file, because a run takes a minute or more. A run with no targets says so and writes nothing

Non-goals: Google Translate, DeepL, and any translator that requires an API key; removing `<to>/<name>/` when a source is removed (done by hand); git operations that change the repository (the script only reads history; committing is the user's); installing an edition; parallel calls in translate-rules; watch mode.

Done conditions:

1. A changed rule or file produces a target in which every unchanged source line keeps its previous target byte for byte
2. With no change in the source, a run makes no translator call and writes nothing
3. A failed call or invalid input exits with an error naming the unit, the cause, and the next action, and the target edition is identical before and after
4. The translator starts without CLAUDE.md, rules, hooks, MCP servers, skills, or tools
5. It runs on both Mac and Windows

## How this specification is kept

It records the "why" and the contracts. The details of behavior are stated in the code, and the tests check them independently.
