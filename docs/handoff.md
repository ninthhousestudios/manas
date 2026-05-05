# manas — handoff

Date: 2026-05-05
Session intent: scaffold manas-cli, implement adapter trait and skill-shell library.
Prior handoff archived to `.handoffs/2026-05-05T08-19-07.md`.

---

## the headline

manas-cli is scaffolded and has its first real code: adapter trait, Claude Code adapter, and skill-shell library. Three phase-1 tasks completed (/4, /5, /6). **Next step is /7 — port /done to two-layer**, which validates the whole adapter + skill-shell chain end-to-end.

## what shipped this session

- `manas-cli/` — standalone git repo, 3 commits, edition 2024
- Five subcommand stubs (health, warm, done, reflect, status)
- `HarnessAdapter` trait + `ClaudeCodeAdapter` (writes per-session MCP config, spawns `claude --strict-mcp-config`)
- `Binding` struct materializing boot-contract §3 (env vars, Tool Group endpoint)
- `SkillShell::run()` — claim lock → launch body → release lock (finally-pattern)
- `LockClient` trait with `SanghaLockClient` (HTTP/MCP) + `MockLockClient`
- `docs/admin-cred.md` — token storage design (env var → file, dev-mode detection)
- 7 tests (4 integration, 3 unit)

## what to pick up next session — in order

The yojana project `manas-harness` is the source of truth. Concrete next moves:

1. **/7 port /done to two-layer** — now unblocked (needs /5 + /6, both done). Wire the `manas done` command to: claim `handoff` lock via SkillShell, launch CC with the /done prompt body, capture output, write `docs/handoff.md`, release lock. This is the first real end-to-end validation.

2. **/8 Gemini CLI adapter** — mechanical port of ClaudeCodeAdapter. Writes `.gemini/settings.json`, sets `GEMINI_CLI_TRUST_WORKSPACE=true`, uses `--allowed-mcp-server-names`.

3. **/9 Codex CLI adapter** — writes `config.toml` under `CODEX_HOME`, uses `bearer_token_env_var` for token (never written to disk).

4. **/11 sideband daemon (minimal)** — independent of adapter chain, depends only on /4. Unix socket, `path-move-notify` endpoint.

5. **/12 boot contract acceptance test** — needs live mcpjungle. The fixture-harness test from boot-contract.md §6.

## cleanup needed

- Parent `manas/` repo still tracks some `manas-cli/docs/` files (archive/, freshness-envelopes.md, etc.) that now live in the manas-cli repo. Should be `git rm` from parent.

## pointers

### canonical
- `docs/manas-architecture.md` — current state, contracts, interaction rules.
- `docs/roadmap.md` — phases, what's done, what's next.
- `docs/principles.md` — 12 cross-cutting principles.

### this session's artifacts
- `manas-cli/` — the new repo (3 commits on main)
- `manas-cli/docs/admin-cred.md` — admin credential design
- `manas-cli/src/adapter/` — trait + CC impl
- `manas-cli/src/skill/` — shell + lock client
- `manas-cli/src/binding.rs` — boot-contract §3 binding struct
- yojana: manas-harness/4, /5, /6 all marked done
