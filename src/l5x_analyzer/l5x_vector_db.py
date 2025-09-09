#!/usr/bin/env python3
"""
L5X Vector Database

Creates and manages a vector database for semantic search of L5X content
extracted using the Studio 5000 SDK. Handles production-scale projects by
indexing only relevant extracted sections.
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

from .l5x_chunk import L5XChunk, L5XChunkType, L5XLocation
from .sdk_powered_analyzer import SDKPoweredL5XAnalyzer

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
class L5XSearchResult:
    """Represents a search result from L5X content"""
    chunk_id: str
    chunk_type: L5XChunkType
    name: str
    description: str
    score: float
    content: str
    location: L5XLocation
    file_path: str
    insertion_hints: List[str] = None
    
    def __post_init__(self):
        if self.insertion_hints is None:
            self.insertion_hints = []

class L5XVectorDatabase:
    """Vector database for L5X content with SDK integration"""
    
    def __init__(self, cache_dir: str = "l5x_vector_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        
        # Initialize sentence transformer for embeddings
        self.model = None
        self.index = None
        self.chunks_data = []
        self.embeddings = None
        
        # SDK analyzer for content extraction
        self.sdk_analyzer = None
        
        # Cache file paths
        self.index_cache = self.cache_dir / "l5x_index.faiss"
        self.embeddings_cache = self.cache_dir / "l5x_embeddings.pkl"
        self.data_cache = self.cache_dir / "l5x_chunks.pkl"
        self.metadata_cache = self.cache_dir / "l5x_metadata.json"
        
        # Project indexing status
        self.indexed_projects = {}
    
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
    
    async def index_acd_project(self, acd_path: str, routines_to_index: List[str] = None,
                              force_rebuild: bool = False) -> bool:
        """
        Index ACD/L5K project by extracting routines via SDK
        
        Args:
            acd_path: Path to ACD or L5K file
            routines_to_index: Specific routines to index (if None, discovers all)
            force_rebuild: Force rebuild even if cached
            
        Returns:
            True if indexing successful
        """
        project_name = Path(acd_path).stem
        
        # Check if already indexed and not forcing rebuild
        if not force_rebuild and self._is_project_indexed(project_name):
            logger.info(f"Project {project_name} already indexed")
            return True
        
        try:
            # Initialize SDK analyzer if needed
            if not self.sdk_analyzer:
                self.sdk_analyzer = SDKPoweredL5XAnalyzer()
            
            # Open project
            if not await self.sdk_analyzer.open_project(acd_path):
                logger.error(f"Failed to open project: {acd_path}")
                return False
            
            # Discover project structure
            project_structure = await self.sdk_analyzer.discover_project_structure()
            
            # Determine which routines to index
            if routines_to_index is None:
                routines_to_index = [r['name'] for r in project_structure['routines']]
            
            logger.info(f"Indexing {len(routines_to_index)} routines from {project_name}")
            
            # Extract and parse each routine
            all_chunks = []
            for routine_info in project_structure['routines']:
                routine_name = routine_info['name']
                program_name = routine_info.get('program', 'MainProgram')
                
                if routine_name in routines_to_index:
                    chunks = await self._extract_and_parse_routine(
                        routine_name, program_name, acd_path
                    )
                    all_chunks.extend(chunks)
            
            # Build vector database from chunks
            self.build_vector_database(all_chunks, force_rebuild=True)
            
            # Update project indexing status
            self.indexed_projects[project_name] = {
                'path': acd_path,
                'indexed_at': time.time(),
                'routine_count': len(routines_to_index),
                'chunk_count': len(all_chunks)
            }
            self._save_metadata()
            
            logger.info(f"Successfully indexed {len(all_chunks)} chunks from {project_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to index project {acd_path}: {e}")
            return False
        finally:
            if self.sdk_analyzer:
                self.sdk_analyzer.close_project()
    
    async def _extract_and_parse_routine(self, routine_name: str, program_name: str, 
                                       acd_path: str) -> List[L5XChunk]:
        """Extract and parse a single routine into chunks"""
        try:
            # Extract routine using SDK
            l5x_path = await self.sdk_analyzer.extract_routine_for_analysis(
                routine_name, program_name
            )
            
            if not l5x_path:
                logger.warning(f"Failed to extract routine {routine_name}")
                return []
            
            # Parse extracted L5X into chunks
            chunks = self.sdk_analyzer.parse_routine_l5x(l5x_path)
            
            # Update file path in chunks
            for chunk in chunks:
                chunk.location.file_path = acd_path
            
            logger.debug(f"Extracted {len(chunks)} chunks from routine {routine_name}")
            return chunks
            
        except Exception as e:
            logger.error(f"Failed to extract/parse routine {routine_name}: {e}")
            return []
    
    def build_vector_database(self, l5x_chunks: List[L5XChunk], force_rebuild: bool = False):
        """Build or load the vector database from L5X chunks"""
        
        # Check if cached version exists and is recent
        if not force_rebuild and self._cache_exists() and self._cache_is_recent():
            logger.info("Loading cached L5X vector database...")
            self._load_from_cache()
            return
        
        logger.info(f"Building vector database for {len(l5x_chunks)} L5X chunks...")
        
        self.chunks_data = l5x_chunks
        self.initialize_model()
        
        if self.model is None or not FAISS_AVAILABLE:
            logger.warning("Vector search not available, using text-only search")
            self._save_to_cache()
            return
        
        # Create embeddings for all chunks
        texts_to_embed = []
        for chunk in l5x_chunks:
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
        logger.info("L5X vector database built and cached successfully")
    
    def search_l5x_content(self, query: str, limit: int = 20, score_threshold: float = 0.3,
                          chunk_types: List[L5XChunkType] = None) -> List[L5XSearchResult]:
        """
        Search L5X content using vector similarity
        
        Args:
            query: Search query
            limit: Maximum results to return
            score_threshold: Minimum similarity score
            chunk_types: Filter by specific chunk types
            
        Returns:
            List of search results ranked by similarity
        """
        if not self.chunks_data:
            logger.warning("No L5X content has been indexed")
            return []
        
        if not self.model or not self.index:
            logger.warning("Vector search not available, falling back to text search")
            return self._text_search(query, limit, chunk_types)
        
        try:
            # Create embedding for the query
            query_embedding = self.model.encode([query])
            faiss.normalize_L2(query_embedding)
            
            # Search the index
            scores, indices = self.index.search(query_embedding.astype(np.float32), 
                                              min(limit * 2, len(self.chunks_data)))
            
            results = []
            for score, idx in zip(scores[0], indices[0]):
                if score >= score_threshold and idx < len(self.chunks_data):
                    chunk = self.chunks_data[idx]
                    
                    # Apply chunk type filter
                    if chunk_types and chunk.chunk_type not in chunk_types:
                        continue
                    
                    result = L5XSearchResult(
                        chunk_id=chunk.id,
                        chunk_type=chunk.chunk_type,
                        name=chunk.name,
                        description=chunk.description,
                        score=float(score),
                        content=chunk.content,
                        location=chunk.location,
                        file_path=chunk.location.file_path,
                        insertion_hints=self._generate_insertion_hints(chunk)
                    )
                    results.append(result)
                    
                    if len(results) >= limit:
                        break
            
            logger.info(f"Found {len(results)} results for query: {query}")
            return results
            
        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            return self._text_search(query, limit, chunk_types)
    
    def find_optimal_insertion_point(self, query: str, routine_name: str) -> Tuple[int, float]:
        """
        Find the best rung position to insert new logic based on semantic similarity
        
        Args:
            query: Description of logic to insert
            routine_name: Target routine name
            
        Returns:
            Tuple of (rung_position, confidence_score)
        """
        # Search for similar logic patterns in the target routine
        routine_chunks = [chunk for chunk in self.chunks_data 
                         if chunk.location.parent_routine == routine_name 
                         and chunk.chunk_type == L5XChunkType.LADDER_RUNG]
        
        if not routine_chunks:
            logger.warning(f"No indexed rungs found for routine {routine_name}")
            return 0, 0.0
        
        # Find most similar rung
        search_results = self.search_l5x_content(
            f"{query} in {routine_name}",
            limit=5,
            chunk_types=[L5XChunkType.LADDER_RUNG]
        )
        
        best_position = 0
        best_confidence = 0.0
        
        for result in search_results:
            if result.location.parent_routine == routine_name:
                # Suggest inserting after the similar logic
                position = result.location.rung_number + 1 if result.location.rung_number else 0
                confidence = result.score
                
                if confidence > best_confidence:
                    best_position = position
                    best_confidence = confidence
                    break
        
        # If no similar logic found in routine, insert at end
        if best_confidence == 0.0:
            max_rung = max([chunk.location.rung_number for chunk in routine_chunks 
                          if chunk.location.rung_number is not None], default=0)
            best_position = max_rung + 1
        
        logger.info(f"Optimal insertion point for '{query}' in {routine_name}: "
                   f"rung {best_position} (confidence: {best_confidence:.3f})")
        
        return best_position, best_confidence
    
    def find_related_components(self, chunk_id: str, relationship_types: List[str] = None) -> List[L5XSearchResult]:
        """Find components related to a given chunk"""
        chunk = next((c for c in self.chunks_data if c.id == chunk_id), None)
        if not chunk:
            return []
        
        related_results = []
        
        # Find chunks that reference the same tags/UDTs
        for dependency in chunk.dependencies:
            dependency_results = self.search_l5x_content(
                f"uses {dependency}",
                limit=10,
                score_threshold=0.2
            )
            related_results.extend(dependency_results)
        
        # Remove duplicates and the original chunk
        seen_ids = {chunk_id}
        unique_results = []
        for result in related_results:
            if result.chunk_id not in seen_ids:
                unique_results.append(result)
                seen_ids.add(result.chunk_id)
        
        return unique_results[:20]  # Limit results
    
    def get_routine_analysis(self, routine_name: str) -> Dict[str, Any]:
        """Get comprehensive analysis of a routine"""
        routine_chunks = [chunk for chunk in self.chunks_data 
                         if chunk.location.parent_routine == routine_name]
        
        if not routine_chunks:
            return {'error': f'No data found for routine {routine_name}'}
        
        # Analyze rung distribution
        rung_chunks = [c for c in routine_chunks if c.chunk_type == L5XChunkType.LADDER_RUNG]
        rung_numbers = [c.location.rung_number for c in rung_chunks if c.location.rung_number is not None]
        
        # Collect all dependencies
        all_dependencies = set()
        for chunk in routine_chunks:
            all_dependencies.update(chunk.dependencies)
        
        analysis = {
            'routine_name': routine_name,
            'total_chunks': len(routine_chunks),
            'rung_count': len(rung_chunks),
            'rung_range': (min(rung_numbers), max(rung_numbers)) if rung_numbers else (0, 0),
            'dependencies': list(all_dependencies),
            'complexity_score': self._calculate_complexity_score(routine_chunks),
            'available_insertion_points': [r + 1 for r in rung_numbers] if rung_numbers else [0]
        }
        
        return analysis
    
    def _generate_insertion_hints(self, chunk: L5XChunk) -> List[str]:
        """Generate hints for where logic could be inserted relative to this chunk"""
        hints = []
        
        if chunk.chunk_type == L5XChunkType.LADDER_RUNG:
            hints.append(f"Insert after rung {chunk.location.rung_number}")
            if chunk.location.rung_number > 0:
                hints.append(f"Insert before rung {chunk.location.rung_number}")
        
        if chunk.chunk_type == L5XChunkType.ROUTINE:
            hints.append(f"Add rungs to routine {chunk.name}")
        
        # Add semantic hints based on content
        content_lower = chunk.content.lower()
        if 'start' in content_lower or 'enable' in content_lower:
            hints.append("Good location for initialization logic")
        if 'stop' in content_lower or 'disable' in content_lower:
            hints.append("Good location for shutdown logic")
        if 'alarm' in content_lower or 'fault' in content_lower:
            hints.append("Good location for safety/alarm logic")
        
        return hints
    
    def _calculate_complexity_score(self, chunks: List[L5XChunk]) -> float:
        """Calculate a complexity score for a set of chunks"""
        if not chunks:
            return 0.0
        
        total_content_length = sum(len(chunk.content) for chunk in chunks)
        total_dependencies = sum(len(chunk.dependencies) for chunk in chunks)
        rung_count = len([c for c in chunks if c.chunk_type == L5XChunkType.LADDER_RUNG])
        
        # Simple complexity calculation
        complexity = (total_content_length / 1000) + (total_dependencies * 0.5) + (rung_count * 0.1)
        return min(complexity, 10.0)  # Cap at 10
    
    def _text_search(self, query: str, limit: int, chunk_types: List[L5XChunkType] = None) -> List[L5XSearchResult]:
        """Fallback text-based search"""
        results = []
        query_lower = query.lower()
        
        for chunk in self.chunks_data:
            if chunk_types and chunk.chunk_type not in chunk_types:
                continue
            
            searchable = chunk.searchable_text.lower()
            
            # Simple text matching score
            score = 0.0
            query_words = query_lower.split()
            for word in query_words:
                if word in searchable:
                    score += 1.0 / len(query_words)
            
            if score > 0:
                result = L5XSearchResult(
                    chunk_id=chunk.id,
                    chunk_type=chunk.chunk_type,
                    name=chunk.name,
                    description=chunk.description,
                    score=score,
                    content=chunk.content,
                    location=chunk.location,
                    file_path=chunk.location.file_path,
                    insertion_hints=self._generate_insertion_hints(chunk)
                )
                results.append(result)
        
        # Sort by score and return top results
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:limit]
    
    def _is_project_indexed(self, project_name: str) -> bool:
        """Check if project is already indexed"""
        self._load_metadata()
        return project_name in self.indexed_projects
    
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
            # Save chunks data
            with open(self.data_cache, 'wb') as f:
                pickle.dump(self.chunks_data, f)
            
            if FAISS_AVAILABLE and self.index is not None:
                # Save FAISS index
                faiss.write_index(self.index, str(self.index_cache))
                
                # Save embeddings
                with open(self.embeddings_cache, 'wb') as f:
                    pickle.dump(self.embeddings, f)
            
            logger.info("Vector database cached successfully")
            
        except Exception as e:
            logger.error(f"Failed to save cache: {e}")
    
    def _load_from_cache(self):
        """Load vector database from cache files"""
        try:
            # Load chunks data
            with open(self.data_cache, 'rb') as f:
                self.chunks_data = pickle.load(f)
            
            if FAISS_AVAILABLE and self.index_cache.exists():
                # Load FAISS index
                self.index = faiss.read_index(str(self.index_cache))
                
                # Load embeddings
                if self.embeddings_cache.exists():
                    with open(self.embeddings_cache, 'rb') as f:
                        self.embeddings = pickle.load(f)
            
            # Initialize model for new searches
            self.initialize_model()
            
            logger.info(f"Loaded {len(self.chunks_data)} chunks from cache")
            
        except Exception as e:
            logger.error(f"Failed to load cache: {e}")
            self.chunks_data = []
    
    def _save_metadata(self):
        """Save project indexing metadata"""
        try:
            with open(self.metadata_cache, 'w') as f:
                json.dump(self.indexed_projects, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save metadata: {e}")
    
    def _load_metadata(self):
        """Load project indexing metadata"""
        try:
            if self.metadata_cache.exists():
                with open(self.metadata_cache, 'r') as f:
                    self.indexed_projects = json.load(f)
        except Exception as e:
            logger.error(f"Failed to load metadata: {e}")
            self.indexed_projects = {}
