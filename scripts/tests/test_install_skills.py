# Test specification for install-skills.
#
# The public seam is the install-skills command: exit code, stdout, stderr,
# and the symbolic links under --home. One behavior per test.

import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
REPO_ROOT = TESTS_DIR.parents[1]
SCRIPT = REPO_ROOT / "scripts" / "install-skills"
DESTINATIONS = (".claude/skills", ".cursor/skills")


def run_build(root: Path, home: Path, *extra: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(root), "--home", str(home), *extra],
        capture_output=True, text=True,
    )


def make_dirs() -> tuple[Path, Path]:
    root = Path(tempfile.mkdtemp(prefix="install-skills-test-"))
    home = Path(tempfile.mkdtemp(prefix="install-skills-home-"))
    return root, home


def write_skill(root: Path, name: str, description: str = "A skill.") -> None:
    skill = root / "skills.ja" / name
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text(
        f"---\nname: {name}\ndescription: {description}\n---\n\nbody\n",
        encoding="utf-8",
    )
    (skill / "notes.md").write_text("aux\n", encoding="utf-8")


def link_paths(names: list[str], destinations: tuple[str, ...] = DESTINATIONS) -> list[str]:
    paths = []
    for name in names:
        for dest in destinations:
            paths.append(f"{dest}/{name}")
    return paths


def install_report(home: Path, names: list[str], destinations: tuple[str, ...] = DESTINATIONS) -> str:
    paths = link_paths(names, destinations)
    summary = f"installed {len(names)} skills from skills.ja under {home}"
    return summary + "\n" + "".join(f"{path}\n" for path in paths)


def check_report(home: Path, names: list[str], destinations: tuple[str, ...] = DESTINATIONS) -> str:
    paths = link_paths(names, destinations)
    summary = (
        f"checked {len(paths)} links from skills.ja under {home}; "
        "all match; wrote nothing"
    )
    return summary + "\n" + "".join(f"{path}\n" for path in paths)


class FreshInstallTest(unittest.TestCase):
    def test_links_every_skill_at_both_destinations(self):
        root, home = make_dirs()
        self.addCleanup(shutil.rmtree, root, True)
        self.addCleanup(shutil.rmtree, home, True)
        write_skill(root, "alpha")
        write_skill(root, "beta")

        result = run_build(root, home)

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertEqual(result.stdout, install_report(home, ["alpha", "beta"]))
        self.assertEqual(result.stderr, "")
        for name in ("alpha", "beta"):
            target = root / "skills.ja" / name
            for dest in DESTINATIONS:
                link = home / dest / name
                self.assertTrue(link.is_symlink(), msg=f"{dest}/{name} is not a symlink")
                self.assertEqual(link.readlink(), target)
                self.assertEqual((link / "notes.md").read_text(encoding="utf-8"), "aux\n")

    def test_relative_root_still_links_with_an_absolute_target(self):
        root, home = make_dirs()
        self.addCleanup(shutil.rmtree, root, True)
        self.addCleanup(shutil.rmtree, home, True)
        write_skill(root, "alpha")

        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--root", ".", "--home", str(home)],
            cwd=root,
            capture_output=True,
            text=True,
        )

        link = home / ".claude" / "skills" / "alpha"
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertTrue(link.readlink().is_absolute(), msg=link.readlink())
        self.assertEqual((link / "notes.md").read_text(encoding="utf-8"), "aux\n")


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


class IdempotencyTest(unittest.TestCase):
    def test_second_run_creates_repairs_and_removes_nothing(self):
        root, home = make_dirs()
        self.addCleanup(shutil.rmtree, root, True)
        self.addCleanup(shutil.rmtree, home, True)
        write_skill(root, "alpha")
        self.assertEqual(run_build(root, home).returncode, 0)
        before = home_entries(home)

        result = run_build(root, home)

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
        write_skill(root, "alpha")
        self.assertEqual(run_build(root, home).returncode, 0)
        before = home_entries(home)

        result = run_build(root, home, "--check")

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertEqual(result.stdout, check_report(home, ["alpha"]))
        self.assertEqual(result.stderr, "")
        self.assertEqual(home_entries(home), before)

    def test_check_names_a_missing_link(self):
        root, home = make_dirs()
        self.addCleanup(shutil.rmtree, root, True)
        self.addCleanup(shutil.rmtree, home, True)
        write_skill(root, "alpha")
        self.assertEqual(run_build(root, home).returncode, 0)
        (home / ".claude" / "skills" / "alpha").unlink()
        before = home_entries(home)

        result = run_build(root, home, "--check")

        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertEqual(
            result.stderr,
            "links do not match skills.ja. --check changes nothing.\n"
            "missing: .claude/skills/alpha\n"
            "run without --check to install the links; "
            "conflicting entries must be removed by hand.\n",
        )
        self.assertEqual(home_entries(home), before)

    def test_check_names_a_wrong_target(self):
        root, home = make_dirs()
        self.addCleanup(shutil.rmtree, root, True)
        self.addCleanup(shutil.rmtree, home, True)
        write_skill(root, "alpha")
        write_skill(root, "beta")
        self.assertEqual(run_build(root, home).returncode, 0)
        wrong = home / ".cursor" / "skills" / "alpha"
        wrong.unlink()
        wrong.symlink_to(root / "skills.ja" / "beta")
        before = home_entries(home)

        result = run_build(root, home, "--check")

        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertEqual(
            result.stderr,
            "links do not match skills.ja. --check changes nothing.\n"
            "differs: .cursor/skills/alpha\n"
            "run without --check to install the links; "
            "conflicting entries must be removed by hand.\n",
        )
        self.assertEqual(home_entries(home), before)

    def test_check_names_a_stale_link(self):
        root, home = make_dirs()
        self.addCleanup(shutil.rmtree, root, True)
        self.addCleanup(shutil.rmtree, home, True)
        write_skill(root, "alpha")
        write_skill(root, "beta")
        self.assertEqual(run_build(root, home).returncode, 0)
        shutil.rmtree(root / "skills.ja" / "beta")
        before = home_entries(home)

        result = run_build(root, home, "--check")

        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertEqual(
            result.stderr,
            "links do not match skills.ja. --check changes nothing.\n"
            "stale: .claude/skills/beta\n"
            "stale: .cursor/skills/beta\n"
            "run without --check to install the links; "
            "conflicting entries must be removed by hand.\n",
        )
        self.assertEqual(home_entries(home), before)

    def test_check_names_a_conflicting_directory(self):
        root, home = make_dirs()
        self.addCleanup(shutil.rmtree, root, True)
        self.addCleanup(shutil.rmtree, home, True)
        write_skill(root, "alpha")
        self.assertEqual(run_build(root, home).returncode, 0)
        link = home / ".claude" / "skills" / "alpha"
        link.unlink()
        link.mkdir()
        (link / "owned.txt").write_text("keep\n", encoding="utf-8")
        before = home_entries(home)

        result = run_build(root, home, "--check")

        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertEqual(
            result.stderr,
            "links do not match skills.ja. --check changes nothing.\n"
            "conflict: .claude/skills/alpha\n"
            "run without --check to install the links; "
            "conflicting entries must be removed by hand.\n",
        )
        self.assertEqual(home_entries(home), before)

    def test_check_names_a_missing_destination_directory_once(self):
        root, home = make_dirs()
        self.addCleanup(shutil.rmtree, root, True)
        self.addCleanup(shutil.rmtree, home, True)
        write_skill(root, "alpha")
        write_skill(root, "beta")
        before = home_entries(home)

        result = run_build(root, home, "--check")

        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertEqual(
            result.stderr,
            "links do not match skills.ja. --check changes nothing.\n"
            "missing: .claude/skills\n"
            "missing: .cursor/skills\n"
            "run without --check to install the links; "
            "conflicting entries must be removed by hand.\n",
        )
        self.assertNotIn("alpha", result.stderr)
        self.assertNotIn("beta", result.stderr)
        self.assertEqual(home_entries(home), before)

    def test_check_names_a_foreign_symlink_as_a_conflict(self):
        root, home = make_dirs()
        outside = Path(tempfile.mkdtemp(prefix="install-skills-outside-"))
        self.addCleanup(shutil.rmtree, root, True)
        self.addCleanup(shutil.rmtree, home, True)
        self.addCleanup(shutil.rmtree, outside, True)
        write_skill(root, "alpha")
        (home / ".claude" / "skills").mkdir(parents=True)
        (home / ".cursor" / "skills").mkdir(parents=True)
        (home / ".claude" / "skills" / "alpha").symlink_to(outside)
        (home / ".cursor" / "skills" / "alpha").symlink_to(root / "skills.ja" / "alpha")
        before = home_entries(home)

        result = run_build(root, home, "--check")

        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertEqual(
            result.stderr,
            "links do not match skills.ja. --check changes nothing.\n"
            "conflict: .claude/skills/alpha\n"
            "run without --check to install the links; "
            "conflicting entries must be removed by hand.\n",
        )
        self.assertEqual(home_entries(home), before)


class InvalidInputTest(unittest.TestCase):
    def test_missing_skills_dir(self):
        root, home = make_dirs()
        self.addCleanup(shutil.rmtree, root, True)
        self.addCleanup(shutil.rmtree, home, True)
        before = home_entries(home)

        result = run_build(root, home)

        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertEqual(result.stderr, "skills.ja: missing skills.ja. create skills.ja\n")
        self.assertNotIn("Traceback", result.stderr)
        self.assertEqual(home_entries(home), before)

    def test_missing_skill_md(self):
        root, home = make_dirs()
        self.addCleanup(shutil.rmtree, root, True)
        self.addCleanup(shutil.rmtree, home, True)
        (root / "skills.ja" / "alpha").mkdir(parents=True)
        before = home_entries(home)

        result = run_build(root, home)

        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertEqual(result.stderr, "alpha: missing SKILL.md. create SKILL.md\n")
        self.assertEqual(home_entries(home), before)

    def test_missing_description(self):
        root, home = make_dirs()
        self.addCleanup(shutil.rmtree, root, True)
        self.addCleanup(shutil.rmtree, home, True)
        skill = root / "skills.ja" / "alpha"
        skill.mkdir(parents=True)
        (skill / "SKILL.md").write_text("---\nname: alpha\n---\n\nbody\n", encoding="utf-8")
        before = home_entries(home)

        result = run_build(root, home)

        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertEqual(
            result.stderr,
            "alpha: missing description. add a non-empty description\n",
        )
        self.assertEqual(home_entries(home), before)

    def test_empty_description(self):
        root, home = make_dirs()
        self.addCleanup(shutil.rmtree, root, True)
        self.addCleanup(shutil.rmtree, home, True)
        skill = root / "skills.ja" / "alpha"
        skill.mkdir(parents=True)
        (skill / "SKILL.md").write_text(
            "---\nname: alpha\ndescription:\n---\n\nbody\n",
            encoding="utf-8",
        )
        before = home_entries(home)

        result = run_build(root, home)

        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertEqual(
            result.stderr,
            "alpha: description is empty. set description to a non-empty string\n",
        )
        self.assertEqual(home_entries(home), before)

    def test_name_does_not_match_directory(self):
        root, home = make_dirs()
        self.addCleanup(shutil.rmtree, root, True)
        self.addCleanup(shutil.rmtree, home, True)
        skill = root / "skills.ja" / "alpha"
        skill.mkdir(parents=True)
        (skill / "SKILL.md").write_text(
            "---\nname: other\ndescription: A skill.\n---\n\nbody\n",
            encoding="utf-8",
        )
        before = home_entries(home)

        result = run_build(root, home)

        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertEqual(
            result.stderr,
            'alpha: name "other" does not match the directory. set name to alpha\n',
        )
        self.assertEqual(home_entries(home), before)

    def test_synced_name_is_reserved(self):
        root, home = make_dirs()
        self.addCleanup(shutil.rmtree, root, True)
        self.addCleanup(shutil.rmtree, home, True)
        write_skill(root, "synced")
        before = home_entries(home)

        result = run_build(root, home)

        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertEqual(
            result.stderr,
            'synced: name "synced" is reserved. rename the skill\n',
        )
        self.assertEqual(home_entries(home), before)

    def test_synced_name_is_reserved_regardless_of_case(self):
        root, home = make_dirs()
        self.addCleanup(shutil.rmtree, root, True)
        self.addCleanup(shutil.rmtree, home, True)
        skill = root / "skills.ja" / "Synced"
        skill.mkdir(parents=True)
        (skill / "SKILL.md").write_text(
            "---\nname: Synced\ndescription: A skill.\n---\n\nbody\n",
            encoding="utf-8",
        )
        before = home_entries(home)

        result = run_build(root, home)

        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertEqual(
            result.stderr,
            'Synced: name "Synced" is reserved. rename the skill\n',
        )
        self.assertEqual(home_entries(home), before)

    def test_missing_name(self):
        root, home = make_dirs()
        self.addCleanup(shutil.rmtree, root, True)
        self.addCleanup(shutil.rmtree, home, True)
        skill = root / "skills.ja" / "alpha"
        skill.mkdir(parents=True)
        (skill / "SKILL.md").write_text(
            "---\ndescription: A skill.\n---\n\nbody\n",
            encoding="utf-8",
        )
        before = home_entries(home)

        result = run_build(root, home)

        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertEqual(result.stderr, "alpha: missing name. add a non-empty name\n")
        self.assertEqual(home_entries(home), before)

    def test_empty_name(self):
        root, home = make_dirs()
        self.addCleanup(shutil.rmtree, root, True)
        self.addCleanup(shutil.rmtree, home, True)
        skill = root / "skills.ja" / "alpha"
        skill.mkdir(parents=True)
        (skill / "SKILL.md").write_text(
            "---\nname:\ndescription: A skill.\n---\n\nbody\n",
            encoding="utf-8",
        )
        before = home_entries(home)

        result = run_build(root, home)

        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertEqual(result.stderr, "alpha: name is empty. set name to alpha\n")
        self.assertEqual(home_entries(home), before)

    def test_frontmatter_line_without_a_colon(self):
        root, home = make_dirs()
        self.addCleanup(shutil.rmtree, root, True)
        self.addCleanup(shutil.rmtree, home, True)
        skill = root / "skills.ja" / "alpha"
        skill.mkdir(parents=True)
        (skill / "SKILL.md").write_text(
            "---\nname: alpha\nbroken line\ndescription: A skill.\n---\n\nbody\n",
            encoding="utf-8",
        )
        before = home_entries(home)

        result = run_build(root, home)

        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertEqual(
            result.stderr,
            "alpha: SKILL.md line 3 has no colon. write it as key: value\n",
        )
        self.assertEqual(home_entries(home), before)

    def test_frontmatter_without_a_closing_marker(self):
        root, home = make_dirs()
        self.addCleanup(shutil.rmtree, root, True)
        self.addCleanup(shutil.rmtree, home, True)
        skill = root / "skills.ja" / "alpha"
        skill.mkdir(parents=True)
        (skill / "SKILL.md").write_text(
            "---\nname: alpha\ndescription: A skill.\n",
            encoding="utf-8",
        )
        before = home_entries(home)

        result = run_build(root, home)

        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertEqual(
            result.stderr,
            "alpha: SKILL.md frontmatter has no closing ---. "
            "add --- after the frontmatter\n",
        )
        self.assertEqual(home_entries(home), before)

    def test_frontmatter_with_a_duplicate_key(self):
        root, home = make_dirs()
        self.addCleanup(shutil.rmtree, root, True)
        self.addCleanup(shutil.rmtree, home, True)
        skill = root / "skills.ja" / "alpha"
        skill.mkdir(parents=True)
        (skill / "SKILL.md").write_text(
            "---\nname: alpha\ndescription: A skill.\ndescription: Another.\n---\n\nbody\n",
            encoding="utf-8",
        )
        before = home_entries(home)

        result = run_build(root, home)

        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertEqual(
            result.stderr,
            'alpha: duplicate key "description" in SKILL.md. keep one description line\n',
        )
        self.assertEqual(home_entries(home), before)

    def test_valid_sibling_changes_nothing(self):
        root, home = make_dirs()
        self.addCleanup(shutil.rmtree, root, True)
        self.addCleanup(shutil.rmtree, home, True)
        write_skill(root, "alpha")
        (root / "skills.ja" / "beta").mkdir(parents=True)
        stale_dir = home / ".claude" / "skills"
        stale_dir.mkdir(parents=True)
        (stale_dir / "gamma").symlink_to(root / "skills.ja" / "gamma")
        before = home_entries(home)

        result = run_build(root, home)

        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertEqual(result.stderr, "beta: missing SKILL.md. create SKILL.md\n")
        self.assertEqual(home_entries(home), before)


class ExtraFrontmatterTest(unittest.TestCase):
    def test_other_frontmatter_keys_are_installed(self):
        root, home = make_dirs()
        self.addCleanup(shutil.rmtree, root, True)
        self.addCleanup(shutil.rmtree, home, True)
        skill = root / "skills.ja" / "alpha"
        skill.mkdir(parents=True)
        (skill / "SKILL.md").write_text(
            "---\nname: alpha\ndescription: A skill.\n"
            "disable-model-invocation: true\n---\n\nbody\n",
            encoding="utf-8",
        )

        result = run_build(root, home)

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertEqual(result.stdout, install_report(home, ["alpha"]))
        self.assertEqual(
            (home / ".claude" / "skills" / "alpha").readlink(),
            root / "skills.ja" / "alpha",
        )


class UnownedEntriesTest(unittest.TestCase):
    def setUp(self):
        self.root, self.home = make_dirs()
        self.outside = Path(tempfile.mkdtemp(prefix="install-skills-outside-"))
        self.addCleanup(shutil.rmtree, self.root, True)
        self.addCleanup(shutil.rmtree, self.home, True)
        self.addCleanup(shutil.rmtree, self.outside, True)
        write_skill(self.root, "alpha")
        claude = self.home / ".claude" / "skills"
        cursor = self.home / ".cursor" / "skills"
        claude.mkdir(parents=True)
        cursor.mkdir(parents=True)
        synced = claude / "synced"
        synced.mkdir()
        (synced / "kept.md").write_text("synced\n", encoding="utf-8")
        (claude / "other").symlink_to(self.outside)
        (cursor / "notes.txt").write_text("file\n", encoding="utf-8")

    def unowned(self) -> dict:
        keep = {
            ".claude/skills/synced",
            ".claude/skills/synced/kept.md",
            ".claude/skills/other",
            ".cursor/skills/notes.txt",
        }
        return {key: value for key, value in home_entries(self.home).items() if key in keep}

    def test_successful_run_leaves_unowned_entries_unchanged(self):
        before = self.unowned()
        result = run_build(self.root, self.home)
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertEqual(self.unowned(), before)
        self.assertEqual(
            (self.home / ".claude" / "skills" / "alpha").readlink(),
            self.root / "skills.ja" / "alpha",
        )

    def test_failed_run_leaves_unowned_entries_unchanged(self):
        (self.root / "skills.ja" / "beta").mkdir()
        before = home_entries(self.home)
        result = run_build(self.root, self.home)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(home_entries(self.home), before)


class RealSkillsTest(unittest.TestCase):
    def test_real_skills_link_into_a_temporary_home(self):
        home = Path(tempfile.mkdtemp(prefix="install-skills-home-"))
        self.addCleanup(shutil.rmtree, home, True)
        names = sorted(
            p.name for p in (REPO_ROOT / "skills.ja").iterdir() if p.is_dir()
        )

        result = run_build(REPO_ROOT, home)

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertEqual(result.stdout, install_report(home, names))
        self.assertEqual(result.stderr, "")
        self.assertGreater(len(names), 0)
        for name in names:
            target = REPO_ROOT / "skills.ja" / name
            for dest in DESTINATIONS:
                link = home / dest / name
                self.assertTrue(link.is_symlink(), msg=f"{dest}/{name}")
                self.assertEqual(link.readlink(), target)
                self.assertTrue((link / "SKILL.md").is_file(), msg=name)

    def test_omitted_root_installs_from_the_repository_containing_the_script(self):
        home = Path(tempfile.mkdtemp(prefix="install-skills-home-"))
        elsewhere = Path(tempfile.mkdtemp(prefix="install-skills-cwd-"))
        self.addCleanup(shutil.rmtree, home, True)
        self.addCleanup(shutil.rmtree, elsewhere, True)
        names = sorted(
            p.name for p in (REPO_ROOT / "skills.ja").iterdir() if p.is_dir()
        )

        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--home", str(home)],
            cwd=elsewhere,
            capture_output=True, text=True,
        )

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertEqual(result.stdout, install_report(home, names))
        self.assertEqual(result.stderr, "")
        for name in names:
            target = (REPO_ROOT / "skills.ja" / name).resolve()
            for dest in DESTINATIONS:
                link = home / dest / name
                self.assertEqual(link.readlink(), target)


class NormalRunTest(unittest.TestCase):
    def test_removes_stale_links(self):
        root, home = make_dirs()
        self.addCleanup(shutil.rmtree, root, True)
        self.addCleanup(shutil.rmtree, home, True)
        write_skill(root, "alpha")
        write_skill(root, "beta")
        self.assertEqual(run_build(root, home).returncode, 0)
        shutil.rmtree(root / "skills.ja" / "beta")

        result = run_build(root, home)

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertEqual(
            result.stdout,
            install_report(home, ["alpha"])
            + "removed: .claude/skills/beta\n"
            + "removed: .cursor/skills/beta\n",
        )
        self.assertEqual(result.stderr, "")
        self.assertFalse(os.path.lexists(home / ".claude" / "skills" / "beta"))
        self.assertFalse(os.path.lexists(home / ".cursor" / "skills" / "beta"))
        alpha = root / "skills.ja" / "alpha"
        self.assertEqual((home / ".claude" / "skills" / "alpha").readlink(), alpha)
        self.assertEqual((home / ".cursor" / "skills" / "alpha").readlink(), alpha)

    def test_repairs_links_broken_by_moving_the_repository(self):
        root, home = make_dirs()
        self.addCleanup(shutil.rmtree, home, True)
        write_skill(root, "alpha")
        self.assertEqual(run_build(root, home).returncode, 0)
        moved = root.parent / f"{root.name}-moved"
        shutil.move(root, moved)
        self.addCleanup(shutil.rmtree, moved, True)
        old = root / "skills.ja" / "alpha"
        self.assertEqual((home / ".claude" / "skills" / "alpha").readlink(), old)

        result = run_build(moved, home)

        target = moved / "skills.ja" / "alpha"
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertEqual(result.stdout, install_report(home, ["alpha"]))
        self.assertEqual(result.stderr, "")
        self.assertEqual((home / ".claude" / "skills" / "alpha").readlink(), target)
        self.assertEqual((home / ".cursor" / "skills" / "alpha").readlink(), target)
        self.assertEqual((home / ".claude" / "skills" / "alpha" / "notes.md").read_text(encoding="utf-8"), "aux\n")

    def test_removes_stale_links_that_still_point_at_the_old_repository(self):
        root, home = make_dirs()
        self.addCleanup(shutil.rmtree, home, True)
        write_skill(root, "alpha")
        write_skill(root, "beta")
        self.assertEqual(run_build(root, home).returncode, 0)
        moved = root.parent / f"{root.name}-moved"
        shutil.move(root, moved)
        self.addCleanup(shutil.rmtree, moved, True)
        shutil.rmtree(moved / "skills.ja" / "beta")

        result = run_build(moved, home)

        target = moved / "skills.ja" / "alpha"
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertEqual(
            result.stdout,
            install_report(home, ["alpha"])
            + "removed: .claude/skills/beta\n"
            + "removed: .cursor/skills/beta\n",
        )
        self.assertEqual((home / ".claude" / "skills" / "alpha").readlink(), target)
        self.assertFalse(os.path.lexists(home / ".claude" / "skills" / "beta"))
        self.assertFalse(os.path.lexists(home / ".cursor" / "skills" / "beta"))

    def test_conflict_blocks_the_run_and_changes_nothing(self):
        root, home = make_dirs()
        self.addCleanup(shutil.rmtree, root, True)
        self.addCleanup(shutil.rmtree, home, True)
        write_skill(root, "alpha")
        write_skill(root, "beta")
        write_skill(root, "gamma")
        self.assertEqual(run_build(root, home).returncode, 0)
        shutil.rmtree(root / "skills.ja" / "gamma")
        wrong = home / ".cursor" / "skills" / "alpha"
        wrong.unlink()
        wrong.symlink_to(root / "skills.ja" / "beta")
        blocked = home / ".claude" / "skills" / "alpha"
        blocked.unlink()
        blocked.mkdir()
        (blocked / "owned.txt").write_text("keep\n", encoding="utf-8")
        before = home_entries(home)

        result = run_build(root, home)

        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertEqual(
            result.stderr,
            "alpha: conflict at .claude/skills/alpha. "
            "remove the conflicting entry by hand\n",
        )
        self.assertNotIn("Traceback", result.stderr)
        self.assertEqual(home_entries(home), before)

    def test_foreign_symlink_is_a_conflict_and_changes_nothing(self):
        root, home = make_dirs()
        outside = Path(tempfile.mkdtemp(prefix="install-skills-outside-"))
        self.addCleanup(shutil.rmtree, root, True)
        self.addCleanup(shutil.rmtree, home, True)
        self.addCleanup(shutil.rmtree, outside, True)
        write_skill(root, "alpha")
        write_skill(root, "beta")
        (home / ".claude" / "skills").mkdir(parents=True)
        (home / ".claude" / "skills" / "alpha").symlink_to(outside)
        before = home_entries(home)

        result = run_build(root, home)

        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertEqual(
            result.stderr,
            "alpha: conflict at .claude/skills/alpha. "
            "remove the conflicting entry by hand\n",
        )
        self.assertEqual(home_entries(home), before)


class ToolSelectionTest(unittest.TestCase):
    def test_cursor_installs_only_the_cursor_destination(self):
        root, home = make_dirs()
        self.addCleanup(shutil.rmtree, root, True)
        self.addCleanup(shutil.rmtree, home, True)
        write_skill(root, "alpha")
        write_skill(root, "beta")

        result = run_build(root, home, "--tool", "cursor")

        cursor = (".cursor/skills",)
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertEqual(result.stdout, install_report(home, ["alpha", "beta"], cursor))
        self.assertEqual(result.stderr, "")
        self.assertFalse((home / ".claude").exists())
        for name in ("alpha", "beta"):
            link = home / ".cursor" / "skills" / name
            self.assertEqual(link.readlink(), root / "skills.ja" / name)

    def test_claude_installs_only_the_claude_destination(self):
        root, home = make_dirs()
        self.addCleanup(shutil.rmtree, root, True)
        self.addCleanup(shutil.rmtree, home, True)
        write_skill(root, "alpha")

        result = run_build(root, home, "--tool", "claude")

        claude = (".claude/skills",)
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertEqual(result.stdout, install_report(home, ["alpha"], claude))
        self.assertEqual(result.stderr, "")
        self.assertFalse((home / ".cursor").exists())
        self.assertEqual(
            (home / ".claude" / "skills" / "alpha").readlink(),
            root / "skills.ja" / "alpha",
        )

    def test_conflict_on_the_unselected_side_does_not_block(self):
        root, home = make_dirs()
        self.addCleanup(shutil.rmtree, root, True)
        self.addCleanup(shutil.rmtree, home, True)
        write_skill(root, "alpha")
        blocked = home / ".claude" / "skills" / "alpha"
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

        result = run_build(root, home, "--tool", "cursor")

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertEqual(
            (home / ".cursor" / "skills" / "alpha").readlink(),
            root / "skills.ja" / "alpha",
        )
        self.assertEqual(claude_entries(), before)

    def test_check_names_only_the_selected_destination(self):
        root, home = make_dirs()
        self.addCleanup(shutil.rmtree, root, True)
        self.addCleanup(shutil.rmtree, home, True)
        write_skill(root, "alpha")
        before = home_entries(home)

        result = run_build(root, home, "--check", "--tool", "cursor")

        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertEqual(
            result.stderr,
            "links do not match skills.ja. --check changes nothing.\n"
            "missing: .cursor/skills\n"
            "run without --check to install the links; "
            "conflicting entries must be removed by hand.\n",
        )
        self.assertNotIn(".claude", result.stderr)
        self.assertEqual(home_entries(home), before)

    def test_unknown_tool_changes_nothing(self):
        root, home = make_dirs()
        self.addCleanup(shutil.rmtree, root, True)
        self.addCleanup(shutil.rmtree, home, True)
        (home / "marker.txt").write_text("keep\n", encoding="utf-8")
        before = home_entries(home)

        result = run_build(root, home, "--tool", "both")

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
        write_skill(root, "alpha")
        (home / "marker.txt").write_text("keep\n", encoding="utf-8")
        before = home_entries(home)

        result = run_build(root, home, "--tool", "cursor", "--tool", "claude")

        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertEqual(
            result.stderr,
            "tool: --tool was given more than once. pass it once\n",
        )
        self.assertEqual(home_entries(home), before)

    def test_synced_is_an_ordinary_skill_for_cursor_only(self):
        root, home = make_dirs()
        self.addCleanup(shutil.rmtree, root, True)
        self.addCleanup(shutil.rmtree, home, True)
        write_skill(root, "synced")

        result = run_build(root, home, "--tool", "cursor")

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertEqual(result.stdout, install_report(home, ["synced"], (".cursor/skills",)))
        self.assertEqual(
            (home / ".cursor" / "skills" / "synced").readlink(),
            root / "skills.ja" / "synced",
        )
        self.assertFalse((home / ".claude").exists())

    def test_claude_still_rejects_synced(self):
        root, home = make_dirs()
        self.addCleanup(shutil.rmtree, root, True)
        self.addCleanup(shutil.rmtree, home, True)
        write_skill(root, "synced")
        before = home_entries(home)

        result = run_build(root, home, "--tool", "claude")

        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(
            result.stderr,
            'synced: name "synced" is reserved. rename the skill\n',
        )
        self.assertEqual(home_entries(home), before)

    def test_removes_stale_links_only_on_the_selected_side(self):
        root, home = make_dirs()
        self.addCleanup(shutil.rmtree, root, True)
        self.addCleanup(shutil.rmtree, home, True)
        write_skill(root, "alpha")
        write_skill(root, "beta")
        self.assertEqual(run_build(root, home).returncode, 0)
        shutil.rmtree(root / "skills.ja" / "beta")
        claude_beta = home / ".claude" / "skills" / "beta"

        result = run_build(root, home, "--tool", "cursor")

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("removed: .cursor/skills/beta\n", result.stdout)
        self.assertNotIn("removed: .claude/skills/beta", result.stdout)
        self.assertFalse(os.path.lexists(home / ".cursor" / "skills" / "beta"))
        self.assertTrue(claude_beta.is_symlink())
        self.assertEqual(claude_beta.readlink(), root / "skills.ja" / "beta")

    def test_repairs_only_the_selected_side(self):
        root, home = make_dirs()
        self.addCleanup(shutil.rmtree, home, True)
        write_skill(root, "alpha")
        self.assertEqual(run_build(root, home).returncode, 0)
        moved = root.parent / f"{root.name}-moved"
        shutil.move(root, moved)
        self.addCleanup(shutil.rmtree, moved, True)
        old = root / "skills.ja" / "alpha"

        result = run_build(moved, home, "--tool", "cursor")

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertEqual(
            (home / ".cursor" / "skills" / "alpha").readlink(),
            moved / "skills.ja" / "alpha",
        )
        self.assertEqual((home / ".claude" / "skills" / "alpha").readlink(), old)

    def test_check_passes_for_the_selected_destination(self):
        root, home = make_dirs()
        self.addCleanup(shutil.rmtree, root, True)
        self.addCleanup(shutil.rmtree, home, True)
        write_skill(root, "alpha")
        self.assertEqual(run_build(root, home, "--tool", "cursor").returncode, 0)
        before = home_entries(home)

        result = run_build(root, home, "--check", "--tool", "cursor")

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertEqual(
            result.stdout,
            check_report(home, ["alpha"], (".cursor/skills",)),
        )
        self.assertEqual(result.stderr, "")
        self.assertEqual(home_entries(home), before)


if __name__ == "__main__":
    unittest.main()
