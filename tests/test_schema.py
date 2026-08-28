from sqlalchemy.dialects import postgresql
from sqlalchemy.schema import CreateTable

from websignal.storage.schema import companies, observations, technology_signals, change_events


def test_postgresql_schema_compiles():
    dialect = postgresql.dialect()
    sql = "\n".join(str(CreateTable(t).compile(dialect=dialect)) for t in [companies, observations, technology_signals, change_events])
    assert "JSONB" in sql
    assert "UNIQUE (fingerprint)" in sql
    assert "FOREIGN KEY(company_id)" in sql
