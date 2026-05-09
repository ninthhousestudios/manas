# manas — handoff

Date: 2026-05-05
Session intent: port /done to two-layer skill-shell (manas-harness/7)

---

## what to pick up

1. **Sangha systemd service** — crash-looping with `ConnectionClosed("initialize request")`. The unit runs `sangha serve` (stdio mode) but something is trying to connect to it externally. Either fix the service to use `--http` or investigate what's connecting. Low priority — CC uses stdio MCP directly.

--- we tried quite hard to get http to work with sangha and things just werent really
working. later we will think more about sangha and how to connect sessions, because we
also need to include codex, gemini and opencode. theres also a partially relevant note
in ../todo.md.

2. **mcpjungle Tool Group routing** — sub-sessions spawned by `manas done` only see mcpjungle. Chitta, sangha, sutra etc. need to be routable through mcpjungle's Tool Group binding so sub-agents can use them.

3. **Next tasks (manas-harness):**
   - /8 Gemini CLI adapter
   - /9 Codex CLI adapter
   - /11 Sideband daemon (minimal)
   - /12 Boot contract acceptance test

4. **Smoke test artifact** — `.handoffs/2026-05-05T04-41-56.md` is untracked (created by the live smoke test sub-agent). Can delete or commit.

## context

- Sangha HTTP listens on port 3200 (not 4100 as manas-cli config defaults). Config default may need updating, or use env override `MANAS_SANGHA_URL=http://127.0.0.1:3200`.
- All manas-harness tasks /1-/7 are now `done` in yojana. Tasks /8+ are `needs-triage`.
- The `panda` commit message workaround (printf to file, git commit -F) works reliably.
