from django.contrib import admin

from .models import Category, Product


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "price", "stock", "is_active", "updated_at")
    list_filter = ("category", "is_active")
    search_fields = ("name", "slug", "category__name")
    prepopulated_fields = {"slug": ("name",)}
    autocomplete_fields = ("category",)
    actions = ("mark_active", "mark_inactive")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related("category")

    @admin.action(description="Activer les produits sélectionnés")
    def mark_active(self, request, queryset):
        queryset.update(is_active=True)

    @admin.action(description="Désactiver les produits sélectionnés")
    def mark_inactive(self, request, queryset):
        queryset.update(is_active=False)
