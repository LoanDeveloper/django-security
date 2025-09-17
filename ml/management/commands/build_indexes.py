from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
import logging

from ml.index_manager import ProductIndexManager, RAGIndexManager
from catalog.models import Product

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Construit les index ML pour les recommandations et la recherche'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force la reconstruction des index même s\'ils existent déjà',
        )
        parser.add_argument(
            '--product-only',
            action='store_true',
            help='Construit seulement l\'index des produits',
        )
        parser.add_argument(
            '--rag-only',
            action='store_true',
            help='Construit seulement l\'index RAG',
        )

    def handle(self, *args, **options):
        force_rebuild = options['force']
        product_only = options['product_only']
        rag_only = options['rag_only']

        self.stdout.write(
            self.style.SUCCESS('Début de la construction des index ML...')
        )

        try:
            # Récupérer les produits depuis la base de données
            products = []
            for product in Product.objects.all():
                products.append({
                    'id': product.id,
                    'name': product.name,
                    'description': '',  # Pas de description dans le modèle
                    'category': product.category.name if product.category else '',
                    'price': float(product.price),
                    'is_active': product.is_active,
                    'stock_quantity': product.stock
                })

            self.stdout.write(f'Récupéré {len(products)} produits de la base de données')

            # Données FAQ
            faq_data = [
                {
                    'question': 'Comment passer une commande ?',
                    'answer': 'Pour passer une commande, ajoutez les produits à votre panier et suivez le processus de checkout. Vous pouvez modifier votre panier à tout moment avant la validation.',
                    'category': 'commande'
                },
                {
                    'question': 'Quels sont les modes de paiement acceptés ?',
                    'answer': 'Nous acceptons les cartes bancaires (Visa, Mastercard), PayPal, les virements bancaires et les paiements en plusieurs fois.',
                    'category': 'paiement'
                },
                {
                    'question': 'Quelle est la politique de retour ?',
                    'answer': 'Vous pouvez retourner les produits dans les 30 jours suivant la livraison. Les produits doivent être dans leur emballage d\'origine et en parfait état.',
                    'category': 'retour'
                },
                {
                    'question': 'Comment suivre ma commande ?',
                    'answer': 'Vous recevrez un email de confirmation avec un numéro de suivi. Vous pouvez également vous connecter à votre compte pour voir le statut de votre commande.',
                    'category': 'suivi'
                },
                {
                    'question': 'Quels sont les délais de livraison ?',
                    'answer': 'Les délais de livraison varient selon le produit et votre localisation. En général, comptez 2-5 jours ouvrés pour la France métropolitaine.',
                    'category': 'livraison'
                }
            ]

            # Données de politique
            policy_data = [
                {
                    'title': 'Politique de confidentialité',
                    'content': 'Nous respectons votre vie privée et protégeons vos données personnelles conformément au RGPD. Nous ne vendons jamais vos données à des tiers et utilisons des mesures de sécurité appropriées.',
                    'section': 'confidentialite',
                    'category': 'legal'
                },
                {
                    'title': 'Conditions générales de vente',
                    'content': 'Les présentes conditions générales régissent l\'utilisation de notre site et les ventes. En passant commande, vous acceptez ces conditions.',
                    'section': 'cgv',
                    'category': 'legal'
                },
                {
                    'title': 'Politique de cookies',
                    'content': 'Notre site utilise des cookies pour améliorer votre expérience de navigation et analyser le trafic. Vous pouvez désactiver les cookies dans les paramètres de votre navigateur.',
                    'section': 'cookies',
                    'category': 'legal'
                }
            ]

            # Construire l'index des produits
            if not rag_only:
                self.stdout.write('Construction de l\'index des produits...')
                product_manager = ProductIndexManager()
                product_version = product_manager.build_index(products, force_rebuild=force_rebuild)
                self.stdout.write(
                    self.style.SUCCESS(f'Index des produits construit: version {product_version}')
                )

            # Construire l'index RAG
            if not product_only:
                self.stdout.write('Construction de l\'index RAG...')
                rag_manager = RAGIndexManager()
                rag_version = rag_manager.build_index(
                    faq_data=faq_data,
                    policy_data=policy_data,
                    product_data=products,
                    force_rebuild=force_rebuild
                )
                self.stdout.write(
                    self.style.SUCCESS(f'Index RAG construit: version {rag_version}')
                )

            self.stdout.write(
                self.style.SUCCESS('Construction des index terminée avec succès!')
            )

        except Exception as e:
            logger.error(f'Erreur lors de la construction des index: {e}')
            raise CommandError(f'Erreur lors de la construction des index: {e}')
