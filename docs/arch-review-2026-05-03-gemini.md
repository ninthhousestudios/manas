# Manas OS Architecture Review

**Date:** May 3, 2026
**Author:** Gemini
**Status:** Review / Synthesis

This document provides a high-level architectural review of the **Manas** ecosystem, contrasting the original vision described in `docs/first-architecture.md` (April 2026) with the current reality of the implemented and designed subsystems.

## The Evolution of the Vision

The original architecture defined Manas as an operating system for collaborative cognition: a set of decoupled subsystems composed by an LLM runtime. The core philosophy remains fully intact:
- **Subsystems do not call each other directly.** The agent orchestrates interactions.
- **Each subsystem owns its domain's history.**
- **MCP is the universal interface.**

However, the implementation has significantly matured and expanded. The ecosystem has transitioned from relying on external tools and raw text files to a robust suite of native, Rust-based, SQLite/Postgres-backed daemons that provide a complete "grammar of work."

## Component Review

### 1. Memory: Chitta (`chitta-rs`)
- **Original Vision:** Store and retrieve *understanding* (observations, decisions, mental models).
- **Current State:** Implemented (v0.1.0). An agent-native persistent memory server backed by Postgres and `pgvector` with a BGE-M3 ONNX embedder.
- **Shift:** Has firmly established the standard for other subsystems: idempotent writes, bi-temporal records, and typed memories. It remains the core of the system's "consciousness."

### 2. Filesystem Perception: Smriti
- **Original Vision:** Planned content-addressed filesystem indexer.
- **Current State:** Implemented (v0.2.3). Smriti provides content-addressed, allowlist-gated indexing using SQLite FTS5 and BLAKE3 hashing.
- **Shift:** It successfully fulfills the "bespoke git for the filesystem" role. It intentionally limits its scope to shallow text search and file discovery, explicitly deferring deep document understanding to Kosha.

### 3. Code Intelligence: Sutra (Replacing Qartez)
- **Original Vision:** "Qartez" was an external, dual-licensed tool for code perception.
- **Current State:** **Sutra** has been implemented to replace Qartez. Sutra is a native, Rust-based code intelligence server that builds a SQLite index via `tree-sitter`.
- **Shift:** Sutra brings code perception fully in-house under the Manas umbrella, providing 14 MCP tools for semantic code navigation, blast radius analysis, and call hierarchies.

### 4. Session Coordination & IPC: Sangha
- **Original Vision:** Session lifecycle and IPC were mostly handled by static files like `docs/handoff.md`.
- **Current State:** Implemented. Sangha is a session coordination daemon providing a session registry, advisory resource locks, and a broadcast inbox.
- **Shift:** Multi-agent and multi-session concurrency is now formally managed. Sangha replaces raw file overwrites with cooperative locking and TTL-based heartbeats, enabling safe parallel workflows.

### 5. Task & Project Management: Yojana
- **Original Vision:** Not present. The system relied on grepping `.sessions/` to answer "what should I work on next?".
- **Current State:** Design Phase. Yojana introduces a typed task graph (the "grammar of work") backed by SQLite.
- **Shift:** This fills a critical gap. Instead of collapsing task tracking into Chitta, Yojana creates a distinct subsystem for dependencies, state machines, and structured context shapes, allowing agent skills to overlay process opinions.

### 6. Document Intelligence: Kosha
- **Original Vision:** N/A (previously the "grantha" concept).
- **Current State:** Design Phase. Kosha sits on top of Smriti to provide deep document intelligence (PDFs, epubs).
- **Shift:** By leveraging Qwen3-VL embeddings, Kosha unifies text and image extraction into a single 2048-dim vector space. It cleanly separates *file awareness* (Smriti) from *content comprehension* (Kosha).

### 7. The Gateway: MCPJungle
- **Original Vision:** Each subsystem would be configured individually in the client (Claude/Gemini).
- **Current State:** Implemented/Integrated. MCPJungle provides a self-hosted MCP gateway.
- **Shift:** As the number of subsystems (Chitta, Smriti, Sutra, Sangha, etc.) grows, MCPJungle centralizes access, observability, and authentication into a single endpoint, significantly reducing client-side configuration overhead.

## Architectural Assessment

1. **Adherence to Principles:** The ecosystem strictly adheres to the "Single Responsibility" principle. Chitta does memory, Smriti does files, Sutra does code, Yojana does tasks. There is no monolith.
2. **Standardized Stack:** A clear pattern has emerged: Rust binaries, SQLite (or Postgres for vector scale) storage, and MCP interfaces. This makes the ecosystem highly predictable and maintainable.
3. **Graceful Degradation:** The decoupled nature ensures that if Kosha or Yojana is down, Sutra and Chitta still function perfectly for code tasks.
4. **Agent-Native Design:** The introduction of "Context Shapes" in Yojana and the deliberate scoping of Smriti vs. Kosha show a deep understanding of LLM token constraints and context window management.

## Conclusion

The Manas OS has successfully moved from a conceptual framework to a concrete, modular ecosystem. The replacement of external dependencies (Qartez) with native tools (Sutra), and the formalization of previously ad-hoc processes (Sangha, Yojana), demonstrates a maturing system architecture that is well-positioned for complex, collaborative AI workflows.