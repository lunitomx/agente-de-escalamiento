# Claude Code adapter

This directory contains client-specific packaging only. The portable core is
the semantic authority; this adapter supplies no methodology, route table, or
additional public command.

`adapter.json` is machine-readable. During a Claude installation, the
installer adds or replaces only the marked ESCALA block from
`CLAUDE.template.md` in `~/.claude/CLAUDE.md`; all content outside that block
is preserved. The installed block uses absolute references valid from the
user's Claude configuration.

The regular installer creates the single public entrypoint in the selected
Claude skills directory and ships the exact MVP capability catalog with a
portable artifact. Remote extensions remain disabled until an explicit
company authorization is recorded.
