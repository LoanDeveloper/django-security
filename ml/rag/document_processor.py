import re
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass
from .text_processor import TextProcessor


@dataclass
class DocumentChunk:
    """Représente un chunk de document"""
    id: str
    content: str
    metadata: Dict[str, Any]
    embedding: List[float] = None


class DocumentProcessor:
    """Processeur de documents pour le RAG"""
    
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.text_processor = TextProcessor()
    
    def chunk_text(self, text: str, metadata: Dict[str, Any] = None) -> List[DocumentChunk]:
        """Découpe un texte en chunks avec overlap"""
        if not text:
            return []
        
        # Nettoyer le texte
        cleaned_text = self.text_processor.clean_text(text)
        
        # Découper en phrases
        sentences = re.split(r'[.!?]+', cleaned_text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        chunks = []
        current_chunk = ""
        chunk_id = 0
        
        for sentence in sentences:
            # Si ajouter cette phrase dépasse la taille max
            if len(current_chunk) + len(sentence) > self.chunk_size and current_chunk:
                # Sauvegarder le chunk actuel
                chunks.append(DocumentChunk(
                    id=f"{metadata.get('source_id', 'doc')}_{chunk_id}",
                    content=current_chunk.strip(),
                    metadata=metadata or {}
                ))
                chunk_id += 1
                
                # Commencer un nouveau chunk avec overlap
                overlap_text = self._get_overlap_text(current_chunk)
                current_chunk = overlap_text + " " + sentence
            else:
                if current_chunk:
                    current_chunk += ". " + sentence
                else:
                    current_chunk = sentence
        
        # Ajouter le dernier chunk s'il n'est pas vide
        if current_chunk.strip():
            chunks.append(DocumentChunk(
                id=f"{metadata.get('source_id', 'doc')}_{chunk_id}",
                content=current_chunk.strip(),
                metadata=metadata or {}
            ))
        
        return chunks
    
    def _get_overlap_text(self, text: str) -> str:
        """Récupère le texte de fin pour l'overlap"""
        words = text.split()
        if len(words) <= self.chunk_overlap:
            return text
        
        return " ".join(words[-self.chunk_overlap:])
    
    def process_faq_documents(self, faq_data: List[Dict[str, Any]]) -> List[DocumentChunk]:
        """Traite les documents FAQ"""
        chunks = []
        
        for i, faq in enumerate(faq_data):
            # Combiner question et réponse
            content = f"Question: {faq.get('question', '')}\nRéponse: {faq.get('answer', '')}"
            
            metadata = {
                'source_id': f"faq_{i}",
                'type': 'faq',
                'question': faq.get('question', ''),
                'category': faq.get('category', 'general')
            }
            
            chunks.extend(self.chunk_text(content, metadata))
        
        return chunks
    
    def process_policy_documents(self, policy_data: List[Dict[str, Any]]) -> List[DocumentChunk]:
        """Traite les documents de politique"""
        chunks = []
        
        for i, policy in enumerate(policy_data):
            content = policy.get('content', '')
            metadata = {
                'source_id': f"policy_{i}",
                'type': 'policy',
                'title': policy.get('title', ''),
                'section': policy.get('section', ''),
                'category': policy.get('category', 'general')
            }
            
            chunks.extend(self.chunk_text(content, metadata))
        
        return chunks
    
    def process_product_descriptions(self, products: List[Dict[str, Any]]) -> List[DocumentChunk]:
        """Traite les descriptions de produits"""
        chunks = []
        
        for product in products:
            if not product.get('is_active', True):
                continue
            
            # Combiner nom, description et caractéristiques
            content_parts = []
            
            if product.get('name'):
                content_parts.append(f"Produit: {product['name']}")
            
            if product.get('description'):
                content_parts.append(f"Description: {product['description']}")
            
            if product.get('category'):
                content_parts.append(f"Catégorie: {product['category']}")
            
            if product.get('price'):
                content_parts.append(f"Prix: {product['price']}€")
            
            content = "\n".join(content_parts)
            
            metadata = {
                'source_id': f"product_{product['id']}",
                'type': 'product',
                'product_id': product['id'],
                'name': product.get('name', ''),
                'category': product.get('category', ''),
                'price': product.get('price', 0)
            }
            
            chunks.extend(self.chunk_text(content, metadata))
        
        return chunks
    
    def preprocess_chunk(self, chunk: DocumentChunk) -> DocumentChunk:
        """Préprocesse un chunk pour l'indexation"""
        processed_content = self.text_processor.process_text(chunk.content)
        
        return DocumentChunk(
            id=chunk.id,
            content=processed_content,
            metadata=chunk.metadata,
            embedding=chunk.embedding
        )
    
    def extract_keywords(self, chunk: DocumentChunk) -> List[str]:
        """Extrait les mots-clés d'un chunk"""
        return self.text_processor.extract_keywords(chunk.content)
    
    def compute_chunk_similarity(self, chunk1: DocumentChunk, chunk2: DocumentChunk) -> float:
        """Calcule la similarité entre deux chunks"""
        return self.text_processor._text_similarity(chunk1.content, chunk2.content)
