import pytest
from django.urls import reverse

from .models import Category, Product


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


