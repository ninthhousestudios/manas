# Fail-loud discipline

Provenance: reflect pass (global, 2026-07-02). Evidence: panini/2, panini/4,
panini/13, kosha/29, smriti/24, smriti/26, adityas/backend/10,
adityas/backend/12, arjuna/quiver/10, swe-dashboard/7, sutra/147, sutra/143,
vidya/39. Companion lesson in the store: `019ed6cd-4e71` ("nothing there" vs
"failed to look").

The recurring failure shape: the system reports healthy or successful while
actually degraded, and the real fault surfaces later as a confusing secondary
symptom. Three disciplines prevent it.

## 1. Never convert an error into an empty success

- `.ok()` / `filter_map` / `unwrap_or_default` on a fallible path turns "failed
  to look" into "nothing there". Validate at construction time (compile the
  glob when the rule is parsed, not when it matches) so bad input fails loudly
  at the boundary.
- Per-item loops that swallow individual failures (a PDF page, a sandhi rule, a
  watched subtree) must aggregate and surface the failure count. "Completed
  with fewer segments" is data loss wearing a success face.
- A lookup that can plausibly match nothing needs an explicit warning when it
  matches nothing for a suspicious reason (case-mismatched language ID, zero
  import edges from a whole package family).

## 2. Never collapse distinct failure states into one ambiguous state

- A caught `GrpcError` re-thrown as a generic failure, or a `CalcSweError`
  rendered as an empty result list, is indistinguishable from "no data
  selected". Keep error variants distinct end-to-end; the UI/consumer decides
  how to render them, not the catch site.
- Status models for multi-stage pipelines must cover every interruption point:
  a crash between "row inserted" and "marked error" must not strand a
  permanently-skipped or forever-`processing` record.

## 3. Startup posture: external deps degrade, internal invariants refuse

Two opposite rules, chosen per dependency:

- **External dependency unavailable at startup** (JWKS endpoint, migrations
  runner): degrade and recover. Crash-looping production because a fetch
  failed converts a transient outage into a total one. Run migrations as a
  separate pre-deploy step; let public routes serve while auth warms up.
- **Internal invariant violated at startup** (required rule templates missing,
  mandatory config absent): refuse to start. A server that boots with two of
  five templates and 500s at call time — or worse, produces plausible-but-wrong
  output — has moved the failure somewhere far more expensive. Validate *all*
  of the invariant, not the first item (panini/4 checked one template of five).

The test for which rule applies: can the process do useful degraded work
without it? If yes, degrade loudly. If no, die loudly. The one wrong answer is
the quiet middle.
