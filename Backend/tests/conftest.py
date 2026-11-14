import os
import tempfile

# Configure the app BEFORE importing it: temp SQLite file, no background loop, no demo data.
_tmp = tempfile.mkdtemp()
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp}/test.db"
os.environ["JWT_SECRET"] = "test-secret-test-secret-test-secret-0123456789"
os.environ["BCRYPT_ROUNDS"] = "4"
os.environ["ENABLE_BACKGROUND_TASKS"] = "false"
os.environ["SEED_DEMO_DATA"] = "false"
os.environ["OPENAI_API_KEY"] = ""

import pytest
from fastapi.testclient import TestClient

from app.database import Base, engine
from app.main import app


@pytest.fixture()
def client():
    Base.metadata.drop_all(bind=engine)
    with TestClient(app) as c:  # runs lifespan -> creates tables
        yield c


class Api:
    """Small helper: register users and call endpoints with their token."""

    def __init__(self, client):
        self.client = client

    def register(self, email, role="CUSTOMER", name="Test User", restaurant_name=None):
        body = {"name": name, "email": email, "password": "secret123", "role": role}
        if restaurant_name:
            body["restaurant_name"] = restaurant_name
        r = self.client.post("/auth/register", json=body)
        assert r.status_code == 201, r.text
        return r.json()

    def login(self, email):
        r = self.client.post("/auth/login", json={"email": email, "password": "secret123"})
        assert r.status_code == 200, r.text
        return {"Authorization": f"Bearer {r.json()['access_token']}"}

    def user(self, email, role="CUSTOMER", **kw):
        info = self.register(email, role, **kw)
        return info, self.login(email)


@pytest.fixture()
def api(client):
    return Api(client)


@pytest.fixture()
def world(api):
    """Two customers, two owners (one restaurant each), two delivery partners, a few dishes."""
    w = {}
    w["cust1"], w["c1"] = api.user("c1@test.com", "CUSTOMER", name="Cust One")
    w["cust2"], w["c2"] = api.user("c2@test.com", "CUSTOMER", name="Cust Two")
    w["owner1"], w["o1"] = api.user(
        "o1@test.com", "RESTAURANT_OWNER", name="Owner One", restaurant_name="Rest One"
    )
    w["owner2"], w["o2"] = api.user(
        "o2@test.com", "RESTAURANT_OWNER", name="Owner Two", restaurant_name="Rest Two"
    )
    w["del1"], w["d1"] = api.user("d1@test.com", "DELIVERY_PARTNER", name="Del One")
    w["del2"], w["d2"] = api.user("d2@test.com", "DELIVERY_PARTNER", name="Del Two")

    client = api.client
    rest1 = client.get("/owner/restaurant", headers=w["o1"]).json()
    rest2 = client.get("/owner/restaurant", headers=w["o2"]).json()
    w["rest1"], w["rest2"] = rest1, rest2

    def add(headers, name, price, category="Main", available=True):
        r = client.post(
            "/owner/menu-items",
            headers=headers,
            json={"name": name, "price": price, "category": category, "is_available": available},
        )
        assert r.status_code == 201, r.text
        return r.json()

    w["dosa"] = add(w["o1"], "Dosa", 70)
    w["idli"] = add(w["o1"], "Idli", 45)
    w["soldout"] = add(w["o1"], "Vada", 30, available=False)
    w["pizza"] = add(w["o2"], "Pizza", 200)
    return w


def place_order(client, world, qty=2, headers=None, item="dosa", rest="rest1"):
    r = client.post(
        "/orders",
        headers=headers or world["c1"],
        json={
            "restaurant_id": world[rest]["id"],
            "items": [{"menu_item_id": world[item]["id"], "quantity": qty}],
            "delivery_address": "Hostel Block A, Room 12",
        },
    )
    assert r.status_code == 201, r.text
    return r.json()


def walk_to(client, world, order_id, target):
    """Drive an order through the happy path up to `target` status."""
    steps = ["ACCEPTED", "PREPARING", "READY", "ASSIGNED", "OUT_FOR_DELIVERY", "DELIVERED"]
    for step in steps:
        if step in ("ACCEPTED", "PREPARING", "READY"):
            r = client.patch(
                f"/owner/orders/{order_id}/status", headers=world["o1"], json={"status": step}
            )
        elif step == "ASSIGNED":
            r = client.post(
                f"/owner/orders/{order_id}/assign",
                headers=world["o1"],
                json={"delivery_partner_id": world["del1"]["id"]},
            )
        else:
            r = client.patch(
                f"/delivery/orders/{order_id}/status", headers=world["d1"], json={"status": step}
            )
        assert r.status_code == 200, f"{step}: {r.text}"
        if step == target:
            return r.json()
