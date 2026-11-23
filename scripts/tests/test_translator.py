# Test specification for kill_tree in scripts/translator.py.
#
# translate-rules and translate-skills stop a translator through kill_tree.
# A process that outlives the kill, and a taskkill that fails, cannot be
# produced through either command on macOS, so these tests call kill_tree
# with a stand-in process that does not stop.

import subprocess
import sys
import unittest
from pathlib import Path
from unittest import mock

TESTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(TESTS_DIR.parent))

import translator  # noqa: E402


class StuckProcess:
    """A translator process that is still running after it was killed."""

    def __init__(self, pid: int):
        self.pid = pid

    def poll(self):
        return None

    def wait(self, timeout=None):
        if timeout is None:
            raise AssertionError("kill_tree waited without a timeout")
        raise subprocess.TimeoutExpired("translator", timeout)


class KillTreeTest(unittest.TestCase):
    def test_a_process_that_does_not_stop_is_named(self):
        real = subprocess.Popen(["sleep", "30"], start_new_session=True)
        self.addCleanup(real.wait)

        with self.assertRaises(translator.TranslatorFailed) as raised:
            translator.kill_tree(StuckProcess(real.pid))

        self.assertEqual(
            str(raised.exception),
            f"translator process {real.pid} was still running "
            "10 seconds after it was killed",
        )

    def test_a_failed_taskkill_is_named(self):
        failed = subprocess.CompletedProcess(
            ["taskkill"], 1, b"", b"ERROR: Access is denied.\r\n"
        )
        with mock.patch.object(translator.subprocess, "run", return_value=failed), \
                mock.patch.object(translator.os, "name", "nt"):
            with self.assertRaises(translator.TranslatorFailed) as raised:
                translator.kill_tree(StuckProcess(4242))

        self.assertEqual(
            str(raised.exception),
            "taskkill could not stop translator process 4242 "
            "(ERROR: Access is denied.)",
        )


if __name__ == "__main__":
    unittest.main()
