"""Fail if a pull request description or commit message carries generic
Claude / "Claude Code" branding or attribution.

This is a public repository. The repo owner does not want generic-Claude
branding anywhere in its history or its pull requests. The Claude Code
harness has a default that tells agents to end PR descriptions with a
"Generated with Claude Code" footer; the standing rule in CLAUDE.md overrides
that default, and this check is the mechanical backstop that guarantees it:
a PR whose body or commits carry the footer fails here and cannot be merged.

What is flagged (attribution and branding only, never prose):

- the "Generated with Claude Code" footer, including its markdown-link form
  "Generated with [Claude Code](...)";
- links to claude.com/claude-code or claude.ai/code;
- a generic co-author trailer whose author name is "Claude" (or "Claude
  Code"), e.g. "Co-authored-by: Claude <noreply@anthropic.com>".

What is deliberately NOT flagged:

- the agent-specific trailer "Co-Authored-By: <AgentName>" (Finn, Tim, ...),
  which is the one and only attribution this repo wants preserved;
- ordinary prose that happens to mention Claude or the Claude API. Only
  attribution/branding lines are matched, so a PR that legitimately discusses
  Claude does not fail.

Pure standard library, no third-party dependency, so it runs anywhere and is
trivially unit-tested. Usage:

    python scripts/check_pr_branding.py LABEL=path [LABEL=path ...]

Each argument names a text source (LABEL) and a file to read it from. The
check reads every source, prints any violations with their source label and
line number, and exits non-zero if any source is dirty. A missing file is
treated as empty (a PR may have an empty body), never an error.
"""

import re
import sys

# Each pattern targets an attribution/branding line, not a bare mention of
# the word "Claude". Case-insensitive.
_BRANDING_PATTERNS = (
    # "Generated with Claude Code" and "Generated with [Claude Code](...)".
    re.compile(r"generated with\s+\[?claude code", re.IGNORECASE),
    # The Claude Code product links used in the footer.
    re.compile(r"claude\.com/claude-code", re.IGNORECASE),
    re.compile(r"claude\.ai/code", re.IGNORECASE),
    # A generic co-author trailer whose NAME is Claude / Claude Code. An
    # agent-specific name (Finn, Tim, ...) does not match, so those trailers
    # are preserved.
    re.compile(r"co-authored-by:\s*claude(\s+code)?\b", re.IGNORECASE),
)


def find_violations(text):
    """Return a list of (line_number, line, pattern) for every line in text
    that carries generic-Claude branding or attribution. line_number is
    1-based. An empty or None text yields no violations."""
    violations = []
    if not text:
        return violations
    for index, line in enumerate(text.splitlines(), start=1):
        for pattern in _BRANDING_PATTERNS:
            if pattern.search(line):
                violations.append((index, line.strip(), pattern.pattern))
                break
    return violations


def scan_sources(sources):
    """sources: dict of {label: text}. Return {label: violations} for every
    label whose text has at least one violation."""
    dirty = {}
    for label, text in sources.items():
        violations = find_violations(text)
        if violations:
            dirty[label] = violations
    return dirty


def _read_source_arg(arg):
    if "=" not in arg:
        raise SystemExit(
            f"Bad argument {arg!r}: expected LABEL=path (e.g. pr-description=body.txt)."
        )
    label, path = arg.split("=", 1)
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return label, handle.read()
    except FileNotFoundError:
        # A PR may legitimately have no body; an absent file is empty, not an
        # error. This keeps the check from failing for the wrong reason.
        return label, ""


def main(argv):
    if not argv:
        raise SystemExit("Usage: python scripts/check_pr_branding.py LABEL=path [LABEL=path ...]")

    sources = dict(_read_source_arg(arg) for arg in argv)
    dirty = scan_sources(sources)

    if not dirty:
        print("No generic Claude branding found in the PR description or commit messages.")
        return 0

    print("Generic Claude branding / attribution is not allowed on this public repository.")
    print("See the 'Attribution on this public repository' section of CLAUDE.md.\n")
    for label, violations in dirty.items():
        print(f"In {label}:")
        for line_number, line, _pattern in violations:
            print(f"  line {line_number}: {line}")
        print()
    print(
        "Remove the branding above. Keep only the agent-specific "
        "'Co-Authored-By: <AgentName>' trailer."
    )
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
