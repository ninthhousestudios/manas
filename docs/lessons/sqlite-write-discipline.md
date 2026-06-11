# SQLite write discipline

Ledger row L1. Evidence: smriti/31, sutra/90, sutra/103, sutra/125, sutra/140,
sutra/141, sutra/21, yojana/23. The same write-path hazards were independently
rediscovered in three codebases; this is the canonical statement.

## Rules

1. **One durable writer per DB file.** A per-process `Mutex` around the
   connection serializes nothing for other processes opening the same file
   (yojana/23: phase transitions are read-modify-write and can interleave
   across processes; sutra/21: a second process's reparse raced the daemon's
   scheduler on the same DB). Cross-process exclusion needs a file lock or a
   single owning daemon that others talk to.

2. **Every multi-statement mutation runs in a transaction.** The
   DELETE-then-bulk-INSERT "replace" pattern was written untransacted four
   separate times (`replace_health_findings`, `replace_hrr_vectors`
   sutra/103; `replace_pattern_families` sutra/90; `delete_file_cascade`
   sutra/103) — a crash mid-loop leaves silent partial state. If a write
   spans more than one statement, wrap it. No exceptions for "it's fast".

3. **Long-lived reader connections go stale on FTS5.** After the writer
   automerges FTS5 shadow tables, an old readonly connection returns
   `database disk image is malformed` on MATCH while non-FTS queries on the
   same connection still work and `PRAGMA integrity_check` passes — the
   on-disk data is fine; the connection's page-cache view is not (smriti/31).
   Use short-lived reader connections, or treat that error as "reopen and
   retry", never as data corruption.

4. **Correctness flags live in the DB, not in memory.** An in-memory
   "needs_resolution" set lost on restart left indexes permanently poisoned
   (sutra/140). The fix pattern: persistent per-row flag plus a generation
   pair in a meta table, checked on read. Corollary for migrations: a new
   completion-flag column must not `DEFAULT` to "complete" — that assumption
   silently defeats crash recovery for pre-upgrade state (sutra/140
   migration 0037).

5. **Order durable writes so crash points are safe.** Marking dependent rows
   *after* a cascade has wiped the data needed to find them means a crash in
   between loses the queue entry forever (sutra/140 post-review). Write the
   durable intent first, then mutate.

6. **Throughput: WAL, `synchronous=NORMAL`, batched writes** (sutra/141).
   Tune after correctness, not instead of it.
