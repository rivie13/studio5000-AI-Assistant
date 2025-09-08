#!/usr/bin/env python3
"""
Studio 5000 Instruction Vector Database

Creates and manages a vector database for semantic search of Studio 5000 instruction
documentation including syntax, parameters, examples, and usage patterns.
"""

import json
import os
import pickle
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import logging
# sentence_transformers import moved to lazy load in initialize_model()
import faiss
import time

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class InstructionSearchResult:
    """Represents a search result from instruction documentation"""
    name: str
    category: str
    description: str
    languages: List[str]
    score: float
    syntax: Optional[str] = None
    parameters: Optional[List[Dict]] = None
    examples: Optional[str] = None

class InstructionVectorDatabase:
    """Vector database for Studio 5000 instruction documentation"""
    
    def __init__(self, cache_dir: str = "instruction_vector_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        
        # Initialize sentence transformer for embeddings
        self.model = None
        self.index = None
        self.instructions_data = []
        self.embeddings = None
        
        # Cache file paths
        self.index_cache = self.cache_dir / "instruction_index.faiss"
        self.embeddings_cache = self.cache_dir / "instruction_embeddings.pkl"
        self.data_cache = self.cache_dir / "instruction_data.pkl"
    
    def initialize_model(self):
        """Initialize the sentence transformer model"""
        if self.model is None:
            logger.info("Loading sentence transformer model...")
            try:
                # Use the same model as SDK for consistency
                from sentence_transformers import SentenceTransformer
                self.model = SentenceTransformer('all-MiniLM-L6-v2')
                logger.info("Model loaded successfully")
            except Exception as e:
                logger.error(f"Failed to load sentence transformer: {e}")
                self.model = None
    
    def build_vector_database(self, instructions: Dict[str, Any], force_rebuild: bool = False):
        """Build or load the vector database from instruction data"""
        
        # Check if cached version exists and is recent
        if not force_rebuild and self._cache_exists() and self._cache_is_recent():
            logger.info("Loading cached instruction vector database...")
            self._load_from_cache()
            return
        
        # Convert instructions dict to list format
        instruction_list = []
        for name, instruction in instructions.items():
            instruction_data = {
                'name': instruction.name,
                'category': instruction.category,
                'description': instruction.description,
                'languages': instruction.languages,
                'syntax': instruction.syntax,
                'parameters': instruction.parameters,
                'examples': instruction.examples,
                'file_path': instruction.file_path
            }
            instruction_list.append(instruction_data)
        
        logger.info(f"Building vector database for {len(instruction_list)} instructions...")
        
        self.instructions_data = instruction_list
        self.initialize_model()
        
        if self.model is None:
            logger.warning("No vector model available, using text-only search")
            self._save_to_cache()
            return
        
        # Create embeddings for all instructions
        texts_to_embed = []
        for instruction in instruction_list:
            # Create comprehensive text for embedding
            text = self._create_embedding_text(instruction)
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
        logger.info("Instruction vector database built and cached successfully")
    
    def _create_embedding_text(self, instruction: Dict[str, Any]) -> str:
        """Create comprehensive text for embedding an instruction"""
        text_parts = [
            f"Instruction: {instruction.get('name', '')}",
            f"Category: {instruction.get('category', '')}",
            f"Description: {instruction.get('description', '')}",
            f"Languages: {', '.join(instruction.get('languages', []))}"
        ]
        
        # Add syntax information
        if instruction.get('syntax'):
            text_parts.append(f"Syntax: {instruction['syntax']}")
        
        # Add parameter information
        parameters = instruction.get('parameters', [])
        if parameters:
            param_text = "Parameters: " + ", ".join([
                f"{p.get('name', '')} ({p.get('type', '')}) - {p.get('description', '')}"
                for p in parameters
            ])
            text_parts.append(param_text)
        
        # Add examples
        if instruction.get('examples'):
            text_parts.append(f"Examples: {instruction['examples']}")
        
        # Join all parts with separator for clear boundaries
        return " | ".join(filter(None, text_parts))
    
    def search_instructions(self, query: str, limit: int = 20, min_score: float = 0.1) -> List[InstructionSearchResult]:
        """Search for instructions using vector similarity"""
        if not self.model or not self.index:
            logger.warning("Vector search not available, falling back to text search")
            return self._text_search(query, limit)
        
        try:
            # Create embedding for the query
            query_embedding = self.model.encode([query])
            faiss.normalize_L2(query_embedding)
            
            # Search the index
            scores, indices = self.index.search(query_embedding.astype(np.float32), limit)
            
            results = []
            for score, idx in zip(scores[0], indices[0]):
                if score >= min_score and idx < len(self.instructions_data):
                    instruction = self.instructions_data[idx]
                    
                    result = InstructionSearchResult(
                        name=instruction['name'],
                        category=instruction['category'],
                        description=instruction['description'],
                        languages=instruction['languages'],
                        score=float(score),
                        syntax=instruction.get('syntax'),
                        parameters=instruction.get('parameters'),
                        examples=instruction.get('examples')
                    )
                    results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            return self._text_search(query, limit)
    
    def _text_search(self, query: str, limit: int) -> List[InstructionSearchResult]:
        """Fallback text-based search"""
        results = []
        query_lower = query.lower()
        
        for instruction in self.instructions_data:
            match_score = 0
            
            # Name match (highest priority)
            if query_lower in instruction.get('name', '').lower():
                match_score += 10
            
            # Description match
            description = instruction.get('description', '')
            if description and query_lower in description.lower():
                match_score += 5
            
            # Category match
            category = instruction.get('category', '')
            if category and query_lower in category.lower():
                match_score += 3
            
            # Syntax match
            syntax = instruction.get('syntax', '')
            if syntax and query_lower in syntax.lower():
                match_score += 2
            
            if match_score > 0:
                result = InstructionSearchResult(
                    name=instruction['name'],
                    category=instruction['category'],
                    description=instruction['description'],
                    languages=instruction['languages'],
                    score=float(match_score) / 10.0,  # Normalize to 0-1 range
                    syntax=instruction.get('syntax'),
                    parameters=instruction.get('parameters'),
                    examples=instruction.get('examples')
                )
                results.append(result)
        
        # Sort by match score and limit results
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:limit]
    
    def get_instruction_by_name(self, name: str) -> Optional[InstructionSearchResult]:
        """Get specific instruction by exact name match"""
        name_upper = name.upper()
        
        for instruction in self.instructions_data:
            if instruction['name'].upper() == name_upper:
                return InstructionSearchResult(
                    name=instruction['name'],
                    category=instruction['category'],
                    description=instruction['description'],
                    languages=instruction['languages'],
                    score=1.0,
                    syntax=instruction.get('syntax'),
                    parameters=instruction.get('parameters'),
                    examples=instruction.get('examples')
                )
        
        return None
    
    def get_instructions_by_category(self, category: str) -> List[InstructionSearchResult]:
        """Get all instructions in a specific category"""
        results = []
        category_lower = category.lower()
        
        for instruction in self.instructions_data:
            if instruction.get('category', '').lower() == category_lower:
                result = InstructionSearchResult(
                    name=instruction['name'],
                    category=instruction['category'],
                    description=instruction['description'],
                    languages=instruction['languages'],
                    score=1.0,
                    syntax=instruction.get('syntax'),
                    parameters=instruction.get('parameters'),
                    examples=instruction.get('examples')
                )
                results.append(result)
        
        return sorted(results, key=lambda x: x.name)
    
    def get_categories(self) -> List[str]:
        """Get all unique instruction categories"""
        categories = set()
        for instruction in self.instructions_data:
            if instruction.get('category'):
                categories.add(instruction['category'])
        
        return sorted(list(categories))
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get database statistics"""
        if not self.instructions_data:
            return {'total_instructions': 0, 'has_vector_search': False}
        
        # Count by category
        by_category = {}
        by_language = {}
        
        for instruction in self.instructions_data:
            # Category stats
            category = instruction.get('category', 'Unknown')
            by_category[category] = by_category.get(category, 0) + 1
            
            # Language stats
            for lang in instruction.get('languages', []):
                by_language[lang] = by_language.get(lang, 0) + 1
        
        return {
            'total_instructions': len(self.instructions_data),
            'has_vector_search': self.model is not None and self.index is not None,
            'by_category': by_category,
            'by_language': by_language,
            'cache_dir': str(self.cache_dir),
            'model_name': 'all-MiniLM-L6-v2' if self.model else None
        }
    
    def _cache_exists(self) -> bool:
        """Check if cache files exist"""
        return (self.index_cache.exists() and 
                self.embeddings_cache.exists() and 
                self.data_cache.exists())
    
    def _cache_is_recent(self, max_age_days: int = 7) -> bool:
        """Check if cache is recent enough"""
        try:
            cache_age = time.time() - self.data_cache.stat().st_mtime
            return cache_age < (max_age_days * 24 * 3600)
        except:
            return False
    
    def _save_to_cache(self):
        """Save vector database to cache files"""
        try:
            # Save instruction data
            with open(self.data_cache, 'wb') as f:
                pickle.dump(self.instructions_data, f)
            
            if self.embeddings is not None:
                # Save embeddings
                with open(self.embeddings_cache, 'wb') as f:
                    pickle.dump(self.embeddings, f)
            
            if self.index is not None:
                # Save FAISS index
                faiss.write_index(self.index, str(self.index_cache))
            
            logger.info(f"Cached instruction vector database to {self.cache_dir}")
            
        except Exception as e:
            logger.error(f"Failed to save cache: {e}")
    
    def _load_from_cache(self):
        """Load vector database from cache files"""
        try:
            # Load instruction data
            with open(self.data_cache, 'rb') as f:
                self.instructions_data = pickle.load(f)
            
            self.initialize_model()
            
            # Load embeddings if available
            if self.embeddings_cache.exists():
                with open(self.embeddings_cache, 'rb') as f:
                    self.embeddings = pickle.load(f)
            
            # Load FAISS index if available
            if self.index_cache.exists():
                self.index = faiss.read_index(str(self.index_cache))
            
            logger.info(f"Loaded instruction vector database from cache ({len(self.instructions_data)} instructions)")
            
        except Exception as e:
            logger.error(f"Failed to load cache: {e}")
            raise


def main():
    """Test the instruction vector database"""
    # This would normally be called with real instruction data
    print("Instruction Vector Database Test")
    print("Note: This requires actual instruction data from the MCP server")
    
    # Example of how it would be used:
    # vector_db = InstructionVectorDatabase()
    # vector_db.build_vector_database(instructions, force_rebuild=True)
    
    # Test searches
    test_queries = [
        "timer delay",
        "mathematical operations", 
        "motion control",
        "counting pulses",
        "compare values",
        "safety monitoring",
        "communication",
        "array operations"
    ]
    
    print("\n🔍 Example search queries that will work:")
    for query in test_queries:
        print(f"  - '{query}'")
    
    print("\n✅ Ready for integration with MCP server")


if __name__ == "__main__":
    main()
