# Knowledge stack: kosha, vidya, chitta

2026-05-08 — synthesis doc from a session re-grounding the
kosha/chitta/vidya layers in light of (a) the Gemini PH+HDC
conversation and (b) aion's need for cited astrological knowledge.
References: `docs/gemini-convo.md`,
`~/nhs/soft/astrology/aion/docs/architecture-plan-overview.md`.

## TL;DR

- **kosha**: document intelligence — chunks, embeddings, multimodal
  source content. Three collections per deployment: library, practice,
  personal. Reconciled with smriti (file-level perception) instead of
  competing with it.
- **vidya** (new, planned): structured knowledge graph layer. Entities,
  claims, relations, traditions, with provenance back to kosha. The
  **missing layer** that lets an LLM produce *cited*, *tradition-aware*
  domain reasoning instead of confabulating from training data.
- **chitta**: working model of a person. Self-profile (Josh, Sarah) is
  authored by the subject; *modeled* profiles (Sarah's view of client
  Maya) are authored by the practitioner. Per-client profiles for
  ongoing engagements; tag-based for one-off consultations.
- **PH / HDC**: mostly oversold as substrate. They earn their keep as
  *analytics over a real KG*, not as the foundation of one. Cheaper
  alternatives (Tarjan SCC, motif discovery, compression-ratio,
  sequence mining) ship faster and surface the same insights.

## Why this doc exists

A Gemini conversation pitched persistent homology over kosha as the
basis for vidya. That's the inversion of the right layering.
Embeddings have no cognitive structure; voids in a Vietoris-Rips
complex over chunk embeddings are mostly geometric artifacts of the
manifold, not semantic gaps. **The cognitive structure has to come
first; analytics layers run over it.** This doc names the layers,
their responsibilities, and where the analytics actually fit.

## The layers

### kosha — what the books literally say

Document intelligence layer. Decomposes documents (PDF, epub,
markdown, HTML, plain text, images) into leaves → segments → chunks,
embeds via the shared embedder, stores in Postgres + pgvector.

**Three collections** per deployment, sharing primitives but with
distinct ingestion and access patterns:

| Collection | Content | Access pattern | Privacy |
|---|---|---|---|
| Library | Books, papers, ephemerides, references | Semantic search by meaning | Authored content, broad |
| Practice | Client records, sessions, contracts, invoices | Faceted/structured | PII, per-client ACLs |
| Personal | Diary, reflections, private notes | Time-indexed | Strictly private |

Each collection has its own ingestion idiom (semantic chunking for
books; OCR + structured fields for invoices; transcription +
diarization for session recordings) and retrieval defaults. They share
the Rust crate, the Postgres schema for chunks/embeddings, the
embedder, and the provenance model.

**Reconciliation with smriti.** The aion architecture doc (2026-04-21)
gives "smriti" the role kosha now occupies, because kosha didn't exist
yet. The clean split:

- **smriti** = file-level perception (this PDF exists, here's its
  hash, it changed, here's the metadata).
- **kosha** = content-level perception (here are the chunks, here are
  the embeddings, here's how to retrieve by meaning).

Together they replace what aion's doc currently calls "smriti." This
is a decision the aion roadmap needs to absorb.

### vidya — the structured knowledge graph (new)

Domain knowledge as cited, queryable structure. The layer that lets
an LLM reason in a domain *with provenance* instead of confabulating.

#### Why vidya beats pure RAG for astrology specifically

Three properties of astrology that pure RAG fights against:

1. **Tradition-segmented.** Vedic, classical western, Hellenistic, KP
   share vocabulary but disagree on substance. Embedding similarity
   retrieves chunks that *sound* similar; the LLM blends them. The
   output is plausible-sounding but technically wrong — worst kind of
   wrong because you need to be a domain expert to catch it. Vidya
   solves this with `tradition` as a first-class field on every claim.

2. **Rule-based, not textual.** "Saturn exalted in Libra" is a rule,
   not a passage. Pure RAG asks the LLM to reconstruct a rule system
   from retrieved prose every query. Setup for inconsistency. Vidya
   turns rules into queryable facts; the LLM gets prose for nuance,
   the spine is cited structured claims.

3. **Dense structural relationships.** Rulership, exaltation, fall,
   debilitation, mutual reception, aspects — this is a graph. RAG
   flattens the graph to text and asks the LLM to reconstruct on
   demand. Vidya stores the graph and queries it directly.

#### Schema sketch

```
domains(id, slug, title)
entities(id, domain_id, name, kind, metadata)         -- kind: entity | concept
claims(id, domain_id, statement, confidence, status)  -- status: proposed | active | disputed | historical
sources(id, kind, ref)                                -- kind: kosha_chunk | tradition | person
traditions(id, domain_id, name)
relations(id, src_type, src_id, dst_type, dst_id, kind, metadata)
```

Postgres + foreign keys. **No RDF/SPARQL** — the tooling tax doesn't
pay back unless we specifically need OWL reasoning, which we don't.
Matches existing kosha/chitta stack.

Edge kinds:

- `claim --asserts_about--> entity|concept`
- `claim --supported_by--> source` (every claim must have ≥ 1)
- `claim --asserted_by--> tradition`
- `claim --contradicts--> claim` (sources disagree, first-class)
- `claim --refines--> claim`
- `claim --derived_from--> claim`
- `entity --instance_of--> concept`
- `concept --subconcept_of--> concept`
- `entity --R(typed)--> entity` (Saturn --rules--> Capricorn)
- `claim --josh_holds--> chitta_memory_id` (cross-link to personal stance)

Claims are immutable once accepted; corrections are new claims that
supersede via derivation. Status `proposed` → reviewed → `active`;
displaced claims become `historical` rather than being mutated.

#### Extraction pipeline

Three sources, all gated by review:

- **Foundational claims** — hand-curated from canonical texts (BPHS
  for Vedic, Lilly for traditional Western, etc.). Sarah enters with
  citation. Tedious but bounded.
- **LLM-assisted extraction** — LLM proposes claims from kosha chunks;
  practitioner reviews. Status `proposed` → `accepted`. Faster, lower
  precision, gated.
- **Practitioner's accumulated knowledge** — claims learned over years
  not in any one book. Source = self-citation or chitta entry.

The review gate is the quality filter. Without it the KG fills with
LLM-extracted morass.

#### Why astrology is a uniquely tractable domain

Most domains (medicine, law) have unbounded canons — extraction never
ends. **Astrology has a finite foundational rule set**: all dignities,
all aspects, all houses, all dashas, all yogas, planetary
characteristics. Probably thousands of claims, not millions. You can
plausibly *finish* the foundational extraction, then depth comes from
interpretation (LLM + RAG over kosha) on top of structured facts. A
real argument for trying vidya here first.

#### Deployment model

Same shared-subsystem pattern as chitta and smriti:

- vidya-engine — Rust crate, no I/O surface
- vidya-server — thin MCP wrapper
- aion deployment loads astrological domains
- manas deployment loads software/methodology domains (rust, design
  patterns, algorithm complexity, …)
- Both deployments cite kosha for provenance

### chitta — the practitioner's working model

Existing subsystem; two design questions surface from this synthesis.

#### Self vs. modeled profiles

The schema substrate (profile-namespaced memories) supports
multi-tenant per-client modeling. But the **epistemic status** of a
self-profile and a modeled profile is different and the schema should
make this first-class:

- **Self profile** (`kind=self`): authored by the subject + the agent
  watching them. Subject is ground truth. Corrections come from the
  subject.
- **Modeled profile** (`kind=modeled`, `modeled_by=<self_profile>`):
  authored by *another* practitioner about a third party. The
  astrologer's working model of a client. Subject is *not* the author;
  the practitioner is. There is no direct ground truth from the
  subject.

Modeled profiles are useful for the practitioner's work but should
not be confused with portraits of the subject. Practitioner bias is
a feature (data about Sarah's lens), not a bug to flatten.

#### Per-client profiles vs. tag-based

The aion doc proposes `client:<id>` tags inside Sarah's primary
profile. Profile-per-client is a cleaner alternative:

| | tag-based | profile-per-client |
|---|---|---|
| Cross-client queries | trivial | requires fanout |
| Delete a client | easy to miss things | drop the profile, atomic |
| Embedding namespace | shared | isolated per client |
| Modeled-by provenance | implicit | structural |
| Privacy isolation | none | strict |
| Multi-tenant later | hard to retrofit | already there |

**Recommendation**: profile-per-client for ongoing engagements;
tag-based for one-off consultations. They coexist. The privacy
isolation argument is strongest — a chitta query for Sarah's working
model should not accidentally pull a client session memory.

This is also why profile-per-client matters legally: "delete this
client's data" becomes an atomic operation.

## Aion's stack assembled

aion is a single-tenant desktop app for professional astrologers.
**Not multi-tenant hosted** — that simplifies the privacy story
considerably and we should keep it there as long as possible.

```
chart-db        — chart structure + similarity (per-chart vectors)
   |
   v
[the agent answers a question]
   |
   v
+-----------------------------------------------+
| vidya  — astrological claims (cited, typed)   |  ← spine of the answer
| kosha  — books/papers (the prose, multimodal) |  ← nuance and quotation
| chitta — Sarah's notes + per-client profiles  |  ← practice context
| chart-db — this chart                         |  ← the actual subject
+-----------------------------------------------+
   |
   v
LLM synthesizes — citing vidya claims and kosha chunks
```

Privacy/consent (non-negotiable for a professional tool):

- Recording-consent capture in UI before any session recording starts
- Client data delete-on-request — atomic via profile-per-client
- Session-recording retention policy
- Audit log of queries that returned client data
- Possibly: client portal (Maya can see what's stored about her)

## Multimodal

The current embedder is qwen3-vl-embedding (text + image into shared
space). The substrate is in place for image embedding alongside text;
audio/video swap in when a richer multimodal embedder is available.

**Architectural implication: multimodal is an embedder decision, not
an architecture decision.** Storage stays polymorphic over modality;
kosha chunks already support image content; vidya claims cite chunks
regardless of modality. Swapping embedders requires re-embedding the
corpus (mechanical) but no schema migration.

**Caution on diagrams.** CLIP-family image embeddings carry visual
similarity but not semantic meaning. A chart wheel diagram is
findable by "looks like a chart wheel," not by "Sun in Libra in the
4th." For published diagrams in books, run OCR + figure caption +
structured extraction *alongside* the image embedding. The image
embedding makes the diagram findable visually; the extraction layer
makes it queryable semantically.

## Where PH / HDC / motifs / entropy actually fit

The Gemini conversation pitched these as *substrate*. They're better
suited as *analytics over a substrate that already has cognitive
structure*. Where each fits, in priority order:

1. **Tarjan SCC + connected components** — yojana cycle/orphan
   detection. Linear time, ships in a day, replaces the "β1 loops via
   PH" pitch with the right tool. (yojana/17)
2. **Compression-ratio boilerplate detection** — kosha ingest.
   Replaces "Information Bottleneck for boilerplate." 5 lines per
   chunk. (kosha/27)
3. **Temporal sequence mining** over yojana status transitions —
   surfaces real workflow patterns. Replaces static-graph motif
   discovery for task flows (which are temporal, not topological).
   (yojana/18)
4. **Network motif discovery** over the sutra symbol/call/import graph
   — recurring code shapes, interpretable. Real value here.
   (sutra/needs-designing/7)
5. **HDC AST encoding experiment** in sutra — contained research bet,
   either generalizes or closes as null result. Worth a focused week.
   (sutra/needs-designing/8)

PH itself: **revisit once vidya exists.** Motif and component analysis
over a real KG can be meaningful (claim chains, contradiction
clusters, missing-substructure detection on the *graph*, not on the
embedding manifold). PH on a structured graph is more grounded than
PH on embeddings; β2 voids in a sparse claim graph have a chance of
meaning something. Until vidya exists there's nothing real to run it
over.

## Open design questions

These are not yet decisions. They want grilling before any
implementation.

- **kosha collection partitioning**: separate Postgres schemas per
  collection (library / practice / personal) or a single schema with a
  `collection` column? Schemas give cleaner isolation; columns are
  simpler.
- **vidya domain isolation**: same question — separate DBs per
  deployment or per domain, or all in one with a `domain` column?
- **claim subjects**: single subject per claim, multiple, or compound
  (claims about pairs/triples)?
- **claim modality**: do we encode modal claims ("Saturn *can*
  indicate restriction") or only assertoric ones?
- **conflicting claims across traditions**: same entity in multiple
  traditions, or namespace clones per tradition?
- **provenance granularity**: claim → kosha_chunk_id, or
  + character_offset? Probably the latter for citation UX.
- **chitta `kind` migration**: how do we add the self/modeled
  distinction to existing chitta data? All current memories become
  `kind=self` for `profile=josh`?
- **per-client profile naming**: `client_<uuid>` or `client_<slug>`?
  Names leak privacy; UUIDs are opaque. Probably UUIDs with a separate
  alias table.
- **vidya extraction tooling**: what does the LLM-assisted
  proposal-and-review flow look like in aion's UI?

## What to do next

Concrete suggestion from the session: build vidya-engine + vidya-server
in `manas/`, mirroring chitta/smriti structure. Start with **one small
domain** to prove the model — e.g., "western planetary rulerships" or
"Vedic dignities for the seven traditional planets." Maybe 100 claims.
Manually curate with citations to a single canonical source. Get the
agent to answer "what are Saturn's dignities in Vedic astrology?"
using vidya as the spine and kosha for the prose. If the loop feels
right, scale extraction. If wrong, you've spent a week.

Tracking task: `manas/<N>` (this doc's incorporation).
