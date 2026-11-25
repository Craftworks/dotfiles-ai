# Test specification for the language-code rule in scripts/options.py.
#
# Every script builds an edition path from a language code, so the rule is
# shared. The sentence is in scripts/SPEC.md. The script-level tests pin
# the error line for "../x"; these pin which other values are accepted or
# rejected.

import sys
import unittest
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(TESTS_DIR.parent))

import options  # noqa: E402


class LanguageCodeTest(unittest.TestCase):
    def test_letters_digits_hyphen_and_underscore_are_accepted(self):
        for code in ["en", "ja", "zh-CN", "pt_BR", "x1", "A-9_z"]:
            with self.subTest(code=code):
                self.assertEqual(options.language([code], "lang", "en"), code)

    def test_anything_else_is_rejected(self):
        for code in ["a.b", "a/b", "a\\b", "a b", " en", "en\n", "", "..", "é",
                     "a:b", "a$b", "a,b", "a;b"]:
            with self.subTest(code=code):
                with self.assertRaises(options.OptionError):
                    options.language([code], "lang", "en")


if __name__ == "__main__":
    unittest.main()
