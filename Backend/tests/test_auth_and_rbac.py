from conftest import place_order, walk_to


def test_register_login_me(api, client):
    info = api.register("new@test.com", "CUSTOMER", name="New Person")
    assert info["role"] == "CUSTOMER" and "password" not in info and "password_hash" not in info
    headers = api.login("new@test.com")
    me = client.get("/auth/me", headers=headers).json()
    assert me["email"] == "new@test.com"


def test_duplicate_email_rejected_case_insensitive(api, client):
    api.register("dup@test.com")
    r = client.post(
        "/auth/register",
        json={"name": "Dup", "email": "DUP@test.com", "password": "secret123", "role": "CUSTOMER"},
    )
    assert r.status_code == 409


def test_register_validation(client):
    bad_email = client.post(
        "/auth/register", json={"name": "A B", "email": "nope", "password": "secret123"}
    )
    short_pw = client.post(
        "/auth/register", json={"name": "A B", "email": "a@test.com", "password": "123"}
    )
    bad_role = client.post(
        "/auth/register",
        json={"name": "A B", "email": "b@test.com", "password": "secret123", "role": "ADMIN"},
    )
    assert bad_email.status_code == 422
    assert short_pw.status_code == 422
    assert bad_role.status_code == 422


def test_password_is_bcrypt_hashed(api):
    from app.database import SessionLocal
    from app.models import User
    from sqlalchemy import select

    api.register("hash@test.com")
    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.email == "hash@test.com"))
        assert user.password_hash.startswith("$2") and user.password_hash != "secret123"


def test_login_wrong_password(api, client):
    api.register("x@test.com")
    r = client.post("/auth/login", json={"email": "x@test.com", "password": "wrong-pass"})
    assert r.status_code == 401
    assert client.post("/auth/login", json={"email": "ghost@test.com", "password": "x"}).status_code == 401


def test_protected_endpoints_need_a_valid_token(client):
    assert client.get("/auth/me").status_code == 401
    assert client.get("/restaurants").status_code == 401
    assert client.get("/orders", headers={"Authorization": "Bearer garbage"}).status_code == 401


def test_owner_registration_creates_restaurant(api, client):
    _, headers = api.user("own@test.com", "RESTAURANT_OWNER", name="Sam", restaurant_name="Sam's Place")
    r = client.get("/owner/restaurant", headers=headers).json()
    assert r["name"] == "Sam's Place"


def test_role_walls(world, client):
    # customer cannot reach owner / delivery endpoints
    assert client.get("/owner/orders", headers=world["c1"]).status_code == 403
    assert client.get("/owner/stats", headers=world["c1"]).status_code == 403
    assert client.get("/delivery/orders", headers=world["c1"]).status_code == 403
    # owner cannot place orders or see the customer dashboard API
    assert client.get("/orders", headers=world["o1"]).status_code == 403
    # delivery partner cannot manage menus or orders
    assert client.get("/owner/menu-items", headers=world["d1"]).status_code == 403
    assert client.post("/orders", headers=world["d1"], json={}).status_code == 403
    # customer cannot use AI as owner and vice versa
    assert client.post("/ai/insights", headers=world["o1"], json={"question": "hello"}).status_code == 403


def test_customers_only_see_their_own_orders(world, client):
    order = place_order(client, world, headers=world["c1"])
    assert client.get(f"/orders/{order['id']}", headers=world["c1"]).status_code == 200
    # another customer gets a 404, not the data
    assert client.get(f"/orders/{order['id']}", headers=world["c2"]).status_code == 404
    assert client.post(f"/orders/{order['id']}/cancel", headers=world["c2"]).status_code == 404
    mine = client.get("/orders", headers=world["c2"]).json()
    assert mine["total"] == 0


def test_owner_cannot_touch_other_restaurants_orders_or_menu(world, client):
    order = place_order(client, world, headers=world["c1"])  # belongs to restaurant 1
    r = client.patch(
        f"/owner/orders/{order['id']}/status", headers=world["o2"], json={"status": "ACCEPTED"}
    )
    assert r.status_code == 404
    assert client.get("/owner/orders", headers=world["o2"]).json()["total"] == 0
    # menu item of restaurant 1 edited by owner 2
    r = client.put(
        f"/owner/menu-items/{world['dosa']['id']}",
        headers=world["o2"],
        json={"name": "Hacked", "price": 1, "category": "X"},
    )
    assert r.status_code == 404
    assert client.delete(f"/owner/menu-items/{world['dosa']['id']}", headers=world["o2"]).status_code == 404


def test_delivery_partner_sees_only_assigned_orders(world, client):
    order = place_order(client, world)
    walk_to(client, world, order["id"], "ASSIGNED")
    assert client.get("/delivery/orders", headers=world["d1"]).json()["total"] == 1
    assert client.get("/delivery/orders", headers=world["d2"]).json()["total"] == 0
    r = client.patch(
        f"/delivery/orders/{order['id']}/status",
        headers=world["d2"],
        json={"status": "OUT_FOR_DELIVERY"},
    )
    assert r.status_code == 404
