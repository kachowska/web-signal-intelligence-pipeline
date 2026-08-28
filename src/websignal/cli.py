from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path

from .generator import generate_records
from .pipeline import ETLPipeline
from .storage.memory import MemoryRepository
from .storage.postgres import PostgresRepository


def _db_repo() -> PostgresRepository:
    url = os.getenv("DATABASE_URL")
    if not url:
        raise SystemExit("DATABASE_URL is required for database commands")
    return PostgresRepository(url)


def main() -> None:
    parser = argparse.ArgumentParser(prog="websignal")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("init-db")
    ingest = sub.add_parser("ingest")
    ingest.add_argument("path")
    benchmark = sub.add_parser("benchmark")
    benchmark.add_argument("--records", type=int, default=10000)
    benchmark.add_argument("--seed", type=int, default=7)
    generate = sub.add_parser("generate")
    generate.add_argument("path")
    generate.add_argument("--records", type=int, default=1000)
    generate.add_argument("--seed", type=int, default=7)

    args = parser.parse_args()
    if args.cmd == "init-db":
        repo = _db_repo()
        repo.create_schema()
        print("database schema initialized")
    elif args.cmd == "ingest":
        stats = ETLPipeline(_db_repo()).ingest_jsonl(args.path)
        print(stats.model_dump_json(indent=2))
    elif args.cmd == "benchmark":
        repo = MemoryRepository()
        records = generate_records(args.records, args.seed)
        start = time.perf_counter()
        stats = ETLPipeline(repo).ingest_records(records)
        elapsed = time.perf_counter() - start
        payload = stats.model_dump() | {
            "generated_records": len(records),
            "requested_base_records": args.records,
            "elapsed_seconds": round(elapsed, 4),
            "records_per_second": round(len(records) / max(elapsed, 1e-9), 1),
        }
        print(json.dumps(payload, indent=2))
    elif args.cmd == "generate":
        records = generate_records(args.records, args.seed)
        path = Path(args.path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as fh:
            for row in records:
                fh.write(json.dumps(row) + "\n")
        print(f"wrote {len(records)} rows to {path}")


if __name__ == "__main__":
    main()
