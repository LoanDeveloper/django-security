from django.db import migrations, models
import django.db.models.deletion
import django.core.validators


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Category",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("name", models.CharField(max_length=200)),
                ("slug", models.SlugField(max_length=200, unique=True, db_index=True)),
            ],
            options={
                "verbose_name_plural": "Categories",
            },
        ),
        migrations.CreateModel(
            name="Product",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("name", models.CharField(max_length=255)),
                ("slug", models.SlugField(max_length=255)),
                (
                    "price",
                    models.DecimalField(
                        decimal_places=2,
                        max_digits=10,
                        validators=[django.core.validators.MinValueValidator(0)],
                    ),
                ),
                ("stock", models.PositiveIntegerField(default=0)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "category",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="products",
                        to="catalog.category",
                    ),
                ),
            ],
        ),
        migrations.AddIndex(
            model_name="category",
            index=models.Index(fields=["slug"], name="idx_category_slug"),
        ),
        migrations.AddConstraint(
            model_name="product",
            constraint=models.UniqueConstraint(
                fields=("category", "slug"), name="uniq_category_slug"
            ),
        ),
        migrations.AddConstraint(
            model_name="product",
            constraint=models.CheckConstraint(
                check=models.Q(("price__gte", 0)), name="price_gte_0"
            ),
        ),
        migrations.AddIndex(
            model_name="product",
            index=models.Index(fields=["slug"], name="idx_product_slug"),
        ),
        migrations.AddIndex(
            model_name="product",
            index=models.Index(
                fields=["category", "is_active"], name="idx_product_category_active"
            ),
        ),
    ]
