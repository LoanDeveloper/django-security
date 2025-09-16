from django.views.generic import DetailView, ListView
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, mixins, viewsets
from rest_framework.permissions import (
    BasePermission,
    IsAuthenticatedOrReadOnly,
)

from .models import Category, Order, Product
from .serializers import CategorySerializer, OrderSerializer, ProductSerializer


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


class IsAdminOrManager(BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return (
            request.user.is_staff
            or request.user.groups.filter(name__in=["admin", "manager"]).exists()
        )


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.select_related("category")
    serializer_class = ProductSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    filterset_fields = ["category", "is_active"]
    ordering_fields = ["price", "created_at", "updated_at"]
    search_fields = ["name", "slug"]

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [IsAuthenticatedOrReadOnly()]
        return [IsAdminOrManager()]


class CategoryViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = []  # Public


class OrderPermission(BasePermission):
    def has_object_permission(self, request, view, obj):
        if (
            request.user.is_staff
            or request.user.groups.filter(name__in=["admin", "manager"]).exists()
        ):
            return True
        return obj.user == request.user

    def has_permission(self, request, view):
        if view.action in ["list", "retrieve"]:
            return request.user.is_authenticated
        if view.action in ["create"]:
            return (
                request.user.is_authenticated and request.user.groups.filter(name="client").exists()
            )
        return (
            request.user.is_staff
            or request.user.groups.filter(name__in=["admin", "manager"]).exists()
        )


class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [OrderPermission]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["product"]
    ordering_fields = ["created_at", "quantity"]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.groups.filter(name__in=["admin", "manager"]).exists():
            return Order.objects.all()
        return Order.objects.filter(user=user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
