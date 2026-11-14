from conftest import place_order, walk_to


def test_restaurants_menu_search_and_price_filters(world, client):
    rests = client.get("/restaurants", headers=world["c1"]).json()
    assert {r["name"] for r in rests} == {"Rest One", "Rest Two"}
    rid = world["rest1"]["id"]

    menu = client.get(f"/restaurants/{rid}/menu", headers=world["c1"]).json()
    assert len(menu) == 3  # unavailable dishes are still listed
    assert next(m for m in menu if m["name"] == "Vada")["is_available"] is False

    assert [m["name"] for m in client.get(f"/restaurants/{rid}/menu?search=dos", headers=world["c1"]).json()] == ["Dosa"]
    prices = client.get(f"/restaurants/{rid}/menu?min_price=40&max_price=60", headers=world["c1"]).json()
    assert [m["name"] for m in prices] == ["Idli"]
    assert client.get("/restaurants/9999", headers=world["c1"]).status_code == 404


def test_place_order_server_side_price_and_dummy_payment(world, client):
    order = place_order(client, world, qty=3)  # 3 x 70
    assert order["total_amount"] == 210
    assert order["status"] == "PLACED"
    assert order["payment_status"] == "mock_paid"
    assert order["return_status"] == "none"
    assert len(order["payments"]) == 1 and order["payments"][0]["entry_type"] == "payment"
    assert order["items"][0]["unit_price"] == 70


def test_place_order_rules(world, client):
    base = {"restaurant_id": world["rest1"]["id"], "delivery_address": "Hostel Block A"}
    # unavailable dish
    r = client.post("/orders", headers=world["c1"],
                    json={**base, "items": [{"menu_item_id": world["soldout"]["id"], "quantity": 1}]})
    assert r.status_code == 400
    # dish from another restaurant
    r = client.post("/orders", headers=world["c1"],
                    json={**base, "items": [{"menu_item_id": world["pizza"]["id"], "quantity": 1}]})
    assert r.status_code == 400
    # empty cart, bad quantity, short address
    assert client.post("/orders", headers=world["c1"], json={**base, "items": []}).status_code == 422
    assert client.post("/orders", headers=world["c1"],
                       json={**base, "items": [{"menu_item_id": world["dosa"]["id"], "quantity": 0}]}).status_code == 422
    assert client.post("/orders", headers=world["c1"],
                       json={"restaurant_id": base["restaurant_id"], "delivery_address": "x",
                             "items": [{"menu_item_id": world["dosa"]["id"], "quantity": 1}]}).status_code == 422
    # duplicate lines are merged
    r = client.post("/orders", headers=world["c1"], json={**base, "items": [
        {"menu_item_id": world["dosa"]["id"], "quantity": 1},
        {"menu_item_id": world["dosa"]["id"], "quantity": 2},
    ]})
    assert r.status_code == 201 and r.json()["items"][0]["quantity"] == 3 and r.json()["total_amount"] == 210


def test_full_happy_path_lifecycle(world, client):
    order = place_order(client, world)
    oid = order["id"]
    assert client.get(f"/orders/{oid}", headers=world["c1"]).json()["status"] == "PLACED"
    final = walk_to(client, world, oid, "DELIVERED")  # asserts every step returns 200
    assert final["status"] == "DELIVERED"
    assert final["delivery_partner"]["id"] == world["del1"]["id"]
    assert client.get(f"/orders/{oid}", headers=world["c1"]).json()["status"] == "DELIVERED"
    # history shows it for the partner and no longer in active list
    assert client.get("/delivery/history", headers=world["d1"]).json()["total"] == 1
    assert client.get("/delivery/orders", headers=world["d1"]).json()["total"] == 0


def test_invalid_transitions_are_rejected(world, client):
    order = place_order(client, world)
    oid = order["id"]

    def owner_set(status):
        return client.patch(f"/owner/orders/{oid}/status", headers=world["o1"], json={"status": status})

    # skipping steps
    assert owner_set("READY").status_code == 409
    assert owner_set("PREPARING").status_code == 409
    # statuses owners may not set through this endpoint
    assert owner_set("DELIVERED").status_code == 400
    assert owner_set("ASSIGNED").status_code == 400
    assert owner_set("CANCELLED").status_code == 400
    assert owner_set("NONSENSE").status_code == 400
    # cannot assign before READY
    r = client.post(f"/owner/orders/{oid}/assign", headers=world["o1"],
                    json={"delivery_partner_id": world["del1"]["id"]})
    assert r.status_code == 409
    # delivery partner cannot act on an unassigned order
    r = client.patch(f"/delivery/orders/{oid}/status", headers=world["d1"], json={"status": "OUT_FOR_DELIVERY"})
    assert r.status_code == 404

    assert owner_set("ACCEPTED").status_code == 200
    assert owner_set("ACCEPTED").status_code == 409  # not twice
    assert owner_set("PREPARING").status_code == 200
    assert owner_set("READY").status_code == 200
    # assign must be a real delivery partner, not a customer
    r = client.post(f"/owner/orders/{oid}/assign", headers=world["o1"],
                    json={"delivery_partner_id": world["cust1"]["id"]})
    assert r.status_code == 404
    r = client.post(f"/owner/orders/{oid}/assign", headers=world["o1"],
                    json={"delivery_partner_id": world["del1"]["id"]})
    assert r.status_code == 200 and r.json()["status"] == "ASSIGNED"

    # delivery partner: cannot jump to DELIVERED, cannot set other statuses
    set_d = lambda s: client.patch(f"/delivery/orders/{oid}/status", headers=world["d1"], json={"status": s})
    assert set_d("DELIVERED").status_code == 409
    assert set_d("READY").status_code == 400
    assert set_d("OUT_FOR_DELIVERY").status_code == 200
    assert set_d("OUT_FOR_DELIVERY").status_code == 409
    assert set_d("DELIVERED").status_code == 200
    assert set_d("DELIVERED").status_code == 409


def test_customer_cancel_rules(world, client):
    o = place_order(client, world)
    r = client.post(f"/orders/{o['id']}/cancel", headers=world["c1"])
    assert r.status_code == 200
    cancelled = r.json()
    assert cancelled["status"] == "CANCELLED"
    # cancelling a paid order refunds the dummy payment and leaves a ledger trail
    assert cancelled["payment_status"] == "refunded"
    assert [p["entry_type"] for p in cancelled["payments"]] == ["payment", "refund"]
    assert client.post(f"/orders/{o['id']}/cancel", headers=world["c1"]).status_code == 409

    # not allowed once accepted
    o2 = place_order(client, world)
    client.patch(f"/owner/orders/{o2['id']}/status", headers=world["o1"], json={"status": "ACCEPTED"})
    assert client.post(f"/orders/{o2['id']}/cancel", headers=world["c1"]).status_code == 409

    # never after delivery
    o3 = place_order(client, world)
    walk_to(client, world, o3["id"], "DELIVERED")
    assert client.post(f"/orders/{o3['id']}/cancel", headers=world["c1"]).status_code == 409


def test_order_list_filters_and_pagination(world, client):
    ids = [place_order(client, world, qty=1)["id"] for _ in range(5)]
    client.post(f"/orders/{ids[0]}/cancel", headers=world["c1"])
    client.patch(f"/owner/orders/{ids[1]}/status", headers=world["o1"], json={"status": "ACCEPTED"})

    page1 = client.get("/orders?page=1&page_size=2", headers=world["c1"]).json()
    assert page1["total"] == 5 and page1["pages"] == 3 and len(page1["items"]) == 2
    assert page1["items"][0]["id"] == ids[-1]  # newest first
    page3 = client.get("/orders?page=3&page_size=2", headers=world["c1"]).json()
    assert len(page3["items"]) == 1

    assert client.get("/orders?status=CANCELLED", headers=world["c1"]).json()["total"] == 1
    assert client.get("/orders?status=PLACED", headers=world["c1"]).json()["total"] == 3
    assert client.get("/orders?status=BOGUS", headers=world["c1"]).status_code == 422
    assert client.get("/orders?page=0", headers=world["c1"]).status_code == 422

    # date filters (everything was created "today")
    from datetime import date, timedelta
    today = date.today().isoformat()
    tomorrow = (date.today() + timedelta(days=2)).isoformat()
    yesterday = (date.today() - timedelta(days=2)).isoformat()
    assert client.get(f"/orders?date_from={yesterday}&date_to={tomorrow}", headers=world["c1"]).json()["total"] == 5
    assert client.get(f"/orders?date_from={tomorrow}", headers=world["c1"]).json()["total"] == 0
    assert client.get(f"/orders?date_to={yesterday}", headers=world["c1"]).json()["total"] == 0
    assert client.get(f"/orders?date_from={tomorrow}&date_to={yesterday}", headers=world["c1"]).status_code == 422

    # owner view supports the same filters
    assert client.get("/owner/orders?status=ACCEPTED", headers=world["o1"]).json()["total"] == 1
    assert client.get("/owner/orders", headers=world["o1"]).json()["total"] == 5

    # delivery list status filter
    assert client.get("/delivery/orders?status=PLACED", headers=world["d1"]).status_code == 422


def test_timestamps_are_utc_with_z_suffix(world, client):
    order = place_order(client, world)
    assert order["created_at"].endswith("Z")
    assert order["updated_at"].endswith("Z")


def test_date_filter_respects_client_timezone(world, client):
    """An order placed at 20:00 UTC is already 'tomorrow' for an IST (UTC+5:30) user."""
    from datetime import datetime, timedelta

    from app.database import SessionLocal
    from app.models import Order

    order = place_order(client, world)
    fixed = datetime(2026, 11, 14, 20, 0, 0)  # 20:00 UTC == 01:30 IST on 15 Nov
    with SessionLocal() as db:
        db.get(Order, order["id"]).created_at = fixed
        db.commit()

    h = world["c1"]
    # UTC view: it belongs to 14 Nov
    assert client.get("/orders?date_from=2026-11-14&date_to=2026-11-14", headers=h).json()["total"] == 1
    assert client.get("/orders?date_from=2026-11-15&date_to=2026-11-15", headers=h).json()["total"] == 0
    # IST view (tz_offset=330): it belongs to 15 Nov
    assert client.get("/orders?date_from=2026-11-15&date_to=2026-11-15&tz_offset=330", headers=h).json()["total"] == 1
    assert client.get("/orders?date_from=2026-11-14&date_to=2026-11-14&tz_offset=330", headers=h).json()["total"] == 0
    assert client.get("/orders?tz_offset=9999", headers=h).status_code == 422
