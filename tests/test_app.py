import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import app, init_db


@pytest.fixture()
def client(tmp_path):
    db_path = tmp_path / "test.db"
    app.config.update(TESTING=True, DATABASE=str(db_path), SECRET_KEY="test-secret")
    init_db()
    with app.test_client() as test_client:
        yield test_client


def register_and_login(client):
    response = client.post("/signup", json={"username": "tester", "password": "pass1234"})
    assert response.status_code == 201
    response = client.post("/login", json={"username": "tester", "password": "pass1234"})
    assert response.status_code == 200


def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json()["status"] == "healthy"


def test_home_requires_login(client):
    response = client.get("/")
    assert response.status_code == 302
    assert "/login" in response.location


def test_signup_and_login(client):
    register_and_login(client)


def test_add_and_list_expense(client):
    register_and_login(client)
    response = client.post("/expenses", json={"amount": 250, "category": "Food", "description": "Lunch", "date": "2026-09-14"})
    assert response.status_code == 201
    expense_id = response.get_json()["id"]
    response = client.get("/expenses")
    assert response.status_code == 200
    expenses = response.get_json()
    assert len(expenses) == 1
    assert expenses[0]["id"] == expense_id
    assert expenses[0]["category"] == "Food"
    assert expenses[0]["amount"] == 250


def test_update_expense(client):
    register_and_login(client)
    response = client.post("/expenses", json={"amount": 100, "category": "Food", "description": "Tea", "date": "2026-09-14"})
    expense_id = response.get_json()["id"]
    response = client.put(f"/expenses/{expense_id}", json={"amount": 180, "category": "Travel", "description": "Bus", "date": "2026-09-13"})
    assert response.status_code == 200
    assert client.get("/expenses").get_json()[0]["amount"] == 180


def test_delete_expense(client):
    register_and_login(client)
    response = client.post("/expenses", json={"amount": 100, "category": "Other", "description": "Test", "date": "2026-09-14"})
    expense_id = response.get_json()["id"]
    response = client.delete(f"/expenses/{expense_id}")
    assert response.status_code == 200
    assert client.get("/expenses").get_json() == []


def test_invalid_expense_is_rejected(client):
    register_and_login(client)
    response = client.post("/expenses", json={"amount": -10, "category": "Food", "date": "2026-09-14"})
    assert response.status_code == 400


def test_unknown_route_returns_404(client):
    response = client.get("/does-not-exist")
    assert response.status_code == 404
    assert response.get_json()["message"] == "Resource not found"
