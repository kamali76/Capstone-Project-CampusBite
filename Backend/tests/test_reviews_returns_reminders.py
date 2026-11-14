from datetime import timedelta

from conftest import place_order, walk_to


def test_review_rules(world, client):
    o = place_order(client, world)
    # not delivered yet
    r = client.post(f"/orders/{o['id']}/review", headers=world["c1"], json={"rating": 5})
    assert r.status_code == 409

    walk_to(client, world, o["id"], "DELIVERED")
    assert client.post(f"/orders/{o['id']}/review", headers=world["c1"], json={"rating": 6}).status_code == 422
    assert client.post(f"/orders/{o['id']}/review", headers=world["c1"], json={"rating": 0}).status_code == 422
    # someone else's order
    assert client.post(f"/orders/{o['id']}/review", headers=world["c2"], json={"rating": 5}).status_code == 404

    r = client.post(f"/orders/{o['id']}/review", headers=world["c1"], json={"rating": 4, "comment": "Tasty"})
    assert r.status_code == 201 and r.json()["rating"] == 4
    # only one review per order
    assert client.post(f"/orders/{o['id']}/review", headers=world["c1"], json={"rating": 5}).status_code == 409

    # restaurant rating is now visible
    rest = client.get(f"/restaurants/{world['rest1']['id']}", headers=world["c1"]).json()
    assert rest["rating"] == 4.0 and rest["review_count"] == 1
    assert client.get(f"/orders/{o['id']}", headers=world["c1"]).json()["review"]["comment"] == "Tasty"


def test_return_requires_delivery_reason_and_is_single(world, client):
    o = place_order(client, world)
    assert client.post(f"/orders/{o['id']}/return", headers=world["c1"], json={"reason": "cold food"}).status_code == 409

    walk_to(client, world, o["id"], "DELIVERED")
    assert client.post(f"/orders/{o['id']}/return", headers=world["c1"], json={}).status_code == 422
    assert client.post(f"/orders/{o['id']}/return", headers=world["c1"], json={"reason": "  "}).status_code == 422
    assert client.post(f"/orders/{o['id']}/return", headers=world["c2"], json={"reason": "not mine"}).status_code == 404

    r = client.post(f"/orders/{o['id']}/return", headers=world["c1"], json={"reason": "Food arrived cold"})
    assert r.status_code == 201 and r.json()["status"] == "requested"
    assert client.get(f"/orders/{o['id']}", headers=world["c1"]).json()["return_status"] == "requested"
    # no second request for the same order
    assert client.post(f"/orders/{o['id']}/return", headers=world["c1"], json={"reason": "Another reason"}).status_code == 409


def test_return_approval_refunds_the_order(world, client):
    o = place_order(client, world)
    walk_to(client, world, o["id"], "DELIVERED")
    client.post(f"/orders/{o['id']}/return", headers=world["c1"], json={"reason": "Wrong dish delivered"})

    pending = client.get("/owner/returns?status=requested", headers=world["o1"]).json()
    assert pending["total"] == 1
    rid = pending["items"][0]["id"]
    assert pending["items"][0]["order"]["id"] == o["id"]
    # other owner can't see or decide it
    assert client.get("/owner/returns", headers=world["o2"]).json()["total"] == 0
    assert client.patch(f"/owner/returns/{rid}", headers=world["o2"], json={"decision": "approve"}).status_code == 404
    # customers/partners can't decide
    assert client.patch(f"/owner/returns/{rid}", headers=world["c1"], json={"decision": "approve"}).status_code == 403
    assert client.patch(f"/owner/returns/{rid}", headers=world["o1"], json={"decision": "maybe"}).status_code == 422

    r = client.patch(f"/owner/returns/{rid}", headers=world["o1"], json={"decision": "approve"})
    assert r.status_code == 200 and r.json()["status"] == "approved"
    order = client.get(f"/orders/{o['id']}", headers=world["c1"]).json()
    assert order["status"] == "REFUNDED"
    assert order["payment_status"] == "refunded"
    assert order["return_status"] == "approved"
    assert [p["entry_type"] for p in order["payments"]] == ["payment", "refund"]
    # decided requests cannot be decided again
    assert client.patch(f"/owner/returns/{rid}", headers=world["o1"], json={"decision": "reject"}).status_code == 409


def test_return_rejection_keeps_order_delivered(world, client):
    o = place_order(client, world)
    walk_to(client, world, o["id"], "DELIVERED")
    client.post(f"/orders/{o['id']}/return", headers=world["c1"], json={"reason": "Changed my mind"})
    rid = client.get("/owner/returns", headers=world["o1"]).json()["items"][0]["id"]

    r = client.patch(f"/owner/returns/{rid}", headers=world["o1"], json={"decision": "reject"})
    assert r.status_code == 200 and r.json()["status"] == "rejected"
    order = client.get(f"/orders/{o['id']}", headers=world["c1"]).json()
    assert order["status"] == "DELIVERED"
    assert order["payment_status"] == "mock_paid"
    assert order["return_status"] == "rejected"
    # a rejected order cannot be re-requested
    assert client.post(f"/orders/{o['id']}/return", headers=world["c1"], json={"reason": "Trying again"}).status_code == 409


def test_menu_management(world, client):
    h = world["o1"]
    item = client.post("/owner/menu-items", headers=h,
                       json={"name": "Pongal", "price": 55, "category": "Tiffin"}).json()
    assert item["is_available"] is True
    assert client.post("/owner/menu-items", headers=h, json={"name": "Bad", "price": -5}).status_code == 422
    assert client.post("/owner/menu-items", headers=h, json={"name": "Free", "price": 0}).status_code == 422

    r = client.put(f"/owner/menu-items/{item['id']}", headers=h,
                   json={"name": "Ven Pongal", "price": 60, "category": "Tiffin", "description": "Ghee"})
    assert r.json()["name"] == "Ven Pongal" and r.json()["price"] == 60

    r = client.patch(f"/owner/menu-items/{item['id']}/availability", headers=h, json={"is_available": False})
    assert r.json()["is_available"] is False
    # an unavailable dish cannot be ordered
    r = client.post("/orders", headers=world["c1"], json={
        "restaurant_id": world["rest1"]["id"], "delivery_address": "Hostel Block A",
        "items": [{"menu_item_id": item["id"], "quantity": 1}]})
    assert r.status_code == 400

    # deleting a dish keeps old orders intact (name/price are snapshotted)
    placed = place_order(client, world, item="idli")
    assert client.delete(f"/owner/menu-items/{world['idli']['id']}", headers=h).status_code == 204
    old = client.get(f"/orders/{placed['id']}", headers=world["c1"]).json()
    assert old["items"][0]["name"] == "Idli" and old["items"][0]["menu_item_id"] is None


def test_stats(world, client):
    a = place_order(client, world, qty=2)             # 140
    b = place_order(client, world, qty=1, item="idli")  # 45
    c = place_order(client, world, qty=1)             # cancelled, not revenue
    client.post(f"/orders/{c['id']}/cancel", headers=world["c1"])
    walk_to(client, world, a["id"], "DELIVERED")
    client.post(f"/orders/{a['id']}/review", headers=world["c1"], json={"rating": 5})

    s = client.get("/owner/stats", headers=world["o1"]).json()
    assert s["total_orders"] == 3
    assert s["orders_today"] == 3
    assert s["revenue"] == 185
    assert s["orders_by_status"] == {"DELIVERED": 1, "PLACED": 1, "CANCELLED": 1}
    assert s["top_items"][0] == {"name": "Dosa", "quantity": 2}
    assert s["average_rating"] == 5.0 and s["review_count"] == 1
    assert s["pending_returns"] == 0
    # the other restaurant sees none of it
    assert client.get("/owner/stats", headers=world["o2"]).json()["total_orders"] == 0


def _age_order(order_id, minutes):
    from app.database import SessionLocal
    from app.models import Order, utcnow

    with SessionLocal() as db:
        order = db.get(Order, order_id)
        order.updated_at = utcnow() - timedelta(minutes=minutes)
        db.commit()


def test_reminders_for_stale_orders(world, client):
    fresh = place_order(client, world)
    stale = place_order(client, world)
    accepted_stale = place_order(client, world)
    client.patch(f"/owner/orders/{accepted_stale['id']}/status", headers=world["o1"], json={"status": "ACCEPTED"})
    preparing_stale = place_order(client, world)
    for s in ("ACCEPTED", "PREPARING"):
        client.patch(f"/owner/orders/{preparing_stale['id']}/status", headers=world["o1"], json={"status": s})

    _age_order(stale["id"], 20)
    _age_order(accepted_stale["id"], 16)
    _age_order(preparing_stale["id"], 60)  # PREPARING is not a reminder status
    _age_order(fresh["id"], 5)

    reminders = client.get("/owner/reminders", headers=world["o1"]).json()
    assert {r["order_id"] for r in reminders} == {stale["id"], accepted_stale["id"]}
    assert all(r["still_pending"] for r in reminders)
    # idempotent: asking again creates no duplicates
    assert len(client.get("/owner/reminders", headers=world["o1"]).json()) == 2
    assert client.get("/owner/stats", headers=world["o1"]).json()["active_reminders"] == 2
    # other restaurants never see them
    assert client.get("/owner/reminders", headers=world["o2"]).json() == []
    # acting on the order clears the reminder from the dashboard
    client.patch(f"/owner/orders/{stale['id']}/status", headers=world["o1"], json={"status": "ACCEPTED"})
    remaining = client.get("/owner/reminders", headers=world["o1"]).json()
    assert {r["order_id"] for r in remaining} == {accepted_stale["id"]}


def test_background_job_function(world, client):
    from app.database import SessionLocal
    from app.services.reminders import generate_reminders

    o = place_order(client, world)
    _age_order(o["id"], 30)
    with SessionLocal() as db:
        assert generate_reminders(db) == 1
        assert generate_reminders(db) == 0  # no duplicates


def test_middleware_headers_and_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.headers["X-Process-Time"].endswith("ms")
    assert r.headers["X-Request-ID"]
