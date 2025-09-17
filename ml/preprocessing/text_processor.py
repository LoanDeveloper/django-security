import re
import string
from typing import List, Dict, Any
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import SnowballStemmer
import nltk

# Télécharger les ressources NLTK nécessaires
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')


class TextProcessor:
    """Processeur de texte pour le nettoyage et la normalisation"""
    
    def __init__(self, language='french'):
        self.language = language
        self.stemmer = SnowballStemmer(language)
        self.stop_words = set(stopwords.words(language))
        
    def clean_text(self, text: str) -> str:
        """Nettoie le texte en supprimant la ponctuation et normalisant"""
        if not text:
            return ""
        
        # Convertir en minuscules
        text = text.lower()
        
        # Supprimer la ponctuation
        text = text.translate(str.maketrans('', '', string.punctuation))
        
        # Supprimer les chiffres
        text = re.sub(r'\d+', '', text)
        
        # Supprimer les espaces multiples
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    def tokenize(self, text: str) -> List[str]:
        """Tokenise le texte"""
        return word_tokenize(text, language=self.language)
    
    def remove_stopwords(self, tokens: List[str]) -> List[str]:
        """Supprime les mots vides"""
        return [token for token in tokens if token not in self.stop_words]
    
    def stem_tokens(self, tokens: List[str]) -> List[str]:
        """Applique le stemming"""
        return [self.stemmer.stem(token) for token in tokens]
    
    def process_text(self, text: str) -> str:
        """Pipeline complet de traitement du texte"""
        cleaned = self.clean_text(text)
        tokens = self.tokenize(cleaned)
        tokens = self.remove_stopwords(tokens)
        tokens = self.stem_tokens(tokens)
        return ' '.join(tokens)
    
    def extract_keywords(self, text: str, max_keywords: int = 10) -> List[str]:
        """Extrait les mots-clés les plus importants"""
        processed = self.process_text(text)
        tokens = processed.split()
        
        # Compter les fréquences
        word_freq = {}
        for token in tokens:
            if len(token) > 2:  # Ignorer les mots trop courts
                word_freq[token] = word_freq.get(token, 0) + 1
        
        # Trier par fréquence et retourner les top mots
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [word for word, freq in sorted_words[:max_keywords]]


class ProductPreprocessor:
    """Préprocesseur spécialisé pour les produits"""
    
    def __init__(self):
        self.text_processor = TextProcessor()
    
    def prepare_product_features(self, product: Dict[str, Any]) -> Dict[str, Any]:
        """Prépare les caractéristiques d'un produit pour la vectorisation"""
        features = {
            'id': product.get('id'),
            'name': product.get('name', ''),
            'description': product.get('description', ''),
            'category': product.get('category', ''),
            'price': product.get('price', 0),
            'is_active': product.get('is_active', True),
            'stock_quantity': product.get('stock_quantity', 0),
        }
        
        # Traitement du texte
        name_processed = self.text_processor.process_text(features['name'])
        desc_processed = self.text_processor.process_text(features['description'])
        category_processed = self.text_processor.process_text(features['category'])
        
        # Combiner tous les textes traités
        combined_text = f"{name_processed} {desc_processed} {category_processed}"
        
        features.update({
            'processed_text': combined_text,
            'keywords': self.text_processor.extract_keywords(combined_text),
            'text_length': len(combined_text),
        })
        
        return features
