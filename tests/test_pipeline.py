from datetime import datetime, timedelta, timezone

from websignal.pipeline import ETLPipeline
from websignal.storage.memory import MemoryRepository


def row(at, techs):
    return {"url": "https://www.acme.example/product?utm_source=x", "fetched_at": at.isoformat(), "company_name": "Acme", "technologies": techs}

def test_duplicate_ingest_is_idempotent():
    repo = MemoryRepository(); pipe = ETLPipeline(repo)
    t = datetime(2026,1,1,tzinfo=timezone.utc)
    first = pipe.ingest_records([row(t,["Python","Postgres"])])
    second = pipe.ingest_records([row(t,["Python","Postgres"])])
    assert first.inserted == 1
    assert second.duplicates == 1
    assert repo.stats()["observations"] == 1

def test_change_detection_added_and_removed():
    repo = MemoryRepository(); pipe = ETLPipeline(repo)
    t = datetime(2026,1,1,tzinfo=timezone.utc)
    stats = pipe.ingest_records([row(t,["Python","Postgres"]), row(t+timedelta(days=1),["Python","Rust"])])
    history = repo.history("acme.example")
    assert stats.change_events == 2
    assert {(x["event_type"],x["value"]) for x in history} == {("technology_added","rust"),("technology_removed","postgresql")}

def test_rejected_record_counted():
    repo = MemoryRepository(); pipe = ETLPipeline(repo)
    stats = pipe.ingest_records([{"url":"not-a-domain","fetched_at":"2026-01-01T00:00:00Z"}])
    assert stats.rejected == 1

def test_filter_and_pagination():
    repo = MemoryRepository(); pipe = ETLPipeline(repo)
    t = datetime(2026,1,1,tzinfo=timezone.utc)
    pipe.ingest_records([
        {"url":"https://a.example","fetched_at":t.isoformat(),"technologies":["Python"]},
        {"url":"https://b.example","fetched_at":t.isoformat(),"technologies":["Rust"]},
        {"url":"https://c.example","fetched_at":t.isoformat(),"technologies":["Python"]},
    ])
    assert [x["domain"] for x in repo.list_companies("python",0,10)] == ["a.example","c.example"]
    assert len(repo.list_companies(None,1,1)) == 1
