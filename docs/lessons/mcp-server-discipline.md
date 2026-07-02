# MCP server discipline (rmcp / Rust)

Ledger row L4. Evidence: manas/22, chitta/9, chitta/46, manas-harness/7,
panini/7, yojana/32, yojana/33, yojana/37, plus the yojana schema convention.
Every item here failed silently from the client's perspective and was found
at integration time, not by unit tests.

## Rules

1. **`SessionConfig::keep_alive` defaults to 300 s** and kills idle sessions
   every 5 minutes. For long-lived local services where SSE stream
   termination already handles cleanup, set `keep_alive = None` (manas/22 —
   this bit five services at once).

2. **Error responses need a body and a Content-Type.** A `401` with neither
   gets misdiagnosed by clients as a protocol/content-type bug, sending the
   debugging session in the wrong direction (chitta/9). Auth-layer rejections
   must still produce well-formed HTTP.

3. **`notifications/initialized` → `202 Accepted`**, not `200 text/plain`
   (chitta/9). Notification endpoints have per-method status-code contracts.

4. **Never use `serde_json::Value` in tool parameter types.** It emits an
   any-type schema (`true`); clients with no type hint serialize nested
   objects as JSON *strings*, the server receives `Value::String("{...}")`,
   and `as_object()` fails on valid input (chitta/46). Give every parameter
   a real schema.

5. **Shutdown ordering: cancel before drain.** Calling `cancel()` after
   `axum::serve` returns hangs on SIGTERM while SSE clients hold streams
   open (panini/7). Cancel the token first, then drain connections.

6. **Schema text is paid on every reload.** Field-level schemars docs are
   serialized into the tool schema and reloaded several times per session;
   put cross-cutting semantics once in the tool-level description (yojana
   `TaskArgs` convention).

7. **Streamable-HTTP clients are not free.** A client of another MCP service
   needs the init handshake, `mcp-session-id` header propagation, and SSE
   parsing — budget for it when a service must call a sibling directly
   (manas-harness/7).

8. **Responses are paid by every consumer, on every call.** Default response
   shapes (full UUIDs, pretty-printed JSON, echoing the whole entity in a
   create/update ack) cost far more tokens than agent consumers use. Slim
   acks to the fields a caller acts on — yojana/32 cut create/update acks
   ~707→26 tokens and yojana/33 halved total schema tokens with no
   functionality loss. Design the response for the agent reading it, not
   for debuggability (that's what logs are for).
