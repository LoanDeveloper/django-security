from rest_framework import serializers

from .models import Category, Order, Product


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "slug"]


class ProductSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(), source="category", write_only=True
    )

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "slug",
            "price",
            "stock",
            "is_active",
            "created_at",
            "updated_at",
            "category",
            "category_id",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "category"]


class OrderSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)
    product = ProductSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(), source="product", write_only=True
    )

    class Meta:
        model = Order
        fields = [
            "id",
            "user",
            "product",
            "product_id",
            "quantity",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "user", "created_at", "updated_at", "product"]
