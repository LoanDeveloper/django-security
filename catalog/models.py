from django.db import models
from django.utils.text import slugify
from django.core.validators import MinValueValidator


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


