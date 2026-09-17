import os
import sys
import tempfile
import unittest
from pathlib import Path

# scripts/ is a sibling of tests/ at the repo root; add the repo root so the
# script imports as a module regardless of where the test runner is invoked.
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import check_pr_branding as checker  # noqa: E402


class FindViolationsTests(unittest.TestCase):
    def test_generated_with_claude_code_footer_is_flagged(self):
        text = "Some real description.\n\nGenerated with Claude Code"
        self.assertTrue(checker.find_violations(text))

    def test_markdown_link_footer_is_flagged(self):
        text = "Body\n\n\U0001F916 Generated with [Claude Code](https://claude.com/claude-code)"
        violations = checker.find_violations(text)
        # The single footer line matches, and it is reported once per line.
        self.assertEqual(len(violations), 1)

    def test_product_links_are_flagged_on_their_own(self):
        self.assertTrue(checker.find_violations("see https://claude.com/claude-code"))
        self.assertTrue(checker.find_violations("built at claude.ai/code today"))

    def test_generic_claude_coauthor_trailer_is_flagged(self):
        text = "Fix thing\n\nCo-authored-by: Claude <noreply@anthropic.com>"
        self.assertTrue(checker.find_violations(text))

    def test_generic_claude_code_coauthor_trailer_is_flagged(self):
        text = "Co-Authored-By: Claude Code <noreply@anthropic.com>"
        self.assertTrue(checker.find_violations(text))

    def test_agent_specific_coauthor_trailer_is_preserved(self):
        # The one attribution the repo wants kept must never be flagged.
        for name in ("Finn", "Tim", "Alex", "Sam"):
            text = f"Real commit body\n\nCo-Authored-By: {name} <noreply@anthropic.com>"
            self.assertEqual(checker.find_violations(text), [], f"{name} trailer was wrongly flagged")

    def test_prose_mentioning_claude_is_not_flagged(self):
        text = (
            "This PR wires up the Claude API client and documents how Claude "
            "handles the request. Nothing here is an attribution line."
        )
        self.assertEqual(checker.find_violations(text), [])

    def test_clean_text_has_no_violations(self):
        self.assertEqual(checker.find_violations("A perfectly ordinary description."), [])

    def test_empty_or_none_text_is_clean(self):
        self.assertEqual(checker.find_violations(""), [])
        self.assertEqual(checker.find_violations(None), [])

    def test_line_numbers_are_one_based(self):
        text = "line one\nline two\nGenerated with Claude Code"
        violations = checker.find_violations(text)
        self.assertEqual(violations[0][0], 3)


class ScanSourcesTests(unittest.TestCase):
    def test_only_dirty_sources_are_returned(self):
        dirty = checker.scan_sources({
            "pr-description": "clean body",
            "commit-messages": "Fix\n\nGenerated with Claude Code",
        })
        self.assertNotIn("pr-description", dirty)
        self.assertIn("commit-messages", dirty)


class MainCliTests(unittest.TestCase):
    def _run_main(self, sources):
        args = []
        paths = []
        with tempfile.TemporaryDirectory() as tmp:
            for label, text in sources.items():
                p = Path(tmp) / f"{label}.txt"
                p.write_text(text, encoding="utf-8")
                args.append(f"{label}={p}")
                paths.append(p)
            return checker.main(args)

    def test_exit_zero_when_all_clean(self):
        self.assertEqual(self._run_main({
            "pr-description": "A normal description.",
            "commit-messages": "Add feature\n\nCo-Authored-By: Finn <noreply@anthropic.com>",
        }), 0)

    def test_exit_one_when_footer_present(self):
        self.assertEqual(self._run_main({
            "pr-description": "Body\n\nGenerated with Claude Code",
            "commit-messages": "Clean commit",
        }), 1)

    def test_missing_file_is_treated_as_empty_not_an_error(self):
        # A PR with no body: the file may not exist. That is clean, not a crash.
        with tempfile.TemporaryDirectory() as tmp:
            missing = Path(tmp) / "pr-description.txt"  # never created
            self.assertEqual(checker.main([f"pr-description={missing}"]), 0)


if __name__ == "__main__":
    unittest.main()
