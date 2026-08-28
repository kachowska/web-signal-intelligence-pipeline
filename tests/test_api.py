from datetime import datetime, timezone

from fastapi.testclient import TestClient

from websignal.api import create_app
from websignal.pipeline import ETLPipeline
from websignal.storage.memory import MemoryRepository


def client():
    repo = MemoryRepository()
    ETLPipeline(repo).ingest_records([{
        "url":"https://www.acme.example", "fetched_at":datetime(2026,1,1,tzinfo=timezone.utc).isoformat(),
        "company_name":"Acme", "technologies":["Python","PostgreSQL"]
    }])
    return TestClient(create_app(repo))

def test_health():
    assert client().get("/health").json() == {"status":"ok"}

def test_company_search_by_technology():
    r = client().get("/companies", params={"technology":"Python"})
    assert r.status_code == 200
    assert r.json()["items"][0]["domain"] == "acme.example"

def test_company_not_found():
    assert client().get("/companies/missing.example").status_code == 404

def test_stats():
    data = client().get("/stats").json()
    assert data["companies"] == 1
    assert data["observations"] == 1
