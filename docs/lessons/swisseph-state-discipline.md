# SwissEph state & frame discipline

Ledger row L8. Evidence: innerorbits/9, swe-dashboard/2, fletch-astro/4, /5,
/9, /13, /14, /16. Family-scoped: applies to every consumer of swisseph /
swisseph.dart / libaditya bridges (innerorbits, swe-dashboard, fletch-astro,
arjuna, aion, sunflare).

## C-global state

1. **SwissEph configuration is process-wide C globals** (ephemeris path,
   sidereal mode, topocentric position, JPL file). In Dart they drift across
   `await` points and are cleared on Android background→resume
   (innerorbits/9). Re-apply config before every public entry point — the
   facade owns this (`SweFacade._ensureConfig()`, or swe-dashboard's
   `EphemerisRunner.run()/runScoped()` with an `AppliedGlobals` value type
   that diffs state so re-application is idempotent). Per-call-site config
   application is the anti-pattern this replaces.

## Coordinate frames

2. **Label every longitude with its frame** — tropical vs sidereal, ecliptic
   vs equatorial. The bridge bugs were all frame confusion: ayana bala
   computed from sidereal longitude because the bridge context was created
   in SID mode (it requires tropical; fletch-astro/9); nakshatra/pada derived
   by integer division of an *equatorial dhruva-frame* longitude
   (fletch-astro/4, /5 — use the engine's native nakshatra class, not
   `int(lon/13°20′)`).

3. **Custom ayanamsa codes differ between bindings.** Dart and Python
   swisseph disagree on code 98 (Dhruva) by ~4.7° — a library-level
   divergence, not fixable in an adapter (fletch-astro/4). Pin and verify
   ayanamsa values per binding before trusting cross-engine comparisons.

4. **True-node tolerance is 0.005°** across SWE versions for Rahu/Ketu
   (fletch-astro/5); tighter tolerances produce false divergences.

## Cross-engine comparison sweeps

5. **Serialize fine-grained factors, not category strings.** Two engines can
   agree on a sorted list of state names while disagreeing on every
   contributing factor (planet/source/direction/strength) — coarse
   serialization makes the sweep pass vacuously (fletch-astro/13).

6. **Suppress known divergences per-field, never by prefix.** A blanket
   prefix skip silently absorbs future fields added under the same subtree
   (fletch-astro/16). Each accepted divergence gets an explicit key and a
   reason (e.g. argala tiebreaker: Arrow follows Jaimini first-strength
   ranking, libaditya's equal-count rule is wrong but unfixable at the
   adapter; fletch-astro/14).
