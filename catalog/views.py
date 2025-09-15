from django.views.generic import ListView, DetailView

from .models import Product


class ProductListView(ListView):
    model = Product
    paginate_by = 12
    template_name = "catalog/product_list.html"
    context_object_name = "products"

    def get_queryset(self):
        qs = (
            Product.objects.filter(is_active=True)
            .select_related("category")
            .order_by("-updated_at", "-created_at")
        )
        return qs


class ProductDetailView(DetailView):
    model = Product
    template_name = "catalog/product_detail.html"
    context_object_name = "product"
    slug_field = "slug"
    slug_url_kwarg = "slug"

    def get_queryset(self):
        return Product.objects.select_related("category")


