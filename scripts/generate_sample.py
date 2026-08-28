from pathlib import Path
import json
from websignal.generator import generate_records

out = Path("data/sample_crawl.jsonl")
out.parent.mkdir(exist_ok=True)
with out.open("w", encoding="utf-8") as f:
    for row in generate_records(40, seed=3):
        f.write(json.dumps(row) + "\n")
print(out)
