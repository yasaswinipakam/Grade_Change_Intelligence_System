"""SQLite verification for the portable database schema."""

import sqlite3
from pathlib import Path

import pytest


@pytest.fixture()
def database() -> sqlite3.Connection:
    connection = sqlite3.connect(":memory:")
    connection.execute("PRAGMA foreign_keys = ON")
    connection.executescript(Path("schema.sql").read_text())
    return connection


def test_schema_creates_samples_and_supports_query_patterns(database: sqlite3.Connection) -> None:
    assert database.execute("SELECT COUNT(*) FROM process_data_log").fetchone()[0] == 3
    assert database.execute("SELECT COUNT(*) FROM recommendations").fetchone()[0] == 3
    assert database.execute("SELECT COUNT(*) FROM feedback").fetchone()[0] == 3

    # Time-range recommendations, feedback lookup, acceptance rate, feature data,
    # and comparable historical risk-band queries.
    assert len(database.execute("SELECT * FROM recommendations WHERE timestamp >= '2026-07-25T14:00:00Z'").fetchall()) == 3
    assert len(database.execute("SELECT * FROM feedback WHERE recommendation_id = 'a1111111-1111-4111-8111-111111111111'").fetchall()) == 1
    assert database.execute("SELECT AVG(operator_response = 'accept') FROM feedback").fetchone()[0] == 1.0
    assert len(database.execute("SELECT * FROM process_data_log WHERE grade = 'Copy Paper 20lb'").fetchall()) == 1
    assert len(database.execute("SELECT * FROM recommendations WHERE risk_score BETWEEN 60 AND 90").fetchall()) == 2


def test_constraints_foreign_key_and_indexes(database: sqlite3.Connection) -> None:
    with pytest.raises(sqlite3.IntegrityError):
        database.execute("INSERT INTO recommendations (recommendation_id, risk_score, predicted_deviation, action, confidence, similar_cases, success_rate, avg_stabilization_minutes, timestamp, grade) VALUES ('bad', 150, 0, 'x', 1, 1, 1, 1, '2026-07-25T15:00:00Z', 'x')")
    with pytest.raises(sqlite3.IntegrityError):
        database.execute("INSERT INTO feedback (feedback_id, recommendation_id, operator_response, timestamp) VALUES ('bad', 'missing', 'accept', '2026-07-25T15:00:00Z')")
    with pytest.raises(sqlite3.IntegrityError):
        database.execute("INSERT INTO feedback (feedback_id, recommendation_id, operator_response, timestamp) VALUES ('bad2', 'a1111111-1111-4111-8111-111111111111', 'wait', '2026-07-25T15:00:00Z')")

    indexes = {row[1] for row in database.execute("PRAGMA index_list('recommendations')")}
    assert {"idx_recommendations_timestamp", "idx_recommendations_risk_score"}.issubset(indexes)
