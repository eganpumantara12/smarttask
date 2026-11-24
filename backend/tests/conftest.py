import os

os.environ["DATABASE_URL"] = "sqlite:///./test.db"
os.environ["SECRET_KEY"] = "test-secret-key-test-secret-key-1234"
os.environ["ADMIN_EMAIL"] = "admin@test.id"
os.environ["ADMIN_PASSWORD"] = "adminpass123"

import pytest
from fastapi.testclient import TestClient

from app.database import Base, engine
from app.main import app


@pytest.fixture()
def client():
    Base.metadata.drop_all(engine)
    with TestClient(app) as c:  # lifespan membuat tabel + admin
        yield c


def register(client, email="a@test.id", name="Andi", password="rahasia123"):
    r = client.post("/api/auth/register", json={"name": name, "email": email, "password": password})
    assert r.status_code == 201, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture()
def h1(client):
    return register(client, "a@test.id", "Andi")


@pytest.fixture()
def h2(client):
    return register(client, "b@test.id", "Budi")


@pytest.fixture()
def admin_h(client):
    r = client.post("/api/auth/login", json={"email": "admin@test.id", "password": "adminpass123"})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}
