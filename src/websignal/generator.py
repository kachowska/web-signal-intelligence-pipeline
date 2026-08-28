from __future__ import annotations

import random
from datetime import datetime, timedelta, timezone

TECH = ["Python", "PostgreSQL", "TypeScript", "Rust", "React", "Redis", "Docker", "Go", "Node.js"]


def generate_records(count: int, seed: int = 7) -> list[dict]:
    rng = random.Random(seed)
    base = datetime(2026, 1, 1, tzinfo=timezone.utc)
    domains = [f"company-{i:04d}.example" for i in range(max(1, count // 4))]
    records: list[dict] = []
    for i in range(count):
        domain = domains[i % len(domains)]
        tech_count = 2 + rng.randrange(0, 4)
        techs = rng.sample(TECH, tech_count)
        records.append({
            "url": f"https://www.{domain}/products/{i % 11}?utm_source=synthetic",
            "fetched_at": (base + timedelta(hours=i // max(1, len(domains)))).isoformat(),
            "company_name": domain.split(".")[0].replace("-", " ").title(),
            "title": f"Product page {i % 11}",
            "text": "Generated crawl observation for deterministic pipeline validation.",
            "technologies": techs,
        })
        if i and i % 20 == 0:
            records.append(dict(records[-1]))
    return records
