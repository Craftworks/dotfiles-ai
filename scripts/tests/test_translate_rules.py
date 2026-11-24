# Test specification for translate-rules.
#
# The public seam is the translate-rules command run against a temporary git
# repository: exit code, stdout, stderr, and the files under rules.en/. The
# translator is the only thing replaced: --translator points at a fake that
# translates each input line through a dictionary the test provides and
# records how it was called. The real claude is never called here.

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
    with open(os.path.join(here, "calls.jsonl"), "a", encoding="utf-8") as log:
        log.write(json.dumps({"argv": sys.argv[1:], "cwd": os.getcwd(),
                              "cwd_entries": os.listdir(os.getcwd())}) + "\\n")
    request = json.loads(sys.stdin.buffer.read().decode("utf-8"))
    mode = os.environ.get("FAKE_MODE", "")
    if mode == "fail":
        sys.stderr.write("usage limit reached\\n")
        sys.exit(1)
    if mode == "sleep":
        time.sleep(30)
    if mode == "empty":
        sys.exit(0)
    if mode == "not-json":
        print("Here is the translation:")
        sys.exit(0)
    with open(os.path.join(here, "dictionary.json"), encoding="utf-8") as f:
        dictionary = json.load(f)
    out = {"description": dictionary.get(request["description"], request["description"]),
           "body": [dictionary.get(line, line) for line in request["body"]]}
    if mode == "extra-line":
        out["body"].append("extra")
    sys.stdout.buffer.write(json.dumps(out, ensure_ascii=False).encode("utf-8"))
    '''
)


def git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(root), *args], capture_output=True, text=True, check=True
    )
    return result.stdout


class Repo:
    """A temporary git repository with rules.ja and a fake translator."""

    def __init__(self, test: unittest.TestCase):
        self.root = Path(Path(tempfile.mkdtemp(prefix="translate-rules-test-")).resolve())
        self.fake_dir = Path(tempfile.mkdtemp(prefix="translate-rules-fake-"))
        test.addCleanup(shutil.rmtree, self.root, True)
        test.addCleanup(shutil.rmtree, self.fake_dir, True)
        git(self.root, "init", "-q")
        git(self.root, "config", "user.name", "test")
        git(self.root, "config", "user.email", "test@example.invalid")
        git(self.root, "config", "commit.gpgsign", "false")
        (self.fake_dir / "fake.py").write_text(FAKE_TRANSLATOR, encoding="utf-8")
        if os.name == "nt":
            self.translator = self.fake_dir / "fake.cmd"
            self.translator.write_text(
                f'@"{sys.executable}" "%~dp0fake.py" %*\r\n', encoding="utf-8"
            )
        else:
            self.translator = self.fake_dir / "fake"
            self.translator.write_text(
                f"#!{sys.executable}\n" + FAKE_TRANSLATOR, encoding="utf-8"
            )
            self.translator.chmod(0o755)
            (self.fake_dir / "fake.py").unlink()
        self.dictionary({})

    def dictionary(self, mapping: dict[str, str]) -> None:
        (self.fake_dir / "dictionary.json").write_text(
            json.dumps(mapping, ensure_ascii=False), encoding="utf-8"
        )

    def calls(self) -> list[dict]:
        log = self.fake_dir / "calls.jsonl"
        if not log.exists():
            return []
        return [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines()]

    def write_rule(self, name: str, description: str, body: str,
                   cursor: dict | None = None) -> None:
        rule = self.root / "rules.ja" / name
        rule.mkdir(parents=True, exist_ok=True)
        meta = {"description": description,
                "cursor": cursor if cursor is not None else {"globs": None, "alwaysApply": False}}
        (rule / "meta.json").write_text(
            json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        (rule / "body.md").write_text(body, encoding="utf-8")

    def write_en(self, name: str, description: str, body: str,
                 cursor: dict | None = None) -> None:
        rule = self.root / "rules.en" / name
        rule.mkdir(parents=True, exist_ok=True)
        meta = {"description": description,
                "cursor": cursor if cursor is not None else {"globs": None, "alwaysApply": False}}
        (rule / "meta.json").write_text(
            json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        (rule / "body.md").write_text(body, encoding="utf-8")

    def commit(self, message: str = "commit") -> None:
        git(self.root, "add", "-A")
        git(self.root, "commit", "-q", "-m", message)

    def run(self, *extra: str, mode: str = "") -> subprocess.CompletedProcess:
        env = dict(os.environ, FAKE_MODE=mode)
        return subprocess.run(
            [sys.executable, str(install_scripts(self.root) / "translate-rules"),
             "--translator", str(self.translator), *extra],
            capture_output=True, text=True, encoding="utf-8", env=env,
        )

    def read(self, rel: str) -> str:
        return (self.root / rel).read_text(encoding="utf-8")

    def snapshot(self) -> dict[str, bytes]:
        en = self.root / "rules.en"
        if not en.exists():
            return {}
        return {p.relative_to(en).as_posix(): p.read_bytes()
                for p in sorted(en.rglob("*")) if p.is_file()}


JA_BODY = "# Sample\n\n## やること\n\n- 一つ目の項目\n- 二つ目の項目\n"
EN_BODY = "# Sample\n\n## Do\n\n- The first item\n- The second item\n"
JA_DICTIONARY = {
    "サンプルの説明": "A sample description",
    "## やること": "## Do",
    "- 一つ目の項目": "- The first item",
    "- 二つ目の項目": "- The second item",
}


def translated_report(root: Path, names: list[str], progress: list[str]) -> str:
    lines = progress + [f"wrote {2 * len(names)} files from rules.ja under {root}"]
    for name in names:
        lines += [f"rules.en/{name}/body.md", f"rules.en/{name}/meta.json"]
    return "\n".join(lines) + "\n"


class NewRuleTest(unittest.TestCase):
    def test_a_rule_without_rules_en_is_translated_in_full(self):
        repo = Repo(self)
        repo.write_rule("sample", "サンプルの説明", JA_BODY,
                        cursor={"globs": "*.py", "alwaysApply": False})
        repo.commit()
        repo.dictionary(JA_DICTIONARY)

        result = repo.run()

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertEqual(result.stderr, "")
        self.assertEqual(
            result.stdout,
            translated_report(repo.root, ["sample"], ["translating sample"]),
        )
        self.assertEqual(repo.read("rules.en/sample/body.md"), EN_BODY)
        self.assertEqual(
            repo.read("rules.en/sample/meta.json"),
            '{\n  "description": "A sample description",\n'
            '  "cursor": {\n    "globs": "*.py",\n    "alwaysApply": false\n  }\n}\n',
        )


class UnchangedRuleTest(unittest.TestCase):
    def test_an_unchanged_rule_makes_no_call_and_writes_nothing(self):
        repo = Repo(self)
        repo.write_rule("sample", "サンプルの説明", JA_BODY)
        repo.write_en("sample", "A sample description", EN_BODY)
        repo.commit()
        before = repo.snapshot()

        result = repo.run()

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertEqual(result.stderr, "")
        self.assertEqual(
            result.stdout,
            "unchanged sample\n"
            f"nothing to translate from rules.ja under {repo.root}; wrote nothing\n",
        )
        self.assertEqual(repo.calls(), [])
        self.assertEqual(repo.snapshot(), before)


class SpliceTest(unittest.TestCase):
    def test_changed_and_added_lines_are_new_and_unchanged_lines_are_kept(self):
        repo = Repo(self)
        repo.write_rule("sample", "サンプルの説明", JA_BODY)
        repo.write_en("sample", "A sample description", EN_BODY)
        repo.commit()
        repo.write_rule(
            "sample", "サンプルの説明",
            "# Sample\n\n## やること\n\n- 一つ目の項目\n- 三つ目の項目\n- 四つ目の項目\n",
        )
        # The fake words unchanged lines differently from the previous
        # English, so keeping them can only come from the previous English.
        repo.dictionary({
            "サンプルの説明": "Retranslated description",
            "## やること": "## Things to do",
            "- 一つ目の項目": "- Item number one",
            "- 三つ目の項目": "- The third item",
            "- 四つ目の項目": "- The fourth item",
        })

        result = repo.run()

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertEqual(
            result.stdout,
            translated_report(repo.root, ["sample"], ["translating sample"]),
        )
        self.assertEqual(
            repo.read("rules.en/sample/body.md"),
            "# Sample\n\n## Do\n\n- The first item\n- The third item\n- The fourth item\n",
        )
        self.assertEqual(
            json.loads(repo.read("rules.en/sample/meta.json"))["description"],
            "A sample description",
        )
        # Observed with Haiku on 2026-11-23: shown the old English of a
        # changed line, it copied that line instead of translating the new
        # Japanese. Only the English of unchanged lines is shown, for terms.
        [call] = repo.calls()
        prompt = "\n".join(call["argv"])
        self.assertIn("The first item", prompt)
        self.assertNotIn("The second item", prompt)

    def test_a_changed_description_alone_keeps_the_body(self):
        repo = Repo(self)
        repo.write_rule("sample", "サンプルの説明", JA_BODY)
        repo.write_en("sample", "A sample description", EN_BODY)
        repo.commit()
        repo.write_rule("sample", "新しい説明", JA_BODY)
        repo.dictionary({
            "新しい説明": "A new description",
            "## やること": "## Things to do",
            "- 一つ目の項目": "- Item number one",
            "- 二つ目の項目": "- Item number two",
        })

        result = repo.run()

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertEqual(repo.read("rules.en/sample/body.md"), EN_BODY)
        self.assertEqual(
            json.loads(repo.read("rules.en/sample/meta.json"))["description"],
            "A new description",
        )


class CursorOnlyTest(unittest.TestCase):
    def test_a_cursor_change_alone_is_copied_without_a_call(self):
        repo = Repo(self)
        repo.write_rule("sample", "サンプルの説明", JA_BODY)
        repo.write_en("sample", "A sample description", EN_BODY)
        repo.commit()
        repo.write_rule("sample", "サンプルの説明", JA_BODY,
                        cursor={"globs": "*.md", "alwaysApply": False})

        result = repo.run()

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertEqual(result.stderr, "")
        self.assertEqual(
            result.stdout,
            "copying cursor of sample\n"
            f"wrote 1 files from rules.ja under {repo.root}\n"
            "rules.en/sample/meta.json\n",
        )
        self.assertEqual(repo.calls(), [])
        self.assertEqual(repo.read("rules.en/sample/body.md"), EN_BODY)
        self.assertEqual(
            repo.read("rules.en/sample/meta.json"),
            '{\n  "description": "A sample description",\n'
            '  "cursor": {\n    "globs": "*.md",\n    "alwaysApply": false\n  }\n}\n',
        )


class RuleNamesTest(unittest.TestCase):
    def test_names_narrow_the_run_to_those_rules(self):
        repo = Repo(self)
        repo.write_rule("alpha", "サンプルの説明", JA_BODY)
        repo.write_rule("beta", "サンプルの説明", JA_BODY)
        repo.commit()
        repo.dictionary(JA_DICTIONARY)

        result = repo.run("beta")

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertEqual(
            result.stdout,
            translated_report(repo.root, ["beta"], ["translating beta"]),
        )
        self.assertFalse((repo.root / "rules.en" / "alpha").exists())
        self.assertEqual(len(repo.calls()), 1)

    def test_an_unknown_name_is_an_error_and_nothing_is_called(self):
        repo = Repo(self)
        repo.write_rule("alpha", "サンプルの説明", JA_BODY)
        repo.commit()
        repo.dictionary(JA_DICTIONARY)

        result = repo.run("alpha", "gamma")

        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, "")
        self.assertEqual(
            result.stderr,
            "gamma: no such rule in rules.ja. pass the name of a directory under rules.ja\n",
        )
        self.assertEqual(repo.calls(), [])
        self.assertEqual(repo.snapshot(), {})


class BasePairErrorTest(unittest.TestCase):
    def assert_nothing_happened(self, repo: Repo, result, before, stderr: str):
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, "")
        self.assertEqual(result.stderr, stderr)
        self.assertEqual(repo.calls(), [])
        self.assertEqual(repo.snapshot(), before)

    def test_uncommitted_rules_en_is_an_error(self):
        repo = Repo(self)
        repo.write_rule("alpha", "サンプルの説明", JA_BODY)
        repo.write_rule("sample", "サンプルの説明", JA_BODY)
        repo.write_en("sample", "A sample description", EN_BODY)
        repo.commit()
        repo.write_rule("sample", "新しい説明", JA_BODY)
        (repo.root / "rules.en/sample/body.md").write_text(
            EN_BODY + "- Edited by hand\n", encoding="utf-8")
        repo.dictionary(JA_DICTIONARY)
        before = repo.snapshot()

        result = repo.run()

        self.assert_nothing_happened(
            repo, result, before,
            "sample: rules.en/sample has uncommitted changes. "
            "commit or discard rules.en/sample, then rerun\n",
        )

    def test_a_root_that_is_not_a_git_repository_is_an_error(self):
        repo = Repo(self)
        repo.write_rule("sample", "サンプルの説明", JA_BODY)
        repo.write_en("sample", "A sample description", EN_BODY)
        shutil.rmtree(repo.root / ".git")
        before = repo.snapshot()

        result = repo.run()

        self.assert_nothing_happened(
            repo, result, before,
            f"rules.en: {repo.root} is not a git repository. "
            "run translate-rules in a git clone of this repository\n",
        )

    def test_a_base_commit_without_the_japanese_rule_is_an_error(self):
        repo = Repo(self)
        repo.write_en("sample", "A sample description", EN_BODY)
        repo.commit()
        commit = git(repo.root, "log", "-1", "--format=%H").strip()[:12]
        repo.write_rule("sample", "サンプルの説明", JA_BODY)
        repo.commit()
        before = repo.snapshot()

        result = repo.run()

        self.assert_nothing_happened(
            repo, result, before,
            f"sample: rules.ja/sample is not in commit {commit}. "
            "delete rules.en/sample to translate it in full, then rerun\n",
        )

    def test_a_base_pair_with_differing_line_counts_is_an_error(self):
        repo = Repo(self)
        repo.write_rule("alpha", "サンプルの説明", JA_BODY)
        repo.write_rule("sample", "サンプルの説明", JA_BODY)
        repo.write_en("sample", "A sample description", EN_BODY + "- A stray line\n")
        repo.commit()
        commit = git(repo.root, "log", "-1", "--format=%H").strip()[:12]
        repo.write_rule("sample", "新しい説明", JA_BODY)
        repo.dictionary(JA_DICTIONARY)
        before = repo.snapshot()

        result = repo.run()

        self.assert_nothing_happened(
            repo, result, before,
            f"sample: rules.ja/sample/body.md has 6 lines and rules.en/sample/body.md has 7 at commit {commit}. "
            "delete rules.en/sample to translate it in full, then rerun\n",
        )


NEXT_ACTION = "make claude -p succeed, then rerun"


class ReportingTest(unittest.TestCase):
    def test_progress_summary_and_paths_over_several_rules(self):
        repo = Repo(self)
        for name in ("alpha", "gamma"):
            repo.write_rule(name, "サンプルの説明", JA_BODY)
            repo.write_en(name, "A sample description", EN_BODY)
        repo.write_rule("beta", "サンプルの説明", JA_BODY)
        repo.commit()
        repo.write_rule("gamma", "新しい説明", JA_BODY)
        repo.dictionary(dict(JA_DICTIONARY, **{"新しい説明": "A new description"}))

        result = repo.run()

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertEqual(result.stderr, "")
        self.assertEqual(
            result.stdout,
            translated_report(
                repo.root, ["beta", "gamma"],
                ["unchanged alpha", "translating beta", "translating gamma"],
            ),
        )


class LineEndingTest(unittest.TestCase):
    def test_a_crlf_checkout_is_unchanged_and_output_is_lf(self):
        repo = Repo(self)
        repo.write_rule("sample", "サンプルの説明", JA_BODY)
        repo.write_en("sample", "A sample description", EN_BODY)
        repo.commit()
        body = repo.root / "rules.ja/sample/body.md"
        body.write_bytes(JA_BODY.replace("\n", "\r\n").encode("utf-8"))

        result = repo.run()

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("unchanged sample\n", result.stdout)
        self.assertEqual(repo.calls(), [])

    def test_a_crlf_change_is_written_with_lf(self):
        repo = Repo(self)
        repo.write_rule("sample", "サンプルの説明", JA_BODY)
        repo.write_en("sample", "A sample description", EN_BODY)
        repo.commit()
        changed = JA_BODY.replace("二つ目", "三つ目")
        (repo.root / "rules.ja/sample/body.md").write_bytes(
            changed.replace("\n", "\r\n").encode("utf-8"))
        repo.dictionary(dict(JA_DICTIONARY, **{"- 三つ目の項目": "- The third item"}))

        result = repo.run()

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertEqual(
            (repo.root / "rules.en/sample/body.md").read_bytes(),
            EN_BODY.replace("second", "third").encode("utf-8"),
        )


class InvalidInputTest(unittest.TestCase):
    def test_a_missing_rules_ja(self):
        repo = Repo(self)
        (repo.root / "README.md").write_text("x\n", encoding="utf-8")
        repo.commit()

        result = repo.run()

        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, "")
        self.assertEqual(result.stderr, "rules.ja: missing rules.ja. create rules.ja\n")
        self.assertEqual(repo.calls(), [])

    def test_invalid_rules_are_all_named_and_nothing_is_called(self):
        repo = Repo(self)
        repo.write_rule("alpha", "サンプルの説明", JA_BODY)
        repo.write_rule("beta", "サンプルの説明", JA_BODY)
        (repo.root / "rules.ja/beta/body.md").unlink()
        repo.write_rule("gamma", "サンプルの説明", JA_BODY)
        (repo.root / "rules.ja/gamma/meta.json").write_text("{", encoding="utf-8")
        repo.write_rule("delta", "サンプルの説明", JA_BODY)
        (repo.root / "rules.ja/delta/meta.json").write_text(
            '{"description": "説明", "cursor": {}, "extra": 1}', encoding="utf-8")
        repo.commit()
        repo.dictionary(JA_DICTIONARY)

        result = repo.run()

        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, "")
        self.assertEqual(
            result.stderr,
            "beta: missing body.md. create body.md\n"
            'delta: unknown key "extra". remove the unknown key or extend the schema\n'
            "gamma: invalid JSON in meta.json. fix meta.json\n",
        )
        self.assertEqual(repo.calls(), [])
        self.assertEqual(repo.snapshot(), {})


class IsolationTest(unittest.TestCase):
    def test_the_translator_starts_isolated_in_an_empty_directory(self):
        repo = Repo(self)
        repo.write_rule("sample", "サンプルの説明", JA_BODY)
        repo.commit()
        repo.dictionary(JA_DICTIONARY)

        result = repo.run()

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        [call] = repo.calls()
        self.assertEqual(call["argv"][:-1], [
            "-p",
            "--model", "claude-sonnet-5-5",
            "--tools", "",
            "--strict-mcp-config",
            "--setting-sources", "",
            "--disable-slash-commands",
            "--no-session-persistence",
            "--system-prompt",
        ])
        self.assertIn(
            "Japanese inside a code fence, including a comment, is translated.",
            call["argv"][-1],
        )
        self.assertEqual(call["cwd_entries"], [])
        cwd = Path(call["cwd"]).resolve()
        self.assertNotEqual(cwd, repo.root.resolve())
        self.assertNotIn(repo.root.resolve(), cwd.parents)
        self.assertFalse(cwd.exists(), msg="the temporary directory is removed")


class AllOrNothingTest(unittest.TestCase):
    def test_a_later_rule_failing_writes_nothing_for_an_earlier_one(self):
        repo = Repo(self)
        repo.write_rule("alpha", "サンプルの説明", JA_BODY)
        repo.write_rule("beta", "サンプルの説明", JA_BODY + "- 訳されない項目\n")
        repo.write_rule("gamma", "サンプルの説明", JA_BODY)
        repo.write_en("gamma", "A sample description", EN_BODY)
        repo.commit()
        repo.write_rule("gamma", "新しい説明", JA_BODY)
        repo.dictionary(dict(JA_DICTIONARY, **{"新しい説明": "A new description"}))
        before = repo.snapshot()

        result = repo.run()

        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, "translating alpha\ntranslating beta\n")
        self.assertEqual(
            result.stderr,
            f"beta: translator output body line 7 still contains Japanese. {NEXT_ACTION}\n",
        )
        self.assertEqual(repo.snapshot(), before)
        self.assertFalse((repo.root / "rules.en" / "alpha").exists())


class TranslatorFailureTest(unittest.TestCase):
    def setUp(self):
        self.repo = Repo(self)
        self.repo.write_rule("sample", "サンプルの説明", JA_BODY)
        self.repo.commit()
        self.repo.dictionary(JA_DICTIONARY)

    def assert_failed(self, result, cause: str):
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, "translating sample\n")
        self.assertEqual(result.stderr, f"sample: {cause}. {NEXT_ACTION}\n")
        self.assertEqual(self.repo.snapshot(), {})

    def test_a_missing_translator(self):
        missing = str(self.repo.fake_dir / "no-such-claude")
        result = subprocess.run(
            [sys.executable, str(install_scripts(self.repo.root) / "translate-rules"),
             "--translator", missing],
            capture_output=True, text=True, encoding="utf-8",
        )
        self.assert_failed(result, f'translator "{missing}" was not found')

    def test_a_translator_that_exits_non_zero(self):
        self.assert_failed(self.repo.run(mode="fail"),
                           "translator exited with status 1 (usage limit reached)")

    def test_a_translator_that_exceeds_the_timeout(self):
        result = self.repo.run("--timeout", "1", mode="sleep")
        self.assert_failed(result, "translator did not finish within 1 seconds")

    def test_output_that_is_not_json(self):
        self.assert_failed(
            self.repo.run(mode="not-json"),
            "translator output is not a JSON object with a description string "
            "and a body array of strings",
        )

    def test_empty_output(self):
        self.assert_failed(self.repo.run(mode="empty"), "translator output is empty")

    def test_output_with_a_different_line_count(self):
        self.assert_failed(self.repo.run(mode="extra-line"),
                           "translator output body has 7 lines for 6 Japanese lines")

    def test_output_that_drops_a_list_marker(self):
        self.repo.dictionary(dict(JA_DICTIONARY, **{"- 二つ目の項目": "The second item"}))
        self.assert_failed(
            self.repo.run(),
            "translator output body line 6 does not keep the Markdown marker of the Japanese",
        )

    def test_output_that_turns_text_into_a_heading(self):
        self.repo.dictionary(dict(JA_DICTIONARY, **{"サンプルの説明": "# A sample description"}))
        self.assert_failed(
            self.repo.run(),
            "translator output description does not keep the Markdown marker of the Japanese",
        )

    def test_output_with_japanese_left(self):
        dictionary = dict(JA_DICTIONARY)
        del dictionary["- 一つ目の項目"]
        self.repo.dictionary(dictionary)
        self.assert_failed(self.repo.run(),
                           "translator output body line 5 still contains Japanese")


if __name__ == "__main__":
    unittest.main()
