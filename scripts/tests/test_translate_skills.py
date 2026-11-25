# Test specification for translate-skills.
#
# The public seam is the translate-skills command run against a temporary git
# repository: exit code, stdout, stderr, and the files under skills.en/. The
# translator is the only thing replaced. The real claude is never called here.

import json
import os
import shutil
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

from support import install_scripts

TESTS_DIR = Path(__file__).resolve().parent

FAKE_TRANSLATOR = textwrap.dedent(
    '''
    import json, os, sys, time
    here = os.path.dirname(os.path.abspath(__file__))
    request = json.loads(sys.stdin.buffer.read().decode("utf-8"))
    with open(os.path.join(here, "calls.jsonl"), "a", encoding="utf-8") as log:
        log.write(json.dumps({"t": time.time(), "argv": sys.argv[1:],
                              "request": request}) + "\\n")
    if request.get("description") == "失敗":
        sys.stderr.write("usage limit reached\\n")
        sys.exit(1)
    time.sleep(float(os.environ.get("FAKE_SLEEP", "0")))
    with open(os.path.join(here, "dictionary.json"), encoding="utf-8") as f:
        dictionary = json.load(f)
    out = {"description": dictionary.get(request["description"], request["description"]),
           "body": [dictionary.get(line, line) for line in request["body"]]}
    sys.stdout.buffer.write(json.dumps(out, ensure_ascii=False).encode("utf-8"))
    '''
)

SKILL = (
    "---\n"
    "name: sample\n"
    "description: サンプルの説明\n"
    "disable-model-invocation: true\n"
    "---\n"
    "# Sample\n"
    "- 一つ目の項目\n"
)
SKILL_EN = (
    "---\n"
    "name: sample\n"
    "description: A sample description\n"
    "disable-model-invocation: true\n"
    "---\n"
    "# Sample\n"
    "- The first item\n"
)
DICTIONARY = {
    "サンプルの説明": "A sample description",
    "- 一つ目の項目": "- The first item",
    "echo そのまま": "echo as-is",
}


def git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(root), *args], capture_output=True, text=True, check=True
    )
    return result.stdout


class Repo:
    def __init__(self, test: unittest.TestCase):
        self.root = Path(Path(tempfile.mkdtemp(prefix="translate-skills-test-")).resolve())
        self.fake_dir = Path(tempfile.mkdtemp(prefix="translate-skills-fake-"))
        test.addCleanup(shutil.rmtree, self.root, True)
        test.addCleanup(shutil.rmtree, self.fake_dir, True)
        git(self.root, "init", "-q")
        git(self.root, "config", "user.name", "test")
        git(self.root, "config", "user.email", "test@example.invalid")
        git(self.root, "config", "commit.gpgsign", "false")
        translator = self.fake_dir / "fake"
        translator.write_text(f"#!{sys.executable}\n" + FAKE_TRANSLATOR, encoding="utf-8")
        translator.chmod(0o755)
        self.translator = translator
        self.dictionary(DICTIONARY)

    def dictionary(self, mapping: dict[str, str]) -> None:
        (self.fake_dir / "dictionary.json").write_text(
            json.dumps(mapping, ensure_ascii=False), encoding="utf-8"
        )

    def calls(self) -> list[dict]:
        log = self.fake_dir / "calls.jsonl"
        if not log.exists():
            return []
        return [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines()]

    def write(self, rel: str, text: str) -> None:
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def commit(self) -> None:
        git(self.root, "add", "-A")
        git(self.root, "commit", "-q", "-m", "commit")

    def run(self, *extra: str, sleep: str = "0") -> subprocess.CompletedProcess:
        env = dict(os.environ, FAKE_SLEEP=sleep)
        return subprocess.run(
            [sys.executable, str(install_scripts(self.root) / "translate-skills"),
             "--translator", str(self.translator), *extra],
            capture_output=True, text=True, encoding="utf-8", env=env,
        )

    def read(self, rel: str) -> str:
        return (self.root / rel).read_text(encoding="utf-8")


class NewSkillTest(unittest.TestCase):
    def test_a_new_skill_translates_skill_md_and_keeps_the_name(self):
        repo = Repo(self)
        repo.write("skills.ja/sample/SKILL.md", SKILL)
        repo.commit()

        result = repo.run()

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertEqual(result.stderr, "")
        self.assertEqual(
            result.stdout,
            "translating 1 file, 1 at a time\n"
            "translating sample/SKILL.md\n"
            f"wrote 1 files from skills.ja under {repo.root}\n"
            "skills.en/sample/SKILL.md\n",
        )
        self.assertEqual(repo.read("skills.en/sample/SKILL.md"), SKILL_EN)
        [call] = repo.calls()
        self.assertEqual(call["request"]["description"], "サンプルの説明")
        self.assertEqual(call["request"]["body"], ["# Sample", "- 一つ目の項目"])


class FenceAndCopyTest(unittest.TestCase):
    def test_fence_interiors_are_translated_and_basis_is_omitted(self):
        repo = Repo(self)
        repo.write("skills.ja/sample/SKILL.md", SKILL)
        repo.write(
            "skills.ja/sample/notes.md",
            "# Notes\n\n```bash\necho そのまま\n```\n",
        )
        repo.write("skills.ja/sample/basis.md", "# 根拠\n\n上流の記録\n")
        repo.write("skills.ja/sample/scripts/run.sh", "echo hello\n")
        repo.commit()

        result = repo.run()

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertFalse((repo.root / "skills.en" / "sample" / "basis.md").exists())
        self.assertEqual(repo.read("skills.en/sample/scripts/run.sh"), "echo hello\n")
        notes = repo.read("skills.en/sample/notes.md")
        self.assertIn("echo as-is\n", notes)
        self.assertNotIn("そのまま", notes)
        requests = [call["request"] for call in repo.calls()]
        bodies = [line for request in requests for line in request["body"]]
        self.assertIn("echo そのまま", bodies)
        self.assertIn("```bash", bodies)


class HistoryTest(unittest.TestCase):
    def test_an_unchanged_skill_makes_no_call_and_writes_nothing(self):
        repo = Repo(self)
        repo.write("skills.ja/sample/SKILL.md", SKILL)
        repo.write("skills.en/sample/SKILL.md", SKILL_EN)
        repo.commit()

        result = repo.run()

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertEqual(repo.calls(), [])
        self.assertEqual(
            result.stdout,
            "unchanged sample/SKILL.md\n"
            f"nothing to translate from skills.ja under {repo.root}; wrote nothing\n",
        )

    def test_the_count_line_comes_first_when_a_file_is_translated(self):
        repo = Repo(self)
        repo.write("skills.ja/alpha/SKILL.md", SKILL.replace("name: sample", "name: alpha"))
        repo.write("skills.en/alpha/SKILL.md", SKILL_EN.replace("name: sample", "name: alpha"))
        repo.write("skills.ja/sample/SKILL.md", SKILL)
        repo.write("skills.ja/sample/scripts/run.sh", "echo hello\n")
        repo.commit()

        result = repo.run()

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertEqual(
            result.stdout,
            "translating 1 file, 1 at a time\n"
            "unchanged alpha/SKILL.md\n"
            "copying sample/scripts/run.sh\n"
            "translating sample/SKILL.md\n"
            f"wrote 2 files from skills.ja under {repo.root}\n"
            "skills.en/sample/SKILL.md\n"
            "skills.en/sample/scripts/run.sh\n",
        )

    def test_an_unchanged_line_keeps_its_english_and_the_old_line_is_hidden(self):
        repo = Repo(self)
        repo.write("skills.ja/sample/SKILL.md", SKILL)
        repo.write("skills.en/sample/SKILL.md", SKILL_EN)
        repo.commit()
        changed = SKILL.replace("- 一つ目の項目\n", "- 新しい項目\n")
        repo.write("skills.ja/sample/SKILL.md", changed)
        repo.dictionary(dict(DICTIONARY, **{"- 新しい項目": "- A new item"}))

        result = repo.run()

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        text = repo.read("skills.en/sample/SKILL.md")
        self.assertIn("- A new item\n", text)
        self.assertIn("A sample description", text)
        self.assertIn("# Sample\n", text)
        self.assertNotIn("- The first item\n", text)
        prompt = repo.calls()[0]["argv"][-1]
        self.assertIn("A sample description", prompt)
        self.assertNotIn("- The first item", prompt)


class ParallelTest(unittest.TestCase):
    def test_two_calls_overlap_and_a_failure_writes_nothing(self):
        repo = Repo(self)
        repo.write("skills.ja/alpha/SKILL.md", SKILL.replace("name: sample", "name: alpha"))
        failing = SKILL.replace("name: sample", "name: beta").replace(
            "サンプルの説明", "失敗"
        )
        repo.write("skills.ja/beta/SKILL.md", failing)
        repo.commit()

        result = repo.run("--jobs", "2", sleep="0.4")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("beta/SKILL.md:", result.stderr)
        self.assertIn("make claude -p succeed, then rerun", result.stderr)
        self.assertFalse((repo.root / "skills.en").exists())
        starts = sorted(call["t"] for call in repo.calls())
        self.assertEqual(len(starts), 2)
        self.assertLess(starts[1] - starts[0], 0.3)


class InvalidInputTest(unittest.TestCase):
    def test_jobs_below_one_changes_nothing(self):
        repo = Repo(self)
        result = repo.run("--jobs", "0")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stderr, "jobs: --jobs must be at least 1. pass --jobs 4\n")
        self.assertEqual(repo.calls(), [])

    def test_a_missing_skill_md_makes_no_call(self):
        repo = Repo(self)
        (repo.root / "skills.ja" / "sample").mkdir(parents=True)
        result = repo.run()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stderr, "sample: missing SKILL.md. create SKILL.md\n")
        self.assertEqual(repo.calls(), [])

    def test_one_invalid_skill_among_valid_ones_makes_no_call(self):
        repo = Repo(self)
        repo.write("skills.ja/sample/SKILL.md", SKILL)
        repo.write("skills.ja/broken/SKILL.md", SKILL.replace("name: sample", "name: other"))
        repo.commit()

        result = repo.run()

        self.assertEqual(result.returncode, 1)
        self.assertEqual(
            result.stderr,
            'broken: name "other" does not match the directory. set name to broken\n',
        )
        self.assertEqual(repo.calls(), [])
        self.assertFalse((repo.root / "skills.en").exists())

    def assert_uncommitted_target(self, after, remain, before=()):
        repo = Repo(self)
        repo.write("skills.ja/sample/SKILL.md", SKILL)
        repo.write("skills.en/sample/SKILL.md", SKILL_EN)
        for rel, text in before:
            repo.write(rel, text)
        repo.commit()
        for rel, text in after:
            repo.write(rel, text)

        result = repo.run()

        self.assertEqual(result.returncode, 1)
        self.assertEqual(
            result.stderr,
            "sample: skills.en/sample has uncommitted changes. "
            "commit or discard skills.en/sample, then rerun\n",
        )
        self.assertEqual(repo.calls(), [])
        for rel, text in remain:
            self.assertEqual(repo.read(rel), text)

    def test_uncommitted_changes_in_the_target_skill_are_an_error(self):
        edited = SKILL_EN + "- Edited by hand\n"
        self.assert_uncommitted_target(
            after=[
                ("skills.ja/sample/SKILL.md", SKILL.replace("一つ目", "新しい")),
                ("skills.en/sample/SKILL.md", edited),
            ],
            remain=[("skills.en/sample/SKILL.md", edited)],
        )

    def test_uncommitted_changes_only_in_the_target_are_an_error(self):
        edited = SKILL_EN + "- Edited by hand\n"
        self.assert_uncommitted_target(
            after=[("skills.en/sample/SKILL.md", edited)],
            remain=[("skills.en/sample/SKILL.md", edited)],
        )

    def test_an_uncommitted_target_file_other_than_skill_md_is_an_error(self):
        self.assert_uncommitted_target(
            before=[("skills.en/sample/notes.md", "clean\n")],
            after=[("skills.en/sample/notes.md", "dirty\n")],
            remain=[
                ("skills.en/sample/notes.md", "dirty\n"),
                ("skills.en/sample/SKILL.md", SKILL_EN),
            ],
        )


class NonMarkdownCopyTest(unittest.TestCase):
    def test_a_non_markdown_file_is_copied_byte_for_byte_without_a_call(self):
        repo = Repo(self)
        repo.write("skills.ja/sample/SKILL.md", SKILL)
        payload = b"\x00\xff\r\n\x89PNG\xe3\x81\x82"
        (repo.root / "skills.ja/sample/assets").mkdir(parents=True)
        (repo.root / "skills.ja/sample/assets/blob.bin").write_bytes(payload)
        repo.commit()

        result = repo.run()

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertEqual((repo.root / "skills.en/sample/assets/blob.bin").read_bytes(), payload)
        self.assertEqual(len(repo.calls()), 1)


class LanguagePairTest(unittest.TestCase):
    """--from and --to pick the editions skills.<from> and skills.<to>."""

    def english_repo(self) -> "Repo":
        repo = Repo(self)
        repo.write("skills.en/sample/SKILL.md", SKILL_EN)
        repo.commit()
        repo.dictionary({
            "A sample description": "Une description",
            "- The first item": "- Le premier élément",
        })
        return repo

    def test_an_explicit_pair_builds_the_target_edition(self):
        repo = self.english_repo()

        result = repo.run("--from", "en", "--to", "fr")

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertEqual(
            result.stdout,
            "translating 1 file, 1 at a time\n"
            "translating sample/SKILL.md\n"
            f"wrote 1 files from skills.en under {repo.root}\n"
            "skills.fr/sample/SKILL.md\n",
        )
        self.assertEqual(
            repo.read("skills.fr/sample/SKILL.md"),
            "---\nname: sample\ndescription: Une description\n"
            "disable-model-invocation: true\n---\n# Sample\n- Le premier élément\n",
        )
        prompt = repo.calls()[0]["argv"][-1]
        self.assertIn("Translate the English in the JSON object", prompt)
        self.assertIn("into French.", prompt)
        self.assertFalse((repo.root / "skills.ja").exists())

    def test_a_missing_source_edition_makes_no_call(self):
        repo = Repo(self)
        result = repo.run("--from", "de", "--to", "en")
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stderr, "skills.de: missing skills.de. create skills.de\n")
        self.assertEqual(repo.calls(), [])

    def test_a_repeated_from_or_to_changes_nothing(self):
        repo = self.english_repo()

        again_from = repo.run("--from", "en", "--from", "ja", "--to", "fr")
        again_to = repo.run("--from", "en", "--to", "fr", "--to", "de")

        self.assertEqual(again_from.returncode, 1)
        self.assertEqual(
            again_from.stderr, "from: --from was given more than once. pass it once\n")
        self.assertEqual(again_to.returncode, 1)
        self.assertEqual(
            again_to.stderr, "to: --to was given more than once. pass it once\n")
        self.assertEqual(repo.calls(), [])
        self.assertFalse((repo.root / "skills.fr").exists())

    def test_a_value_that_is_not_a_language_code_changes_nothing(self):
        repo = self.english_repo()
        result = repo.run("--from", "en", "--to", "../x")
        self.assertEqual(result.returncode, 1)
        self.assertEqual(
            result.stderr,
            'to: "../x" is not a language code. '
            "pass --to with letters, digits, - or _, such as en or ja\n",
        )
        self.assertEqual(repo.calls(), [])

    def test_the_same_language_on_both_sides_changes_nothing(self):
        repo = self.english_repo()
        result = repo.run("--from", "en", "--to", "en")
        self.assertEqual(result.returncode, 1)
        self.assertEqual(
            result.stderr,
            "to: --from and --to are both en. pass two different languages\n",
        )
        self.assertEqual(repo.calls(), [])


if __name__ == "__main__":
    unittest.main()
