# Test specification for install-rules.
#
# The public seam is the install-rules command: exit code, stdout, stderr,
# and the symbolic links under --home. One behavior per test. The bytes
# behind a link are the files build-rules already wrote under the
# repository's .cursor/rules and .claude/rules.

import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from support import install_scripts

NAME = "install-rules"
DESTINATIONS = (
    (".claude/rules", ".md"),
    (".cursor/rules", ".mdc"),
)
CHECK_NEXT = (
    "run without --check to install the links; "
    "conflicting entries must be removed by hand."
)


def run_install(root: Path, home: Path, *extra: str) -> subprocess.CompletedProcess:
    """Run install-rules. The fixtures are Japanese editions, so --lang ja is
    passed unless the test passes its own --lang."""
    lang = [] if "--lang" in extra else ["--lang", "ja"]
    return subprocess.run(
        [sys.executable, str(install_scripts(root) / NAME), "--home", str(home),
         *lang, *extra],
        capture_output=True, text=True,
    )


def make_dirs() -> tuple[Path, Path]:
    root = Path(tempfile.mkdtemp(prefix="install-rules-test-")).resolve()
    home = Path(tempfile.mkdtemp(prefix="install-rules-home-")).resolve()
    return root, home


def write_rule(root: Path, name: str, cursor: bytes | None = None, claude: bytes | None = None) -> None:
    (root / "rules.ja" / name).mkdir(parents=True)
    if cursor is not None:
        cursor_path = root / ".cursor" / "rules" / f"{name}.mdc"
        cursor_path.parent.mkdir(parents=True, exist_ok=True)
        cursor_path.write_bytes(cursor)
    if claude is not None:
        claude_path = root / ".claude" / "rules" / f"{name}.md"
        claude_path.parent.mkdir(parents=True, exist_ok=True)
        claude_path.write_bytes(claude)


def link_paths(
    names: list[str],
    destinations: tuple[tuple[str, str], ...] = DESTINATIONS,
) -> list[str]:
    paths = []
    for name in names:
        for dest, ext in destinations:
            paths.append(f"{dest}/{name}{ext}")
    return paths


def install_report(
    home: Path,
    names: list[str],
    destinations: tuple[tuple[str, str], ...] = DESTINATIONS,
) -> str:
    paths = link_paths(names, destinations)
    summary = f"installed {len(paths)} files from rules.ja under {home}"
    return summary + "\n" + "".join(f"{path}\n" for path in paths)


def check_report(
    home: Path,
    names: list[str],
    destinations: tuple[tuple[str, str], ...] = DESTINATIONS,
) -> str:
    paths = link_paths(names, destinations)
    summary = (
        f"checked {len(paths)} links from rules.ja under {home}; "
        "all match; wrote nothing"
    )
    return summary + "\n" + "".join(f"{path}\n" for path in paths)


def check_failure(*problems: str) -> str:
    body = "".join(f"{problem}\n" for problem in problems)
    return (
        "links do not match rules.ja. --check changes nothing.\n"
        f"{body}"
        f"{CHECK_NEXT}\n"
    )


def home_entries(home: Path) -> dict:
    entries = {}
    for path in sorted(home.rglob("*")):
        rel = path.relative_to(home).as_posix()
        if path.is_symlink():
            entries[rel] = ("symlink", path.readlink())
        elif path.is_dir():
            entries[rel] = ("dir",)
        else:
            entries[rel] = ("file", path.read_bytes())
    return entries


class FreshInstallTest(unittest.TestCase):
    def test_links_every_rule_at_both_destinations(self):
        root, home = make_dirs()
        self.addCleanup(shutil.rmtree, root, True)
        self.addCleanup(shutil.rmtree, home, True)
        write_rule(root, "alpha", b"cursor-alpha\n", b"claude-alpha\n")
        write_rule(root, "beta", b"cursor-beta\n", b"claude-beta\n")

        result = run_install(root, home)

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertEqual(result.stdout, install_report(home, ["alpha", "beta"]))
        self.assertEqual(result.stderr, "")
        expected = {
            ".claude/rules/alpha.md": (root / ".claude" / "rules" / "alpha.md", b"claude-alpha\n"),
            ".cursor/rules/alpha.mdc": (root / ".cursor" / "rules" / "alpha.mdc", b"cursor-alpha\n"),
            ".claude/rules/beta.md": (root / ".claude" / "rules" / "beta.md", b"claude-beta\n"),
            ".cursor/rules/beta.mdc": (root / ".cursor" / "rules" / "beta.mdc", b"cursor-beta\n"),
        }
        for rel, (target, payload) in expected.items():
            link = home / rel
            self.assertTrue(link.is_symlink(), msg=rel)
            self.assertTrue(link.readlink().is_absolute(), msg=link.readlink())
            self.assertEqual(link.readlink(), target)
            self.assertEqual(link.read_bytes(), payload)

    def test_relative_script_path_still_links_with_an_absolute_target(self):
        root, home = make_dirs()
        self.addCleanup(shutil.rmtree, root, True)
        self.addCleanup(shutil.rmtree, home, True)
        write_rule(root, "alpha", b"cursor-alpha\n", b"claude-alpha\n")
        install_scripts(root)

        result = subprocess.run(
            [sys.executable, "scripts/install-rules", "--home", str(home), "--lang", "ja"],
            cwd=root, capture_output=True, text=True,
        )

        link = home / ".claude" / "rules" / "alpha.md"
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertTrue(link.readlink().is_absolute(), msg=link.readlink())
        self.assertEqual(link.read_bytes(), b"claude-alpha\n")


class IdempotencyTest(unittest.TestCase):
    def test_second_run_creates_repairs_and_removes_nothing(self):
        root, home = make_dirs()
        self.addCleanup(shutil.rmtree, root, True)
        self.addCleanup(shutil.rmtree, home, True)
        write_rule(root, "alpha", b"cursor-alpha\n", b"claude-alpha\n")
        self.assertEqual(run_install(root, home).returncode, 0)
        before = home_entries(home)

        result = run_install(root, home)

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertEqual(result.stdout, install_report(home, ["alpha"]))
        self.assertEqual(result.stderr, "")
        self.assertNotIn("removed:", result.stdout)
        self.assertEqual(home_entries(home), before)


class CheckModeTest(unittest.TestCase):
    def test_check_passes_on_installed_state_and_writes_nothing(self):
        root, home = make_dirs()
        self.addCleanup(shutil.rmtree, root, True)
        self.addCleanup(shutil.rmtree, home, True)
        write_rule(root, "alpha", b"cursor-alpha\n", b"claude-alpha\n")
        self.assertEqual(run_install(root, home).returncode, 0)
        before = home_entries(home)

        result = run_install(root, home, "--check")

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertEqual(result.stdout, check_report(home, ["alpha"]))
        self.assertEqual(result.stderr, "")
        self.assertEqual(home_entries(home), before)

    def test_check_names_a_missing_link(self):
        root, home = make_dirs()
        self.addCleanup(shutil.rmtree, root, True)
        self.addCleanup(shutil.rmtree, home, True)
        write_rule(root, "alpha", b"cursor-alpha\n", b"claude-alpha\n")
        self.assertEqual(run_install(root, home).returncode, 0)
        (home / ".claude" / "rules" / "alpha.md").unlink()
        before = home_entries(home)

        result = run_install(root, home, "--check")

        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertEqual(result.stderr, check_failure("missing: .claude/rules/alpha.md"))
        self.assertEqual(home_entries(home), before)

    def test_check_names_a_wrong_target(self):
        root, home = make_dirs()
        self.addCleanup(shutil.rmtree, root, True)
        self.addCleanup(shutil.rmtree, home, True)
        write_rule(root, "alpha", b"cursor-alpha\n", b"claude-alpha\n")
        write_rule(root, "beta", b"cursor-beta\n", b"claude-beta\n")
        self.assertEqual(run_install(root, home).returncode, 0)
        wrong = home / ".cursor" / "rules" / "alpha.mdc"
        wrong.unlink()
        wrong.symlink_to(root / ".cursor" / "rules" / "beta.mdc")
        before = home_entries(home)

        result = run_install(root, home, "--check")

        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertEqual(result.stderr, check_failure("differs: .cursor/rules/alpha.mdc"))
        self.assertEqual(home_entries(home), before)

    def test_check_names_a_stale_link(self):
        root, home = make_dirs()
        self.addCleanup(shutil.rmtree, root, True)
        self.addCleanup(shutil.rmtree, home, True)
        write_rule(root, "alpha", b"cursor-alpha\n", b"claude-alpha\n")
        write_rule(root, "beta", b"cursor-beta\n", b"claude-beta\n")
        self.assertEqual(run_install(root, home).returncode, 0)
        shutil.rmtree(root / "rules.ja" / "beta")
        before = home_entries(home)

        result = run_install(root, home, "--check")

        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertEqual(
            result.stderr,
            check_failure("stale: .claude/rules/beta.md", "stale: .cursor/rules/beta.mdc"),
        )
        self.assertEqual(home_entries(home), before)
        self.assertTrue((root / ".cursor" / "rules" / "beta.mdc").is_file())

    def test_check_names_a_conflicting_directory(self):
        root, home = make_dirs()
        self.addCleanup(shutil.rmtree, root, True)
        self.addCleanup(shutil.rmtree, home, True)
        write_rule(root, "alpha", b"cursor-alpha\n", b"claude-alpha\n")
        self.assertEqual(run_install(root, home).returncode, 0)
        link = home / ".claude" / "rules" / "alpha.md"
        link.unlink()
        link.mkdir()
        (link / "owned.txt").write_text("keep\n", encoding="utf-8")
        before = home_entries(home)

        result = run_install(root, home, "--check")

        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertEqual(result.stderr, check_failure("conflict: .claude/rules/alpha.md"))
        self.assertEqual(home_entries(home), before)

    def test_check_names_a_missing_destination_directory_once(self):
        root, home = make_dirs()
        self.addCleanup(shutil.rmtree, root, True)
        self.addCleanup(shutil.rmtree, home, True)
        write_rule(root, "alpha", b"cursor-alpha\n", b"claude-alpha\n")
        write_rule(root, "beta", b"cursor-beta\n", b"claude-beta\n")
        before = home_entries(home)

        result = run_install(root, home, "--check")

        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertEqual(
            result.stderr,
            check_failure("missing: .claude/rules", "missing: .cursor/rules"),
        )
        self.assertNotIn("alpha", result.stderr)
        self.assertNotIn("beta", result.stderr)
        self.assertEqual(home_entries(home), before)

    def test_check_names_a_foreign_symlink_as_a_conflict(self):
        root, home = make_dirs()
        outside = Path(tempfile.mkdtemp(prefix="install-rules-outside-"))
        self.addCleanup(shutil.rmtree, root, True)
        self.addCleanup(shutil.rmtree, home, True)
        self.addCleanup(shutil.rmtree, outside, True)
        write_rule(root, "alpha", b"cursor-alpha\n", b"claude-alpha\n")
        (home / ".claude" / "rules").mkdir(parents=True)
        (home / ".cursor" / "rules").mkdir(parents=True)
        (home / ".claude" / "rules" / "alpha.md").symlink_to(outside)
        (home / ".cursor" / "rules" / "alpha.mdc").symlink_to(root / ".cursor" / "rules" / "alpha.mdc")
        before = home_entries(home)

        result = run_install(root, home, "--check")

        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertEqual(result.stderr, check_failure("conflict: .claude/rules/alpha.md"))
        self.assertEqual(home_entries(home), before)


class InvalidInputTest(unittest.TestCase):
    def test_missing_rules_dir(self):
        root, home = make_dirs()
        self.addCleanup(shutil.rmtree, root, True)
        self.addCleanup(shutil.rmtree, home, True)
        before = home_entries(home)

        result = run_install(root, home)

        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertEqual(result.stderr, "rules.ja: missing rules.ja. create rules.ja\n")
        self.assertNotIn("Traceback", result.stderr)
        self.assertEqual(home_entries(home), before)

    def test_missing_deliverable_changes_nothing(self):
        root, home = make_dirs()
        self.addCleanup(shutil.rmtree, root, True)
        self.addCleanup(shutil.rmtree, home, True)
        write_rule(root, "alpha", b"cursor-alpha\n", b"claude-alpha\n")
        write_rule(root, "beta", cursor=None, claude=b"claude-beta\n")
        before = home_entries(home)

        result = run_install(root, home)

        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertEqual(
            result.stderr,
            "beta: missing .cursor/rules/beta.mdc. run build-rules\n",
        )
        self.assertNotIn("Traceback", result.stderr)
        self.assertEqual(home_entries(home), before)
        self.assertEqual((root / ".claude" / "rules" / "alpha.md").read_bytes(), b"claude-alpha\n")


class UnownedEntriesTest(unittest.TestCase):
    def test_successful_run_leaves_an_unrelated_file(self):
        root, home = make_dirs()
        self.addCleanup(shutil.rmtree, root, True)
        self.addCleanup(shutil.rmtree, home, True)
        write_rule(root, "alpha", b"cursor-alpha\n", b"claude-alpha\n")
        notes = home / ".cursor" / "rules" / "notes.mdc"
        notes.parent.mkdir(parents=True)
        notes.write_bytes(b"mine\n")

        result = run_install(root, home)

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertEqual(notes.read_bytes(), b"mine\n")
        self.assertFalse(notes.is_symlink())


class NormalRunTest(unittest.TestCase):
    def test_removes_stale_links(self):
        root, home = make_dirs()
        self.addCleanup(shutil.rmtree, root, True)
        self.addCleanup(shutil.rmtree, home, True)
        write_rule(root, "alpha", b"cursor-alpha\n", b"claude-alpha\n")
        write_rule(root, "beta", b"cursor-beta\n", b"claude-beta\n")
        self.assertEqual(run_install(root, home).returncode, 0)
        shutil.rmtree(root / "rules.ja" / "beta")

        result = run_install(root, home)

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertEqual(
            result.stdout,
            install_report(home, ["alpha"])
            + "removed: .claude/rules/beta.md\n"
            + "removed: .cursor/rules/beta.mdc\n",
        )
        self.assertEqual(result.stderr, "")
        self.assertFalse(os.path.lexists(home / ".claude" / "rules" / "beta.md"))
        self.assertFalse(os.path.lexists(home / ".cursor" / "rules" / "beta.mdc"))
        self.assertEqual(
            (home / ".claude" / "rules" / "alpha.md").readlink(),
            root / ".claude" / "rules" / "alpha.md",
        )
        self.assertTrue((root / ".cursor" / "rules" / "beta.mdc").is_file())

    def test_repairs_links_broken_by_moving_the_repository(self):
        root, home = make_dirs()
        self.addCleanup(shutil.rmtree, home, True)
        write_rule(root, "alpha", b"cursor-alpha\n", b"claude-alpha\n")
        self.assertEqual(run_install(root, home).returncode, 0)
        moved = root.parent / f"{root.name}-moved"
        shutil.move(root, moved)
        self.addCleanup(shutil.rmtree, moved, True)
        old = root / ".claude" / "rules" / "alpha.md"
        self.assertEqual((home / ".claude" / "rules" / "alpha.md").readlink(), old)

        result = run_install(moved, home)

        target = moved / ".claude" / "rules" / "alpha.md"
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertEqual(result.stdout, install_report(home, ["alpha"]))
        self.assertEqual(result.stderr, "")
        self.assertEqual((home / ".claude" / "rules" / "alpha.md").readlink(), target)
        self.assertEqual(
            (home / ".cursor" / "rules" / "alpha.mdc").readlink(),
            moved / ".cursor" / "rules" / "alpha.mdc",
        )
        self.assertEqual((home / ".claude" / "rules" / "alpha.md").read_bytes(), b"claude-alpha\n")

    def test_removes_stale_links_that_still_point_at_the_old_repository(self):
        root, home = make_dirs()
        self.addCleanup(shutil.rmtree, home, True)
        write_rule(root, "alpha", b"cursor-alpha\n", b"claude-alpha\n")
        write_rule(root, "beta", b"cursor-beta\n", b"claude-beta\n")
        self.assertEqual(run_install(root, home).returncode, 0)
        moved = root.parent / f"{root.name}-moved"
        shutil.move(root, moved)
        self.addCleanup(shutil.rmtree, moved, True)
        shutil.rmtree(moved / "rules.ja" / "beta")

        result = run_install(moved, home)

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertEqual(
            result.stdout,
            install_report(home, ["alpha"])
            + "removed: .claude/rules/beta.md\n"
            + "removed: .cursor/rules/beta.mdc\n",
        )
        self.assertEqual(
            (home / ".claude" / "rules" / "alpha.md").readlink(),
            moved / ".claude" / "rules" / "alpha.md",
        )
        self.assertFalse(os.path.lexists(home / ".claude" / "rules" / "beta.md"))
        self.assertFalse(os.path.lexists(home / ".cursor" / "rules" / "beta.mdc"))

    def test_conflict_blocks_the_run_and_changes_nothing(self):
        root, home = make_dirs()
        self.addCleanup(shutil.rmtree, root, True)
        self.addCleanup(shutil.rmtree, home, True)
        write_rule(root, "alpha", b"cursor-alpha\n", b"claude-alpha\n")
        write_rule(root, "beta", b"cursor-beta\n", b"claude-beta\n")
        write_rule(root, "gamma", b"cursor-gamma\n", b"claude-gamma\n")
        self.assertEqual(run_install(root, home).returncode, 0)
        shutil.rmtree(root / "rules.ja" / "gamma")
        wrong = home / ".cursor" / "rules" / "alpha.mdc"
        wrong.unlink()
        wrong.symlink_to(root / ".cursor" / "rules" / "beta.mdc")
        blocked = home / ".claude" / "rules" / "alpha.md"
        blocked.unlink()
        blocked.mkdir()
        (blocked / "owned.txt").write_text("keep\n", encoding="utf-8")
        before = home_entries(home)

        result = run_install(root, home)

        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertEqual(
            result.stderr,
            "alpha: conflict at .claude/rules/alpha.md. "
            "remove the conflicting entry by hand\n",
        )
        self.assertNotIn("Traceback", result.stderr)
        self.assertEqual(home_entries(home), before)

    def test_foreign_symlink_is_a_conflict_and_changes_nothing(self):
        root, home = make_dirs()
        outside = Path(tempfile.mkdtemp(prefix="install-rules-outside-"))
        self.addCleanup(shutil.rmtree, root, True)
        self.addCleanup(shutil.rmtree, home, True)
        self.addCleanup(shutil.rmtree, outside, True)
        write_rule(root, "alpha", b"cursor-alpha\n", b"claude-alpha\n")
        write_rule(root, "beta", b"cursor-beta\n", b"claude-beta\n")
        (home / ".claude" / "rules").mkdir(parents=True)
        (home / ".claude" / "rules" / "alpha.md").symlink_to(outside)
        before = home_entries(home)

        result = run_install(root, home)

        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertEqual(
            result.stderr,
            "alpha: conflict at .claude/rules/alpha.md. "
            "remove the conflicting entry by hand\n",
        )
        self.assertEqual(home_entries(home), before)


class LangTest(unittest.TestCase):
    """--lang picks the rule set rules.<lang>; the default is en."""

    def setUp(self):
        self.root, self.home = make_dirs()
        self.addCleanup(shutil.rmtree, self.root, True)
        self.addCleanup(shutil.rmtree, self.home, True)
        write_rule(self.root, "alpha", b"cursor-alpha\n", b"claude-alpha\n")
        write_rule(self.root, "beta", b"cursor-beta\n", b"claude-beta\n")
        # alpha is the only rule in the English edition.
        (self.root / "rules.en" / "alpha").mkdir(parents=True)

    def test_default_installs_the_english_rule_set(self):
        result = run_install(self.root, self.home, "--lang", "en")
        bare = subprocess.run(
            [sys.executable, str(self.root / "scripts" / NAME), "--home", str(self.home), "--check"],
            capture_output=True, text=True,
        )

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertEqual(
            result.stdout.splitlines()[0],
            f"installed 2 files from rules.en under {self.home}",
        )
        self.assertFalse((self.home / ".claude" / "rules" / "beta.md").exists())
        self.assertEqual(bare.returncode, 0, msg=bare.stderr)
        self.assertEqual(bare.stdout, check_report(self.home, ["alpha"]).replace("rules.ja", "rules.en"))

    def test_a_link_to_a_rule_missing_from_the_selected_edition_is_stale(self):
        self.assertEqual(run_install(self.root, self.home).returncode, 0)

        check = run_install(self.root, self.home, "--lang", "en", "--check")
        self.assertEqual(check.returncode, 1)
        self.assertEqual(
            check.stderr,
            check_failure(
                "stale: .claude/rules/beta.md", "stale: .cursor/rules/beta.mdc"
            ).replace("rules.ja", "rules.en"),
        )

        fixed = run_install(self.root, self.home, "--lang", "en")
        self.assertEqual(fixed.returncode, 0, msg=fixed.stderr)
        self.assertIn("removed: .claude/rules/beta.md", fixed.stdout)
        self.assertTrue((self.root / ".claude" / "rules" / "beta.md").is_file())

    def test_a_missing_edition_changes_nothing(self):
        result = run_install(self.root, self.home, "--lang", "fr")
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stderr, "rules.fr: missing rules.fr. create rules.fr\n")
        self.assertEqual(home_entries(self.home), {})

    def test_a_repeated_lang_changes_nothing(self):
        result = run_install(self.root, self.home, "--lang", "en", "--lang", "ja")
        self.assertEqual(result.returncode, 1)
        self.assertEqual(
            result.stderr, "lang: --lang was given more than once. pass it once\n")
        self.assertEqual(home_entries(self.home), {})


class ToolSelectionTest(unittest.TestCase):
    def test_cursor_installs_only_the_cursor_destination(self):
        root, home = make_dirs()
        self.addCleanup(shutil.rmtree, root, True)
        self.addCleanup(shutil.rmtree, home, True)
        write_rule(root, "alpha", b"cursor-alpha\n", b"claude-alpha\n")
        write_rule(root, "beta", b"cursor-beta\n", b"claude-beta\n")

        result = run_install(root, home, "--tool", "cursor")

        cursor = ((".cursor/rules", ".mdc"),)
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertEqual(result.stdout, install_report(home, ["alpha", "beta"], cursor))
        self.assertEqual(result.stderr, "")
        self.assertFalse((home / ".claude").exists())
        self.assertEqual(
            (home / ".cursor" / "rules" / "alpha.mdc").readlink(),
            root / ".cursor" / "rules" / "alpha.mdc",
        )

    def test_claude_installs_only_the_claude_destination(self):
        root, home = make_dirs()
        self.addCleanup(shutil.rmtree, root, True)
        self.addCleanup(shutil.rmtree, home, True)
        write_rule(root, "alpha", b"cursor-alpha\n", b"claude-alpha\n")

        result = run_install(root, home, "--tool", "claude")

        claude = ((".claude/rules", ".md"),)
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertEqual(result.stdout, install_report(home, ["alpha"], claude))
        self.assertEqual(result.stderr, "")
        self.assertFalse((home / ".cursor").exists())
        self.assertEqual(
            (home / ".claude" / "rules" / "alpha.md").readlink(),
            root / ".claude" / "rules" / "alpha.md",
        )

    def test_conflict_on_the_unselected_side_does_not_block(self):
        root, home = make_dirs()
        self.addCleanup(shutil.rmtree, root, True)
        self.addCleanup(shutil.rmtree, home, True)
        write_rule(root, "alpha", b"cursor-alpha\n", b"claude-alpha\n")
        blocked = home / ".claude" / "rules" / "alpha.md"
        blocked.parent.mkdir(parents=True)
        blocked.mkdir()
        (blocked / "owned.txt").write_text("keep\n", encoding="utf-8")

        def claude_entries() -> dict:
            return {
                key: value
                for key, value in home_entries(home).items()
                if key == ".claude" or key.startswith(".claude/")
            }

        before = claude_entries()

        result = run_install(root, home, "--tool", "cursor")

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertEqual(
            (home / ".cursor" / "rules" / "alpha.mdc").readlink(),
            root / ".cursor" / "rules" / "alpha.mdc",
        )
        self.assertEqual(claude_entries(), before)

    def test_check_names_only_the_selected_destination(self):
        root, home = make_dirs()
        self.addCleanup(shutil.rmtree, root, True)
        self.addCleanup(shutil.rmtree, home, True)
        write_rule(root, "alpha", b"cursor-alpha\n", b"claude-alpha\n")
        before = home_entries(home)

        result = run_install(root, home, "--check", "--tool", "cursor")

        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertEqual(result.stderr, check_failure("missing: .cursor/rules"))
        self.assertNotIn(".claude", result.stderr)
        self.assertEqual(home_entries(home), before)

    def test_unknown_tool_changes_nothing(self):
        root, home = make_dirs()
        self.addCleanup(shutil.rmtree, root, True)
        self.addCleanup(shutil.rmtree, home, True)
        (home / "marker.txt").write_text("keep\n", encoding="utf-8")
        before = home_entries(home)

        result = run_install(root, home, "--tool", "both")

        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertEqual(
            result.stderr,
            'tool: unknown tool "both". pass --tool cursor or --tool claude\n',
        )
        self.assertEqual(home_entries(home), before)

    def test_repeated_tool_changes_nothing(self):
        root, home = make_dirs()
        self.addCleanup(shutil.rmtree, root, True)
        self.addCleanup(shutil.rmtree, home, True)
        write_rule(root, "alpha", b"cursor-alpha\n", b"claude-alpha\n")
        (home / "marker.txt").write_text("keep\n", encoding="utf-8")
        before = home_entries(home)

        result = run_install(root, home, "--tool", "cursor", "--tool", "claude")

        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertEqual(
            result.stderr,
            "tool: --tool was given more than once. pass it once\n",
        )
        self.assertEqual(home_entries(home), before)

    def test_cursor_does_not_require_the_claude_deliverable(self):
        root, home = make_dirs()
        self.addCleanup(shutil.rmtree, root, True)
        self.addCleanup(shutil.rmtree, home, True)
        write_rule(root, "alpha", cursor=b"cursor-alpha\n", claude=None)

        result = run_install(root, home, "--tool", "cursor")

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertEqual(
            (home / ".cursor" / "rules" / "alpha.mdc").read_bytes(),
            b"cursor-alpha\n",
        )
        self.assertFalse((home / ".claude").exists())

    def test_removes_stale_links_only_on_the_selected_side(self):
        root, home = make_dirs()
        self.addCleanup(shutil.rmtree, root, True)
        self.addCleanup(shutil.rmtree, home, True)
        write_rule(root, "alpha", b"cursor-alpha\n", b"claude-alpha\n")
        write_rule(root, "beta", b"cursor-beta\n", b"claude-beta\n")
        self.assertEqual(run_install(root, home).returncode, 0)
        shutil.rmtree(root / "rules.ja" / "beta")
        claude_beta = home / ".claude" / "rules" / "beta.md"

        result = run_install(root, home, "--tool", "cursor")

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("removed: .cursor/rules/beta.mdc\n", result.stdout)
        self.assertNotIn("removed: .claude/rules/beta.md", result.stdout)
        self.assertFalse(os.path.lexists(home / ".cursor" / "rules" / "beta.mdc"))
        self.assertTrue(claude_beta.is_symlink())
        self.assertEqual(claude_beta.readlink(), root / ".claude" / "rules" / "beta.md")

    def test_repairs_only_the_selected_side(self):
        root, home = make_dirs()
        self.addCleanup(shutil.rmtree, home, True)
        write_rule(root, "alpha", b"cursor-alpha\n", b"claude-alpha\n")
        self.assertEqual(run_install(root, home).returncode, 0)
        moved = root.parent / f"{root.name}-moved"
        shutil.move(root, moved)
        self.addCleanup(shutil.rmtree, moved, True)
        old = root / ".claude" / "rules" / "alpha.md"

        result = run_install(moved, home, "--tool", "cursor")

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertEqual(
            (home / ".cursor" / "rules" / "alpha.mdc").readlink(),
            moved / ".cursor" / "rules" / "alpha.mdc",
        )
        self.assertEqual((home / ".claude" / "rules" / "alpha.md").readlink(), old)

    def test_check_passes_for_the_selected_destination(self):
        root, home = make_dirs()
        self.addCleanup(shutil.rmtree, root, True)
        self.addCleanup(shutil.rmtree, home, True)
        write_rule(root, "alpha", b"cursor-alpha\n", b"claude-alpha\n")
        self.assertEqual(run_install(root, home, "--tool", "cursor").returncode, 0)
        before = home_entries(home)

        result = run_install(root, home, "--check", "--tool", "cursor")

        cursor = ((".cursor/rules", ".mdc"),)
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertEqual(result.stdout, check_report(home, ["alpha"], cursor))
        self.assertEqual(result.stderr, "")
        self.assertEqual(home_entries(home), before)


if __name__ == "__main__":
    unittest.main()
