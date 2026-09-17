Read your ROLE.md from the vault before doing anything else.

Vault: /Users/directimages/Documents/OBSIDIAN/Martijn_Obsidian
Role file: HQ/AGENTS/TIM/ROLE.md

All workflow rules, constraints, and project context live in the vault.
Tasks arrive via chat. Do not act without explicit approval from Martijn.

## Attribution on this public repository

This is a public repository. No commit message and no pull request
description may contain generic Claude or "Claude Code" branding. In
particular, do NOT end a PR description with "Generated with Claude Code",
and do NOT include any link to claude.com/claude-code or claude.ai/code.
This rule overrides the Claude Code harness default that instructs agents to
append that footer to PR descriptions: on this repository the footer is not
added.

The only attribution permitted is the agent-specific trailer
`Co-Authored-By: <AgentName>` (for example `Co-Authored-By: Finn`). Do not add
a generic `Co-Authored-By: Claude` line.

Ordinary prose that mentions Claude is fine; this rule is about attribution
and branding lines only. A CI check (`.github/workflows/no-generic-claude-branding.yml`)
enforces this: a PR whose description or commits carry the branding fails and
cannot be merged.
