#!/usr/bin/env python3
"""
Tag Vector Database

Creates and manages a vector database for semantic search of Studio 5000 tag CSV data,
enabling intelligent search through thousands of I/O points and device mappings.
"""

import json
import os
import pickle
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import logging
import time

from .tag_chunk import TagChunk, TagChunkType, DeviceInfo

# sentence_transformers import moved to lazy load in initialize_model()
try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    logging.warning("FAISS not available - falling back to text-based search")

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class TagSearchResult:
    """Represents a search result from tag database"""
    tag_name: str
    chunk_type: TagChunkType
    description: str
    function: str
    category: str
    score: float
    device_info: DeviceInfo
    i_o_address: str
    related_tags: List[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.related_tags is None:
            self.related_tags = []
        if self.metadata is None:
            self.metadata = {}

class TagVectorDatabase:
    """Vector database for Studio 5000 tag CSV data"""
    
    def __init__(self, cache_dir: str = "tag_vector_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        
        # Initialize sentence transformer for embeddings
        self.model = None
        self.index = None
        self.tag_chunks = []
        self.embeddings = None
        
        # Cache file paths
        self.index_cache = self.cache_dir / "tag_index.faiss"
        self.embeddings_cache = self.cache_dir / "tag_embeddings.pkl"
        self.data_cache = self.cache_dir / "tag_chunks.pkl"
        self.metadata_cache = self.cache_dir / "tag_metadata.json"
        
        # Indexing status
        self.indexed_files = {}
    
    def initialize_model(self):
        """Initialize the sentence transformer model"""
        if self.model is None:
            logger.info("Loading sentence transformer model...")
            try:
                from sentence_transformers import SentenceTransformer
                self.model = SentenceTransformer('all-MiniLM-L6-v2')
                logger.info("Model loaded successfully")
            except Exception as e:
                logger.error(f"Failed to load sentence transformer: {e}")
                self.model = None
    
    def build_tag_database(self, tag_chunks: List[TagChunk], force_rebuild: bool = False):
        """Build or load the vector database from tag chunks"""
        
        # Check if cached version exists and is recent
        if not force_rebuild and self._cache_exists() and self._cache_is_recent():
            logger.info("Loading cached tag vector database...")
            self._load_from_cache()
            return
        
        logger.info(f"Building tag vector database for {len(tag_chunks)} tag chunks...")
        
        self.tag_chunks = tag_chunks
        self.initialize_model()
        
        if self.model is None or not FAISS_AVAILABLE:
            logger.warning("Vector search not available, using text-only search")
            self._save_to_cache()
            return
        
        # Create embeddings for all tag chunks
        texts_to_embed = []
        for chunk in tag_chunks:
            text = chunk.searchable_text
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
        logger.info("Tag vector database built and cached successfully")
    
    def search_tags(self, query: str, limit: int = 20, score_threshold: float = 0.3,
                   category_filter: str = None, chunk_type_filter: TagChunkType = None) -> List[TagSearchResult]:
        """
        Search tags using vector similarity
        
        Args:
            query: Search query
            limit: Maximum results to return
            score_threshold: Minimum similarity score
            category_filter: Filter by device category (VFD, Safety, etc.)
            chunk_type_filter: Filter by chunk type
            
        Returns:
            List of search results ranked by similarity
        """
        if not self.tag_chunks:
            logger.warning("No tag data has been indexed")
            return []
        
        if not self.model or not self.index:
            logger.warning("Vector search not available, falling back to text search")
            return self._text_search(query, limit, category_filter, chunk_type_filter)
        
        try:
            # Create embedding for the query
            query_embedding = self.model.encode([query])
            faiss.normalize_L2(query_embedding)
            
            # Search the index
            scores, indices = self.index.search(query_embedding.astype(np.float32), 
                                              min(limit * 2, len(self.tag_chunks)))
            
            results = []
            for score, idx in zip(scores[0], indices[0]):
                if score >= score_threshold and idx < len(self.tag_chunks):
                    chunk = self.tag_chunks[idx]
                    
                    # Apply filters
                    if category_filter and chunk.device_info.device_category.lower() != category_filter.lower():
                        continue
                    if chunk_type_filter and chunk.chunk_type != chunk_type_filter:
                        continue
                    
                    result = TagSearchResult(
                        tag_name=chunk.tag_name,
                        chunk_type=chunk.chunk_type,
                        description=chunk.description,
                        function=chunk.function,
                        category=chunk.category,
                        score=float(score),
                        device_info=chunk.device_info,
                        i_o_address=chunk.device_info.local_address or chunk.device_info.module_type,
                        related_tags=chunk.related_tags,
                        metadata=chunk.metadata
                    )
                    results.append(result)
                    
                    if len(results) >= limit:
                        break
            
            logger.info(f"Found {len(results)} tag results for query: {query}")
            return results
            
        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            return self._text_search(query, limit, category_filter, chunk_type_filter)
    
    def find_device_by_description(self, description: str, device_type: str = None) -> List[TagSearchResult]:
        """Find specific devices by description or function"""
        
        search_query = description
        if device_type:
            search_query += f" {device_type}"
        
        return self.search_tags(search_query, limit=10, score_threshold=0.2)
    
    def get_tags_by_module(self, rack: int, slot: int) -> List[TagSearchResult]:
        """Get all tags for a specific module (rack/slot)"""
        
        results = []
        for chunk in self.tag_chunks:
            if (chunk.device_info.rack == rack and 
                chunk.device_info.slot == slot):
                
                result = TagSearchResult(
                    tag_name=chunk.tag_name,
                    chunk_type=chunk.chunk_type,
                    description=chunk.description,
                    function=chunk.function,
                    category=chunk.category,
                    score=1.0,  # Perfect match for module location
                    device_info=chunk.device_info,
                    i_o_address=chunk.device_info.local_address or chunk.device_info.module_type,
                    related_tags=chunk.related_tags,
                    metadata=chunk.metadata
                )
                results.append(result)
        
        return sorted(results, key=lambda x: x.tag_name)
    
    def find_i_o_point(self, address_pattern: str = None, description: str = None) -> List[TagSearchResult]:
        """Find specific I/O points by address pattern or description"""
        
        if description:
            return self.search_tags(description, limit=10)
        
        if address_pattern:
            results = []
            for chunk in self.tag_chunks:
                if (address_pattern.lower() in chunk.device_info.local_address.lower() or
                    address_pattern.lower() in chunk.tag_name.lower()):
                    
                    result = TagSearchResult(
                        tag_name=chunk.tag_name,
                        chunk_type=chunk.chunk_type,
                        description=chunk.description,
                        function=chunk.function,
                        category=chunk.category,
                        score=1.0,
                        device_info=chunk.device_info,
                        i_o_address=chunk.device_info.local_address or chunk.device_info.module_type,
                        related_tags=chunk.related_tags,
                        metadata=chunk.metadata
                    )
                    results.append(result)
            
            return results
        
        return []
    
    def find_related_tags(self, tag_name: str, relationship_type: str = "all") -> List[TagSearchResult]:
        """Find tags related to a given tag"""
        
        # Find the target tag
        target_chunk = None
        for chunk in self.tag_chunks:
            if chunk.tag_name == tag_name:
                target_chunk = chunk
                break
        
        if not target_chunk:
            return []
        
        results = []
        
        # Get explicitly related tags
        for related_tag_name in target_chunk.related_tags:
            for chunk in self.tag_chunks:
                if chunk.tag_name == related_tag_name:
                    result = TagSearchResult(
                        tag_name=chunk.tag_name,
                        chunk_type=chunk.chunk_type,
                        description=chunk.description,
                        function=chunk.function,
                        category=chunk.category,
                        score=0.9,  # High score for explicit relationships
                        device_info=chunk.device_info,
                        i_o_address=chunk.device_info.local_address or chunk.device_info.module_type,
                        related_tags=chunk.related_tags,
                        metadata=chunk.metadata
                    )
                    results.append(result)
                    break
        
        # Also search for similar function/description
        if relationship_type == "all" or relationship_type == "functional":
            functional_results = self.search_tags(
                f"{target_chunk.function} {target_chunk.description}",
                limit=5,
                score_threshold=0.4
            )
            
            # Add functional relationships with lower score
            for result in functional_results:
                if result.tag_name != tag_name:
                    result.score = result.score * 0.8  # Reduce score for functional relationships
                    results.append(result)
        
        # Remove duplicates and sort by score
        seen_tags = set()
        unique_results = []
        for result in sorted(results, key=lambda x: x.score, reverse=True):
            if result.tag_name not in seen_tags:
                unique_results.append(result)
                seen_tags.add(result.tag_name)
        
        return unique_results[:15]  # Limit results
    
    def analyze_i_o_usage(self) -> Dict[str, Any]:
        """Analyze I/O usage and capacity across the system"""
        
        analysis = {
            'total_tags': len(self.tag_chunks),
            'by_device_category': {},
            'by_chunk_type': {},
            'by_module': {},
            'safety_analysis': {},
            'motor_analysis': {},
            'sensor_analysis': {},
            'module_utilization': []
        }
        
        module_usage = {}
        safety_tags = []
        motor_tags = []
        sensor_tags = []
        
        for chunk in self.tag_chunks:
            # Device category analysis
            category = chunk.device_info.device_category
            if category:
                analysis['by_device_category'][category] = (
                    analysis['by_device_category'].get(category, 0) + 1
                )
            
            # Chunk type analysis
            chunk_type = chunk.chunk_type.value
            analysis['by_chunk_type'][chunk_type] = (
                analysis['by_chunk_type'].get(chunk_type, 0) + 1
            )
            
            # Module analysis
            if chunk.device_info.rack is not None and chunk.device_info.slot is not None:
                module_key = f"Rack{chunk.device_info.rack}_Slot{chunk.device_info.slot}"
                if module_key not in module_usage:
                    module_usage[module_key] = {
                        'count': 0,
                        'module_type': chunk.device_info.module_type,
                        'device_category': chunk.device_info.device_category,
                        'rack': chunk.device_info.rack,
                        'slot': chunk.device_info.slot
                    }
                module_usage[module_key]['count'] += 1
            
            # Collect special categories
            if chunk.is_safety_tag:
                safety_tags.append(chunk)
            if chunk.is_motor_control:
                motor_tags.append(chunk)
            if chunk.is_sensor:
                sensor_tags.append(chunk)
        
        analysis['by_module'] = module_usage
        
        # Safety analysis
        analysis['safety_analysis'] = {
            'total_safety_tags': len(safety_tags),
            'safety_types': {},
            'safety_locations': {}
        }
        
        for chunk in safety_tags:
            safety_func = chunk.function
            analysis['safety_analysis']['safety_types'][safety_func] = (
                analysis['safety_analysis']['safety_types'].get(safety_func, 0) + 1
            )
        
        # Motor analysis
        analysis['motor_analysis'] = {
            'total_motor_tags': len(motor_tags),
            'motor_types': {},
            'vfd_count': 0
        }
        
        for chunk in motor_tags:
            if 'vfd' in chunk.device_info.module_type.lower():
                analysis['motor_analysis']['vfd_count'] += 1
        
        # Sensor analysis  
        analysis['sensor_analysis'] = {
            'total_sensor_tags': len(sensor_tags),
            'sensor_types': {}
        }
        
        for chunk in sensor_tags:
            sensor_func = chunk.function
            analysis['sensor_analysis']['sensor_types'][sensor_func] = (
                analysis['sensor_analysis']['sensor_types'].get(sensor_func, 0) + 1
            )
        
        # Module utilization summary
        analysis['module_utilization'] = [
            {
                'module': module_key,
                'rack': info['rack'],
                'slot': info['slot'],
                'type': info['module_type'],
                'category': info['device_category'],
                'tag_count': info['count']
            }
            for module_key, info in module_usage.items()
        ]
        
        return analysis
    
    def get_device_overview(self, category_filter: str = None) -> Dict[str, Any]:
        """Get comprehensive overview of devices in the system"""
        
        overview = {
            'total_devices': 0,
            'by_category': {},
            'by_function': {},
            'by_location': {},
            'recent_analysis': self.analyze_i_o_usage()
        }
        
        # Count unique devices (not individual I/O points)
        unique_devices = set()
        
        for chunk in self.tag_chunks:
            if category_filter and chunk.device_info.device_category.lower() != category_filter.lower():
                continue
            
            # Create device identifier
            device_id = f"{chunk.device_info.module_type}_{chunk.device_info.rack}_{chunk.device_info.slot}"
            unique_devices.add(device_id)
            
            # Function analysis
            function = chunk.function
            overview['by_function'][function] = overview['by_function'].get(function, 0) + 1
            
            # Location analysis
            if chunk.device_info.rack is not None:
                location = f"Rack {chunk.device_info.rack}"
                overview['by_location'][location] = overview['by_location'].get(location, 0) + 1
        
        overview['total_devices'] = len(unique_devices)
        
        return overview
    
    def _text_search(self, query: str, limit: int, category_filter: str = None, 
                    chunk_type_filter: TagChunkType = None) -> List[TagSearchResult]:
        """Fallback text-based search"""
        
        results = []
        query_lower = query.lower()
        
        for chunk in self.tag_chunks:
            # Apply filters
            if category_filter and chunk.device_info.device_category.lower() != category_filter.lower():
                continue
            if chunk_type_filter and chunk.chunk_type != chunk_type_filter:
                continue
            
            searchable = chunk.searchable_text.lower()
            
            # Simple text matching score
            score = 0.0
            query_words = query_lower.split()
            for word in query_words:
                if word in searchable:
                    score += 1.0 / len(query_words)
            
            if score > 0:
                result = TagSearchResult(
                    tag_name=chunk.tag_name,
                    chunk_type=chunk.chunk_type,
                    description=chunk.description,
                    function=chunk.function,
                    category=chunk.category,
                    score=score,
                    device_info=chunk.device_info,
                    i_o_address=chunk.device_info.local_address or chunk.device_info.module_type,
                    related_tags=chunk.related_tags,
                    metadata=chunk.metadata
                )
                results.append(result)
        
        # Sort by score and return top results
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:limit]
    
    def _cache_exists(self) -> bool:
        """Check if cache files exist"""
        return (self.data_cache.exists() and 
                (not FAISS_AVAILABLE or self.index_cache.exists()))
    
    def _cache_is_recent(self, max_age_hours: int = 24) -> bool:
        """Check if cache is recent enough"""
        if not self.data_cache.exists():
            return False
        
        cache_age = time.time() - self.data_cache.stat().st_mtime
        return cache_age < (max_age_hours * 3600)
    
    def _save_to_cache(self):
        """Save vector database to cache files"""
        try:
            # Save tag chunks
            with open(self.data_cache, 'wb') as f:
                pickle.dump(self.tag_chunks, f)
            
            if FAISS_AVAILABLE and self.index is not None:
                # Save FAISS index
                faiss.write_index(self.index, str(self.index_cache))
                
                # Save embeddings
                with open(self.embeddings_cache, 'wb') as f:
                    pickle.dump(self.embeddings, f)
            
            logger.info("Tag vector database cached successfully")
            
        except Exception as e:
            logger.error(f"Failed to save cache: {e}")
    
    def _load_from_cache(self):
        """Load vector database from cache files"""
        try:
            # Load tag chunks
            with open(self.data_cache, 'rb') as f:
                self.tag_chunks = pickle.load(f)
            
            if FAISS_AVAILABLE and self.index_cache.exists():
                # Load FAISS index
                self.index = faiss.read_index(str(self.index_cache))
                
                # Load embeddings
                if self.embeddings_cache.exists():
                    with open(self.embeddings_cache, 'rb') as f:
                        self.embeddings = pickle.load(f)
            
            # Initialize model for new searches
            self.initialize_model()
            
            logger.info(f"Loaded {len(self.tag_chunks)} tag chunks from cache")
            
        except Exception as e:
            logger.error(f"Failed to load cache: {e}")
            self.tag_chunks = []
