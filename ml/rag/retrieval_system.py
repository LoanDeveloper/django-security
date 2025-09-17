import pickle
import re
import numpy as np
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import os
from django.conf import settings
from .document_processor import DocumentChunk


@dataclass
class RetrievalResult:
    """Résultat de recherche RAG"""
    chunk: DocumentChunk
    score: float
    explanation: str


class RAGRetrievalSystem:
    """Système de récupération pour le RAG"""
    
    def __init__(self, max_features=1000):
        self.vectorizer = TfidfVectorizer(
            max_features=max_features,
            min_df=1,
            max_df=0.8,
            ngram_range=(1, 2),
            stop_words=None
        )
        self.chunks = []
        self.chunk_vectors = None
        self.is_fitted = False
        
    def add_documents(self, chunks: List[DocumentChunk]) -> None:
        """Ajoute des documents au système de récupération"""
        self.chunks.extend(chunks)
        
        # Préprocesser les chunks
        processed_texts = []
        for chunk in chunks:
            processed_text = self._preprocess_chunk_content(chunk.content)
            processed_texts.append(processed_text)
        
        # Entraîner le vectoriseur si c'est la première fois
        if not self.is_fitted:
            self.vectorizer.fit(processed_texts)
            self.is_fitted = True
        
        # Vectoriser les nouveaux chunks
        new_vectors = self.vectorizer.transform(processed_texts).toarray()
        
        if self.chunk_vectors is None:
            self.chunk_vectors = new_vectors
        else:
            self.chunk_vectors = np.vstack([self.chunk_vectors, new_vectors])
    
    def _preprocess_chunk_content(self, content: str) -> str:
        """Préprocesse le contenu d'un chunk"""
        # Nettoyage basique
        content = content.lower()
        content = re.sub(r'[^\w\s]', ' ', content)
        content = re.sub(r'\s+', ' ', content)
        return content.strip()
    
    def search(self, query: str, top_k: int = 5, 
              min_score: float = 0.1) -> List[RetrievalResult]:
        """Recherche des chunks pertinents pour une requête"""
        if not self.is_fitted or len(self.chunks) == 0:
            return []
        
        # Préprocesser la requête
        processed_query = self._preprocess_chunk_content(query)
        
        # Vectoriser la requête
        query_vector = self.vectorizer.transform([processed_query]).toarray()
        
        # Calculer les similarités
        similarities = cosine_similarity(query_vector, self.chunk_vectors)[0]
        
        # Créer les résultats
        results = []
        for i, (chunk, similarity) in enumerate(zip(self.chunks, similarities)):
            if similarity >= min_score:
                explanation = self._generate_explanation(query, chunk, similarity)
                results.append(RetrievalResult(
                    chunk=chunk,
                    score=similarity,
                    explanation=explanation
                ))
        
        # Trier par score décroissant et retourner le top-k
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:top_k]
    
    def _generate_explanation(self, query: str, chunk: DocumentChunk, 
                            similarity: float) -> str:
        """Génère une explication pour un résultat de recherche"""
        explanations = []
        
        # Explication basée sur le type de document
        doc_type = chunk.metadata.get('type', 'unknown')
        if doc_type == 'faq':
            explanations.append("Information trouvée dans la FAQ")
        elif doc_type == 'policy':
            explanations.append("Information trouvée dans les politiques")
        elif doc_type == 'product':
            product_name = chunk.metadata.get('name', 'Produit')
            explanations.append(f"Information trouvée dans la description du produit: {product_name}")
        
        # Explication basée sur la similarité
        if similarity > 0.8:
            explanations.append("Correspondance très forte")
        elif similarity > 0.6:
            explanations.append("Correspondance forte")
        elif similarity > 0.4:
            explanations.append("Correspondance modérée")
        else:
            explanations.append("Correspondance faible")
        
        # Explication basée sur les mots-clés communs
        query_words = set(query.lower().split())
        chunk_words = set(chunk.content.lower().split())
        common_words = query_words.intersection(chunk_words)
        
        if common_words:
            explanations.append(f"Mots-clés correspondants: {', '.join(list(common_words)[:3])}")
        
        return "; ".join(explanations)
    
    def get_chunk_by_id(self, chunk_id: str) -> DocumentChunk:
        """Récupère un chunk par son ID"""
        for chunk in self.chunks:
            if chunk.id == chunk_id:
                return chunk
        return None
    
    def get_chunks_by_type(self, doc_type: str) -> List[DocumentChunk]:
        """Récupère tous les chunks d'un type donné"""
        return [chunk for chunk in self.chunks if chunk.metadata.get('type') == doc_type]
    
    def get_chunks_by_category(self, category: str) -> List[DocumentChunk]:
        """Récupère tous les chunks d'une catégorie donnée"""
        return [chunk for chunk in self.chunks if chunk.metadata.get('category') == category]
    
    def clear(self) -> None:
        """Vide le système de récupération"""
        self.chunks = []
        self.chunk_vectors = None
        self.is_fitted = False
    
    def save(self, filepath: str) -> None:
        """Sauvegarde le système de récupération"""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'wb') as f:
            pickle.dump({
                'vectorizer': self.vectorizer,
                'chunks': self.chunks,
                'chunk_vectors': self.chunk_vectors,
                'is_fitted': self.is_fitted
            }, f)
    
    @classmethod
    def load(cls, filepath: str) -> 'RAGRetrievalSystem':
        """Charge un système de récupération sauvegardé"""
        with open(filepath, 'rb') as f:
            data = pickle.load(f)
        
        instance = cls()
        instance.vectorizer = data['vectorizer']
        instance.chunks = data['chunks']
        instance.chunk_vectors = data['chunk_vectors']
        instance.is_fitted = data['is_fitted']
        
        return instance


class RAGAssistant:
    """Assistant RAG pour répondre aux questions"""
    
    def __init__(self, retrieval_system: RAGRetrievalSystem):
        self.retrieval_system = retrieval_system
        
    def ask(self, question: str, max_sources: int = 3) -> Dict[str, Any]:
        """Répond à une question en utilisant le RAG"""
        if not question.strip():
            return {
                'answer': "Je n'ai pas compris votre question. Pouvez-vous la reformuler ?",
                'sources': [],
                'confidence': 0.0,
                'trace_id': None
            }
        
        # Rechercher des chunks pertinents
        results = self.retrieval_system.search(question, top_k=max_sources, min_score=0.2)
        
        if not results:
            return {
                'answer': "Je n'ai pas trouvé d'information pertinente pour répondre à votre question. "
                         "Pouvez-vous reformuler ou essayer une question différente ?",
                'sources': [],
                'confidence': 0.0,
                'trace_id': None
            }
        
        # Générer la réponse
        answer, confidence = self._generate_answer(question, results)
        
        # Préparer les sources
        sources = []
        for result in results:
            source = {
                'chunk_id': result.chunk.id,
                'content': result.chunk.content[:200] + "..." if len(result.chunk.content) > 200 else result.chunk.content,
                'score': result.score,
                'explanation': result.explanation,
                'metadata': result.chunk.metadata
            }
            sources.append(source)
        
        return {
            'answer': answer,
            'sources': sources,
            'confidence': confidence,
            'trace_id': f"rag_{hash(question)}_{len(results)}"
        }
    
    def _generate_answer(self, question: str, results: List[RetrievalResult]) -> Tuple[str, float]:
        """Génère une réponse basée sur les résultats de recherche"""
        if not results:
            return "Je n'ai pas trouvé d'information pertinente.", 0.0
        
        # Calculer la confiance basée sur le score moyen
        confidence = sum(result.score for result in results) / len(results)
        
        # Générer la réponse basée sur le type de contenu trouvé
        answer_parts = []
        
        # Grouper par type de document
        by_type = {}
        for result in results:
            doc_type = result.chunk.metadata.get('type', 'unknown')
            if doc_type not in by_type:
                by_type[doc_type] = []
            by_type[doc_type].append(result)
        
        # Construire la réponse
        if 'faq' in by_type:
            answer_parts.append("D'après notre FAQ :")
            for result in by_type['faq']:
                answer_parts.append(f"- {result.chunk.content}")
        
        if 'policy' in by_type:
            answer_parts.append("Selon nos politiques :")
            for result in by_type['policy']:
                answer_parts.append(f"- {result.chunk.content}")
        
        if 'product' in by_type:
            answer_parts.append("Concernant nos produits :")
            for result in by_type['product']:
                product_name = result.chunk.metadata.get('name', 'Produit')
                answer_parts.append(f"- {product_name}: {result.chunk.content}")
        
        # Si pas de réponse spécifique, utiliser le contenu le plus pertinent
        if not answer_parts:
            best_result = results[0]
            answer_parts.append(f"Voici ce que j'ai trouvé : {best_result.chunk.content}")
        
        answer = "\n\n".join(answer_parts)
        
        # Limiter la longueur de la réponse
        if len(answer) > 1000:
            answer = answer[:1000] + "..."
        
        return answer, confidence
