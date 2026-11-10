from sqlalchemy import inspect, text

from database.postgres_db import dbEngine


def test_alembic_head_and_runs_table_are_applied():
    with dbEngine.connect() as connection:
        revision = connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
        tables = inspect(connection).get_table_names()

    assert revision == "7f6c2e1a9b34"
    assert "runs" in tables
