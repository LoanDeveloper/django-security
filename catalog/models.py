from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, db_index=True)

    class Meta:
        verbose_name_plural = "Categories"
        indexes = [
            models.Index(fields=["slug"], name="idx_category_slug"),
        ]

    def __str__(self) -> str:
        return self.name


class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="products")
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    stock = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["category", "slug"], name="uniq_category_slug"),
            models.CheckConstraint(check=models.Q(price__gte=0), name="price_gte_0"),
        ]
        indexes = [
            models.Index(fields=["slug"], name="idx_product_slug"),
            models.Index(fields=["category", "is_active"], name="idx_product_category_active"),
        ]

    def __str__(self) -> str:
        return self.name


class Order(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="orders",
        null=True,
        blank=True,
    )
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="orders")
    quantity = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Commande {self.id} de {self.user}"
