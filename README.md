# manas

[![License: AGPL v3](https://img.shields.io/badge/License-AGPL_v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)

**manas** (मनस् — "mind") is a collaborative cognition system for humans and agents. It's a federation of agent-native subsystems that provide memory, perception, coordination, planning, code intelligence, and document comprehension to LLM-driven workflows. The LLM is the cognition; manas is its body.

Each subsystem is a standalone Rust binary with its own MCP server surface, systemd unit, and README.

## Subsystems

| Subsystem | Sanskrit | What it does | Status |
|---|---|---|---|
| [chitta](https://github.com/ninthhousestudios/chitta/) | चित्त — consciousness | Persistent working model of a person: observations, decisions, mental models, session episodes. Postgres + pgvector, BGE-M3 ONNX embeddings, hybrid retrieval. | v0.3.0 |
| [smriti](https://github.com/ninthhousestudios/smriti/) | स्मृति — remembrance | Content-addressed filesystem indexer. Tracks files by BLAKE3 hash, detects moves/copies/edits, emits lifecycle events. SQLite + FTS5. | v0.2.3 |
| [sutra](https://github.com/ninthhousestudios/sutra/) | सूत्र — thread | Code intelligence via tree-sitter. Symbols, calls, deps, blast radius, hotspots, dead code, co-change analysis. SQLite. | v0.1.0 |
| [sangha](https://github.com/ninthhousestudios/sangha/) | संघ — assembly | Session coordination daemon. Registry with heartbeat TTL, advisory resource locks, broadcast inbox. SQLite. | v0.1.0 |
| [kosha](https://github.com/ninthhousestudios/kosha/) | कोश — treasury | Document comprehension. PDFs, EPUBs, scanned pages via multimodal embeddings (Qwen3-VL). Postgres + pgvector. | design |
| [vidya](https://github.com/ninthhousestudios/vidya/) | विद्या — knowledge | Structured knowledge graph with provenance. Cited, tradition-aware domain facts. Postgres. | design |
| [yojana](https://github.com/ninthhousestudios/yojana/) | योजना — plan | Local task graph. Projects, tasks, dependency edges, context shapes. SQLite. | v0.1.0 |
| [manas-cli](https://github.com/ninthhousestudios/manas-cli/) | — | Ops CLI: `manas health`, `manas warm`, `manas done`, `manas serve`. Harness adapters for Claude Code, Codex, Gemini. | v0.1.2 |
| [vidhi](https://github.com/ninthhousestudios/vidhi/) | विधि — method | Engineering methodology skills for Claude Code agents. Planning, TDD, diagnosis, architecture. | v0.1.0 |
| [karma](https://github.com/ninthhousestudios/karma/) | कर्म — action | Personal assistant layer: triggers, connectors, approval gate. | design only |

## Architecture

Each subsystem runs as a local daemon (systemd user service) exposing MCP over streamable HTTP. The CLI (`manas`) ties them together for lifecycle operations — health checks, session warm-up, shutdown.

```
 Agent (Claude Code / Codex / Gemini)
   │
   ├── chitta  :3100  (memory)
   ├── smriti  :3300  (filesystem)
   ├── sutra   :3400  (code intelligence)
   ├── sangha  :3200  (coordination)
   ├── kosha   :3500  (documents)
   ├── yojana  :4200  (tasks)
   └── manas   :3000  (composed ops)
```

See [docs/manas-architecture.md](docs/manas-architecture.md) for the full design.

## Install

Each subsystem builds independently:

```bash
cd <subsystem>
cargo install --path .
```

Most subsystems need a systemd user service. Check each README for prerequisites and setup.

## Context

This is a personal project — built for my own AI workflow. It's public because I believe in open source and because the ideas might be useful to others building similar systems. It is not designed for general-purpose deployment and there is no support commitment. I have "stolen" many ideas from various sources; not source if they are mentioned but I will add that in the future if not. So while I want everyone to respect the license, the ideas and design choices I have made are free to inspect and build upon if you want.

## License

AGPL-3.0 for all subsystems except [vidhi](vidhi/) (MIT, forked from [mattpocock/claude-code-skills](https://github.com/mattpocock/claude-code-skills)).
