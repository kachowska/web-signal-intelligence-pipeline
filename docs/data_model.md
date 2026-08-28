# Data model

## companies
Stable entity keyed by canonical domain. `first_seen_at` and `last_seen_at` support lifecycle queries.

## observations
Append-only facts from a crawl feed. `fingerprint` is unique and provides import idempotency. `raw_payload` preserves the original normalized input for debugging/reprocessing.

## technology_signals
One normalized technology value per observation. A composite uniqueness rule prevents duplicate tags inside one observation.

## change_events
Derived events comparing consecutive observations for a company. Currently records `technology_added` and `technology_removed`. This makes historical changes cheap to query without recomputing diffs for every request.
