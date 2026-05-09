# manas — handoff

Date: 2026-05-07

## Immediate

- **smriti/31: Fix corrupted DB.** smriti_health and smriti_find both fail with "database disk image is malformed." FTS5 or vec0 virtual tables corrupted. Main tables are fine. Needs index rebuild. Blocking smriti_find usage.
- **rm chitta/.sessions/sync.sh** — old sync script, transcripts already moved to ~/.sessions/claude-code/. Just needs manual delete.

## Ready to pick up

- **manas-cli backlog** (6 open tasks): sideband daemon, boot contract acceptance test, /reflect port, manas warm codex clobber check, CLAUDE.md + warm interaction, sutra health checkpoint.
- **sangha backlog** (2 tasks): /health endpoint, multi-harness coordination design.
- **darshana implementation** — decision made, design doc updated. First tool: `darshana_impact` (cross-tier blast radius). Lives in manas serve.

## Context for next session

- Yojana projects reorganized: `manas` (ecosystem), `manas-cli` (CLI), `manas-harness` (archived). Check `yojana_query project:manas` and `yojana_query project:manas-cli` for current state.
- All mcpjungle references removed from manas-architecture.md and principles.md.
- Session transcripts now at `~/.sessions/<harness>/` — sync.sh handles claude-code, codex, opencode. /done skill updated.
- External_refs backfill ran but only covered 22/187 path-bearing memories (only resolved paths got refs). Full coverage needs sideband daemon for path-move tracking.
