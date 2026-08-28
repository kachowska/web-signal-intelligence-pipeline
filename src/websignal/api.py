from __future__ import annotations

import os
from fastapi import Depends, FastAPI, HTTPException, Query

from .normalization import normalize_technology
from .storage.memory import MemoryRepository
from .storage.postgres import PostgresRepository


def build_repository():
    url = os.getenv("DATABASE_URL")
    return PostgresRepository(url) if url else MemoryRepository()


def create_app(repository=None) -> FastAPI:
    app = FastAPI(title="Web Signal Intelligence API", version="0.1.0")
    repo = repository or build_repository()

    def get_repo():
        return repo

    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.get("/companies")
    def companies(
        technology: str | None = None,
        offset: int = Query(0, ge=0),
        limit: int = Query(20, ge=1, le=100),
        repository=Depends(get_repo),
    ):
        tech = normalize_technology(technology) if technology else None
        return {"items": repository.list_companies(tech, offset, limit), "offset": offset, "limit": limit}

    @app.get("/companies/{domain}")
    def company(domain: str, repository=Depends(get_repo)):
        row = repository.get_company(domain.lower())
        if row is None:
            raise HTTPException(status_code=404, detail="company not found")
        return row

    @app.get("/companies/{domain}/history")
    def history(domain: str, repository=Depends(get_repo)):
        return {"items": repository.history(domain.lower())}

    @app.get("/stats")
    def stats(repository=Depends(get_repo)):
        return repository.stats()

    return app


app = create_app()
