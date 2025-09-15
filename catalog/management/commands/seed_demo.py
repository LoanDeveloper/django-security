from django.core.management.base import BaseCommand

from catalog.models import Category, Product


class Command(BaseCommand):
    help = "Insère des données de démonstration pour le catalogue"

    def handle(self, *args, **options):
        Category.objects.all().delete()
        Product.objects.all().delete()

        categories = [
            ("Smartphones", "smartphones"),
            ("Ordinateurs", "ordinateurs"),
            ("Accessoires", "accessoires"),
        ]
        cat_objs = {}
        for name, slug in categories:
            cat_objs[slug] = Category.objects.create(name=name, slug=slug)

        products = [
            ("iPhone 15", "iphone-15", "smartphones", 1199.00, 10),
            ("Galaxy S24", "galaxy-s24", "smartphones", 999.00, 15),
            ("MacBook Air", "macbook-air", "ordinateurs", 1299.00, 5),
            ("Clavier mécanique", "clavier-mecanique", "accessoires", 89.90, 50),
        ]
        for name, slug, cat_slug, price, stock in products:
            Product.objects.create(
                name=name,
                slug=slug,
                category=cat_objs[cat_slug],
                price=price,
                stock=stock,
                is_active=True,
            )

        self.stdout.write(self.style.SUCCESS("Données de démo insérées."))


