from collections.abc import Generator
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401
from app.auth import require_admin, require_employee
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.enums import UserRole, WorkSessionStatus
from app.models.time_tracking import WorkSession
from app.models.user import User


@pytest.fixture
def test_context() -> Generator[tuple[TestClient, Session, User, User], None, None]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    testing_session = sessionmaker(bind=engine, expire_on_commit=False)
    database = testing_session()

    employee = User(
        keycloak_subject="employee-subject",
        email="employee@example.test",
        display_name="Employee Test",
        role=UserRole.EMPLOYEE,
    )
    admin = User(
        keycloak_subject="admin-subject",
        email="admin@example.test",
        display_name="Admin Test",
        role=UserRole.ADMIN,
    )
    other_employee = User(
        keycloak_subject="other-subject",
        email="other@example.test",
        display_name="Other Employee",
        role=UserRole.EMPLOYEE,
    )
    database.add_all([employee, admin, other_employee])
    database.commit()

    def override_database():
        yield database

    app.dependency_overrides[get_db] = override_database
    app.dependency_overrides[require_employee] = lambda: employee
    app.dependency_overrides[require_admin] = lambda: admin

    with TestClient(app) as client:
        yield client, database, employee, other_employee

    app.dependency_overrides.clear()
    database.close()
    Base.metadata.drop_all(engine)
    engine.dispose()


def test_complete_time_tracking_workflow(test_context) -> None:
    client, _, _, _ = test_context

    response = client.get("/api/time/status")
    assert response.status_code == 200
    assert response.json() == {"state": "checked_out", "current_session": None}

    response = client.post(
        "/api/time/check-in",
        json={"source_timezone": "Asia/Colombo", "notes": "Morning shift"},
    )
    assert response.status_code == 201
    assert response.json()["status"] == "open"

    response = client.post("/api/time/check-in", json={"source_timezone": "Asia/Colombo"})
    assert response.status_code == 409
    assert response.json()["detail"] == "An open work session already exists"

    response = client.post(
        "/api/time/breaks/start",
        json={"break_type": "meal", "notes": "Lunch"},
    )
    assert response.status_code == 201
    assert response.json()["active_break"]["break_type"] == "meal"

    response = client.post("/api/time/breaks/start", json={"break_type": "rest"})
    assert response.status_code == 409
    assert response.json()["detail"] == "An active break already exists"

    response = client.post("/api/time/check-out", json={})
    assert response.status_code == 409
    assert response.json()["detail"] == "End the active break before checking out"

    response = client.post("/api/time/breaks/end")
    assert response.status_code == 200
    assert response.json()["active_break"] is None

    response = client.post("/api/time/check-out", json={"notes": "Shift complete"})
    assert response.status_code == 200
    completed = response.json()
    assert completed["status"] == "completed"
    assert completed["ended_at"] is not None
    assert completed["notes"] == "Shift complete"

    response = client.get("/api/time/status")
    assert response.status_code == 200
    assert response.json()["state"] == "checked_out"


def test_employee_history_excludes_other_users(test_context) -> None:
    client, database, employee, other_employee = test_context
    database.add_all(
        [
            WorkSession(
                user_id=employee.id,
                started_at=datetime(2026, 10, 22, 2, 0, tzinfo=timezone.utc),
                ended_at=datetime(2026, 10, 22, 10, 0, tzinfo=timezone.utc),
                status=WorkSessionStatus.COMPLETED,
                source_timezone="Asia/Colombo",
            ),
            WorkSession(
                user_id=other_employee.id,
                started_at=datetime(2026, 10, 22, 3, 0, tzinfo=timezone.utc),
                ended_at=datetime(2026, 10, 22, 11, 0, tzinfo=timezone.utc),
                status=WorkSessionStatus.COMPLETED,
                source_timezone="Asia/Colombo",
            ),
        ]
    )
    database.commit()

    response = client.get("/api/time/sessions")
    assert response.status_code == 200
    sessions = response.json()
    assert len(sessions) == 1
    assert sessions[0]["user_id"] == str(employee.id)

    response = client.get("/api/admin/time/sessions")
    assert response.status_code == 200
    sessions = response.json()
    assert len(sessions) == 2
    assert {session["user_display_name"] for session in sessions} == {
        "Employee Test",
        "Other Employee",
    }


def test_rejects_invalid_timezone_and_actions_without_session(test_context) -> None:
    client, _, _, _ = test_context

    response = client.post("/api/time/check-in", json={"source_timezone": "Mars/Olympus"})
    assert response.status_code == 422
    assert response.json()["detail"] == "Source timezone is not recognized"

    response = client.post("/api/time/breaks/end")
    assert response.status_code == 409
    assert response.json()["detail"] == "Check in before performing this action"

    response = client.post("/api/time/check-out", json={})
    assert response.status_code == 409
    assert response.json()["detail"] == "Check in before performing this action"
