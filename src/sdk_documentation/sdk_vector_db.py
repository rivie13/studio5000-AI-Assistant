#!/usr/bin/env python3
"""
Studio 5000 SDK Vector Database

Creates and manages a vector database for semantic search of SDK documentation,
methods, classes, enums, and examples.
"""

import json
import os
import pickle
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import logging
from sentence_transformers import SentenceTransformer
import faiss
import time

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class SDKSearchResult:
    """Represents a search result from SDK documentation"""
    name: str
    type: str  # method, class, enum, example
    description: str
    category: str
    score: float
    details: Dict[str, Any]
    
class SDKVectorDatabase:
    """Vector database for Studio 5000 SDK documentation"""
    
    def __init__(self, cache_dir: str = "sdk_vector_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        
        # Initialize sentence transformer for embeddings
        self.model = None
        self.index = None
        self.operations_data = []
        self.embeddings = None
        
        # Cache file paths
        self.index_cache = self.cache_dir / "sdk_index.faiss"
        self.embeddings_cache = self.cache_dir / "sdk_embeddings.pkl"
        self.data_cache = self.cache_dir / "sdk_operations.pkl"
        
    def initialize_model(self):
        """Initialize the sentence transformer model"""
        if self.model is None:
            logger.info("Loading sentence transformer model...")
            try:
                # Use a model optimized for semantic search
                self.model = SentenceTransformer('all-MiniLM-L6-v2')
                logger.info("Model loaded successfully")
            except Exception as e:
                logger.error(f"Failed to load sentence transformer: {e}")
                logger.info("Falling back to simple text matching")
                self.model = None
    
    def build_vector_database(self, sdk_operations: List[Dict[str, Any]], force_rebuild: bool = False):
        """Build or load the vector database from SDK operations"""
        
        # Check if cached version exists and is recent
        if not force_rebuild and self._cache_exists() and self._cache_is_recent():
            logger.info("Loading cached vector database...")
            self._load_from_cache()
            return
        
        logger.info(f"Building vector database for {len(sdk_operations)} SDK operations...")
        
        self.operations_data = sdk_operations
        self.initialize_model()
        
        if self.model is None:
            logger.warning("No vector model available, using text-only search")
            self._save_to_cache()
            return
        
        # Create embeddings for all operations
        texts_to_embed = []
        for op in sdk_operations:
            # Create comprehensive text for embedding
            text = self._create_embedding_text(op)
            texts_to_embed.append(text)
        
        logger.info("Creating embeddings...")
        start_time = time.time()
        self.embeddings = self.model.encode(texts_to_embed, show_progress_bar=True)
        embedding_time = time.time() - start_time
        logger.info(f"Created {len(self.embeddings)} embeddings in {embedding_time:.2f} seconds")
        
        # Build FAISS index for fast similarity search
        logger.info("Building FAISS index...")
        dimension = self.embeddings.shape[1]
        self.index = faiss.IndexFlatIP(dimension)  # Inner product for cosine similarity
        
        # Normalize embeddings for cosine similarity
        faiss.normalize_L2(self.embeddings)
        self.index.add(self.embeddings.astype(np.float32))
        
        # Save to cache
        self._save_to_cache()
        logger.info("Vector database built and cached successfully")
    
    def _create_embedding_text(self, operation: Dict[str, Any]) -> str:
        """Create comprehensive text for embedding an operation"""
        op_type = operation.get('type', '')
        
        if op_type == 'method':
            text_parts = [
                f"SDK method: {operation.get('name', '')}",
                f"class: {operation.get('class_name', '')}",
                f"description: {operation.get('description', '')}",
                f"category: {operation.get('category', '')}",
                f"signature: {operation.get('signature', '')}",
                f"async: {'yes' if operation.get('is_async') else 'no'}",
            ]
            
            # Add parameter information
            params = operation.get('parameters', [])
            if params:
                param_text = "parameters: " + ", ".join([f"{p.get('name')} ({p.get('type')})" for p in params])
                text_parts.append(param_text)
                
        elif op_type == 'class':
            text_parts = [
                f"SDK class: {operation.get('name', '')}",
                f"description: {operation.get('description', '')}",
                f"category: {operation.get('category', '')}",
                f"namespace: {operation.get('namespace', '')}",
            ]
            
            # Add method names
            methods = operation.get('methods', [])
            if methods:
                text_parts.append(f"methods: {', '.join(methods[:10])}")  # Limit to first 10
                
        elif op_type == 'enum':
            text_parts = [
                f"SDK enumeration: {operation.get('name', '')}",
                f"description: {operation.get('description', '')}",
                f"category: {operation.get('category', '')}",
            ]
            
            # Add enum values
            values = operation.get('values', [])
            if values:
                value_names = [v.get('name', '') for v in values if v.get('name')]
                text_parts.append(f"values: {', '.join(value_names[:10])}")
                
        elif op_type == 'example':
            text_parts = [
                f"SDK example: {operation.get('title', '')}",
                f"description: {operation.get('description', '')}",
                f"category: {operation.get('category', '')}",
            ]
            
            # Add related methods
            related = operation.get('related_methods', [])
            if related:
                text_parts.append(f"related methods: {', '.join(related)}")
            
            # Add code snippet (truncated)
            code = operation.get('code', '')
            if code and len(code) > 50:
                text_parts.append(f"code: {code[:200]}")
        
        else:
            # Generic operation
            text_parts = [
                f"SDK {op_type}: {operation.get('name', operation.get('title', ''))}",
                f"description: {operation.get('description', '')}",
                f"category: {operation.get('category', '')}",
            ]
        
        return " | ".join([part for part in text_parts if part])
    
    def search_sdk_operations(self, query: str, limit: int = 20, score_threshold: float = 0.3) -> List[SDKSearchResult]:
        """Search SDK operations using vector similarity"""
        if not self.operations_data:
            logger.warning("No SDK operations data available")
            return []
        
        if self.model is None or self.index is None:
            # Fallback to text-based search
            return self._text_based_search(query, limit)
        
        # Create embedding for query
        query_embedding = self.model.encode([query])
        faiss.normalize_L2(query_embedding)
        
        # Search using FAISS
        scores, indices = self.index.search(query_embedding.astype(np.float32), min(limit * 2, len(self.operations_data)))
        
        # Convert to results
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if score >= score_threshold:
                operation = self.operations_data[idx]
                result = SDKSearchResult(
                    name=operation.get('name', operation.get('title', '')),
                    type=operation.get('type', ''),
                    description=operation.get('description', ''),
                    category=operation.get('category', ''),
                    score=float(score),
                    details=operation
                )
                results.append(result)
        
        # Sort by score and return top results
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:limit]
    
    def _text_based_search(self, query: str, limit: int) -> List[SDKSearchResult]:
        """Fallback text-based search when vector search is not available"""
        query_lower = query.lower()
        results = []
        
        for operation in self.operations_data:
            score = 0.0
            searchable_text = operation.get('searchable_text', '').lower()
            
            # Simple scoring based on text matches
            if query_lower in searchable_text:
                # Exact match gets high score
                if query_lower in operation.get('name', '').lower():
                    score = 0.9
                elif query_lower in operation.get('description', '').lower():
                    score = 0.7
                elif query_lower in operation.get('category', '').lower():
                    score = 0.6
                else:
                    score = 0.4
                
                # Bonus for multiple word matches
                query_words = query_lower.split()
                word_matches = sum(1 for word in query_words if word in searchable_text)
                score += (word_matches / len(query_words)) * 0.2
                
                if score > 0.3:  # Threshold
                    result = SDKSearchResult(
                        name=operation.get('name', operation.get('title', '')),
                        type=operation.get('type', ''),
                        description=operation.get('description', ''),
                        category=operation.get('category', ''),
                        score=score,
                        details=operation
                    )
                    results.append(result)
        
        # Sort by score and return top results
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:limit]
    
    def get_operation_by_name(self, name: str, op_type: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get a specific operation by name"""
        for operation in self.operations_data:
            if operation.get('name') == name or operation.get('title') == name:
                if op_type is None or operation.get('type') == op_type:
                    return operation
        return None
    
    def get_operations_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Get all operations in a specific category"""
        return [op for op in self.operations_data if op.get('category', '').lower() == category.lower()]
    
    def get_methods_by_class(self, class_name: str) -> List[Dict[str, Any]]:
        """Get all methods for a specific class"""
        return [op for op in self.operations_data 
                if op.get('type') == 'method' and op.get('class_name') == class_name]
    
    def get_all_categories(self) -> List[str]:
        """Get all unique categories"""
        categories = set()
        for operation in self.operations_data:
            cat = operation.get('category')
            if cat:
                categories.add(cat)
        return sorted(list(categories))
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about the SDK documentation"""
        stats = {
            'total_operations': len(self.operations_data),
            'by_type': {},
            'by_category': {},
            'has_vector_search': self.model is not None and self.index is not None
        }
        
        for operation in self.operations_data:
            op_type = operation.get('type', 'unknown')
            category = operation.get('category', 'unknown')
            
            stats['by_type'][op_type] = stats['by_type'].get(op_type, 0) + 1
            stats['by_category'][category] = stats['by_category'].get(category, 0) + 1
        
        return stats
    
    def _cache_exists(self) -> bool:
        """Check if cache files exist"""
        return (self.data_cache.exists() and 
                (not self.model or (self.index_cache.exists() and self.embeddings_cache.exists())))
    
    def _cache_is_recent(self, max_age_hours: int = 24) -> bool:
        """Check if cache is recent enough"""
        try:
            cache_time = self.data_cache.stat().st_mtime
            age_hours = (time.time() - cache_time) / 3600
            return age_hours < max_age_hours
        except:
            return False
    
    def _save_to_cache(self):
        """Save vector database to cache files"""
        try:
            # Save operations data
            with open(self.data_cache, 'wb') as f:
                pickle.dump(self.operations_data, f)
            
            if self.model is not None:
                # Save FAISS index
                if self.index is not None:
                    faiss.write_index(self.index, str(self.index_cache))
                
                # Save embeddings
                if self.embeddings is not None:
                    with open(self.embeddings_cache, 'wb') as f:
                        pickle.dump(self.embeddings, f)
            
            logger.info("Vector database cached successfully")
        except Exception as e:
            logger.error(f"Failed to save cache: {e}")
    
    def _load_from_cache(self):
        """Load vector database from cache files"""
        try:
            # Load operations data
            with open(self.data_cache, 'rb') as f:
                self.operations_data = pickle.load(f)
            
            # Initialize model if we have vector cache
            if self.index_cache.exists() and self.embeddings_cache.exists():
                self.initialize_model()
                
                if self.model is not None:
                    # Load FAISS index
                    self.index = faiss.read_index(str(self.index_cache))
                    
                    # Load embeddings
                    with open(self.embeddings_cache, 'rb') as f:
                        self.embeddings = pickle.load(f)
            
            logger.info(f"Loaded {len(self.operations_data)} operations from cache")
        except Exception as e:
            logger.error(f"Failed to load cache: {e}")
            raise


def main():
    """Test the SDK vector database"""
    from sdk_doc_parser import SDKDocumentationParser
    
    # Parse documentation
    doc_root = r"C:\Users\Public\Documents\Studio 5000\Logix Designer SDK\python\Documentation"
    parser = SDKDocumentationParser(doc_root)
    parsed_data = parser.parse_all_documentation()
    operations = parser.get_all_sdk_operations()
    
    # Build vector database
    vector_db = SDKVectorDatabase()
    vector_db.build_vector_database(operations, force_rebuild=True)
    
    # Test searches
    test_queries = [
        "create new project",
        "tag values",
        "download to controller",
        "communication path",
        "import L5X",
        "controller mode",
        "async operations",
        "LogixProject methods"
    ]
    
    print("\n🔍 Testing SDK Vector Search:")
    print("=" * 50)
    
    for query in test_queries:
        print(f"\nQuery: '{query}'")
        results = vector_db.search_sdk_operations(query, limit=5)
        
        if results:
            for i, result in enumerate(results):
                print(f"  {i+1}. {result.name} ({result.type}) - Score: {result.score:.3f}")
                print(f"     Category: {result.category}")
                print(f"     Description: {result.description[:100]}...")
        else:
            print("  No results found")
    
    # Display statistics
    stats = vector_db.get_statistics()
    print(f"\n📊 Database Statistics:")
    print(f"  Total operations: {stats['total_operations']}")
    print(f"  Vector search enabled: {stats['has_vector_search']}")
    print(f"  By type: {stats['by_type']}")
    print(f"  Categories: {len(stats['by_category'])}")


if __name__ == "__main__":
    main()
