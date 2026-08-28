# Scaling notes

This repository is deliberately small enough to run on a laptop, but the design leaves clear upgrade paths.

1. Partition `observations` by `fetched_at` once the table becomes large.
2. Replace single-process file ingestion with a queue/stream consumer while keeping the idempotent fingerprint contract.
3. Use COPY or staging tables for very large batches, then merge into canonical tables.
4. Maintain materialized latest-company snapshots for read-heavy API traffic.
5. Keep raw crawl payloads in object storage and retain only pointers/hashes in PostgreSQL if payload size becomes dominant.
6. Add a proper public-suffix parser if domain resolution expands beyond controlled feeds.
7. Use consistent hashing / domain partitioning if ingestion is horizontally sharded.
8. Monitor duplicate rate, rejected record rate, batch latency and change-event volume as operational signals.
