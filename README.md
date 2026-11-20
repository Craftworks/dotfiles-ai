English | [日本語](README.ja.md)

# dotfiles-ai

Configuration repository for an AI-assisted development environment. This is the single source of truth for the principles, rules, and skills shared by Cursor, Claude Code, and the Muse CLI; each tool receives its configuration from here. The top-level layout mirrors the home directory it deploys to (`.cursor/`, `.claude/`).

## Roles

- **Claude CLI (Claude Code) = the hands**: implements and tests
- **Muse CLI = the secretary**: never implements. Decomposes tasks, dispatches them to the Claude CLI, manages state, and reports. Its concrete duties are still to be defined
- **The user = the approver**: judges design, vulnerabilities, performance, and cost, and approves based on evidence (test results, diffs, measurements)
- **Cursor = the approver's cockpit**: a window for reading diffs, navigating code, and approving. Cursor's own agent and cloud features are not used (GitHub operations are done by the Claude CLI via `gh`)

When the secretary's context grows long, it is written out to files; sessions themselves are disposable. Files, not conversations, are the source of truth for state, and the secretary (Muse CLI) is the single writer of state files. The web version of Muse remains as a read-only window onto those state files over SFTP.

## Current layout (v0)

```text
dotfiles-ai/
├── README.md               # this file
├── README.ja.md            # Japanese version
├── .cursor/
│   ├── rules/              # 11 Cursor rules (.mdc) plus their index README.md
│   └── skills/
│       └── commit-command/ # first shared skill (SKILL.md)
└── .claude/                # empty for now; Claude Code configuration will go here
```

## How principles are shared

- **Skills** use the Agent Skills standard (`SKILL.md`) and can be shared as-is across all three tools. Claude Code reads `~/.claude/skills/`; Cursor reads `~/.cursor/skills/` and also `~/.claude/skills/` as a compatibility path
- **Rules** differ in format per platform (Cursor uses `.mdc`, Claude Code uses `CLAUDE.md` plus rules with `paths:`, the Muse CLI uses plain Markdown). For now, the Cursor format is canonical. If distribution to the Claude and Muse sides becomes necessary, the shared text will be split out as the source of truth and wrapped in each platform's format

## Operating principles

1. **Keep the resident context lean**: instructions loaded at all times are limited to a map, verification commands, and scars from past failures; details live in layers loaded on demand (skills, project specifications)
2. **Add only in response to observed failures**: when an agent makes a mistake, do not stop at fixing the instance — promote it: a judgment miss becomes a line in a rule or skill, repeated work becomes a skill, and an exceptionless rule becomes a mechanism such as a hook
3. **Enforce exceptionless rules with mechanisms, not prompts**: when you are about to write "always do X" in a rule, its home is a hook or a linter
4. **Create roles only where context isolation pays off**: subagents are used only where parallelism, output isolation, or an unseen reviewer helps, and are built from your own frequent workflows. Do not assemble a full roster up front
5. **Control the flow**: never generate more than the approver can review

## Planned (not yet done)

- Add Claude Code configuration (CLAUDE.md, subagent definitions, hooks) under `.claude/`
- Build an index of principles (which principle falls into which layer)
- Script the deployment (install) procedure

