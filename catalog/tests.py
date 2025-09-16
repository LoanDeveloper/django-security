import time

import pytest
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.urls import reverse
from rest_framework.test import APIClient

from .models import Category, Product

User = get_user_model()


@pytest.mark.django_db
def test_unique_category_slug_constraint():
    cat = Category.objects.create(name="A", slug="a")
    Product.objects.create(category=cat, name="P1", slug="p", price=1, stock=1)
    with pytest.raises(Exception):
        # Violates UniqueConstraint(category, slug)
        Product.objects.create(category=cat, name="P2", slug="p", price=2, stock=1)


@pytest.mark.django_db
def test_product_list_and_detail_views(client):
    cat = Category.objects.create(name="Cat", slug="cat")
    p = Product.objects.create(category=cat, name="Prod", slug="prod", price=10, stock=3)

    # list
    url_list = reverse("product_list")
    resp = client.get(url_list)
    assert resp.status_code == 200
    assert b"Prod" in resp.content

    # detail
    url_detail = reverse("product_detail", args=[p.slug])
    resp = client.get(url_detail)
    assert resp.status_code == 200
    assert b"Prod" in resp.content


@pytest.mark.django_db
def test_api_auth_success_and_fail():
    user = User.objects.create_user(username="bob", email="bob@x.fr", password="pass12345678")
    client = APIClient()
    # Échec
    resp = client.post("/login/", {"identifier": "bob", "password": "wrong"})
    assert resp.status_code in (200, 400, 403)
    # Succès
    resp = client.post("/login/", {"identifier": "bob", "password": "pass12345678"})
    assert resp.status_code in (200, 302)


@pytest.mark.django_db
def test_api_permissions_order_object_level():
    user1 = User.objects.create_user(username="alice", email="alice@x.fr", password="pass12345678")
    user2 = User.objects.create_user(username="bob", email="bob@x.fr", password="pass12345678")
    cat = Category.objects.create(name="Cat", slug="cat")
    prod = Product.objects.create(category=cat, name="Prod", slug="prod", price=10, stock=3)
    from catalog.models import Order

    order = Order.objects.create(user=user1, product=prod, quantity=1)
    client = APIClient()
    client.force_authenticate(user=user2)
    resp = client.get(f"/api/v1/orders/{order.id}/")
    assert resp.status_code in (403, 404)
    client.force_authenticate(user=user1)
    resp = client.get(f"/api/v1/orders/{order.id}/")
    assert resp.status_code == 200


@pytest.mark.django_db
def test_api_throttling_export():
    user = User.objects.create_user(username="throttle", email="t@x.fr", password="pass12345678")
    client = APIClient()
    client.force_authenticate(user=user)
    for _ in range(10):
        resp = client.get("/api/v1/rgpd/export/")
        assert resp.status_code == 200
    resp = client.get("/api/v1/rgpd/export/")
    assert resp.status_code == 429
    time.sleep(6)


@pytest.mark.django_db
def test_api_rgpd_export_and_erase():
    user = User.objects.create_user(username="rgpd", email="rgpd@x.fr", password="pass12345678")
    cat = Category.objects.create(name="Cat", slug="cat")
    prod = Product.objects.create(category=cat, name="Prod", slug="prod", price=10, stock=3)
    from catalog.models import Order

    Order.objects.create(user=user, product=prod, quantity=2)
    client = APIClient()
    client.force_authenticate(user=user)
    # Reset du throttle pour ce user
    cache.clear()
    # Export
    resp = client.get("/api/v1/rgpd/export/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["user"]["email"] == "rgpd@x.fr"
    assert len(data["orders"]) == 1
    # Suppression
    resp = client.post("/api/v1/rgpd/erase/")
    assert resp.status_code == 200
    user.refresh_from_db()
    assert not user.is_active
    assert user.email.startswith("anon_")


@pytest.mark.django_db
def test_api_contracts_errors():
    client = APIClient()
    # 404
    resp = client.get("/api/v1/products/9999/")
    assert resp.status_code == 404
    # 400 sur création order sans auth
    resp = client.post("/api/v1/orders/", {"product_id": 1, "quantity": 1})
    assert resp.status_code in (401, 403)
