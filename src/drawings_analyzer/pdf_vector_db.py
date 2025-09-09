#!/usr/bin/env python3
"""
PDF Technical Drawings Vector Database

Creates and manages a vector database for semantic search of PDF drawing content.
Follows the exact same patterns as L5XVectorDatabase, SDKVectorDatabase, and TagVectorDatabase.

Handles production-scale technical drawings with intelligent content processing.
"""

import json
import os
import pickle
import numpy as np
import time
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import logging

from .pdf_chunk import PDFChunk, PDFChunkType, PDFLocation
from .pdf_parser import PDFParser

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
class PDFSearchResult:
    """Represents a search result from PDF drawing content"""
    chunk_id: str
    chunk_type: PDFChunkType
    page_number: int
    drawing_number: Optional[str]
    title: Optional[str]
    description: str
    score: float
    content: str
    equipment_tags: List[str]
    location: PDFLocation
    file_path: str
    
    def __post_init__(self):
        if self.equipment_tags is None:
            self.equipment_tags = []

class PDFVectorDatabase:
    """Vector database for PDF technical drawings with intelligent search"""
    
    def __init__(self, cache_dir: str = "pdf_drawings_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        
        # Initialize sentence transformer for embeddings (same as other DBs)
        self.model = None
        self.index = None
        self.chunks_data = []
        self.embeddings = None
        
        # PDF parser for content extraction with optimized configuration
        from .pdf_parser import OptimizedProcessingConfig
        config = OptimizedProcessingConfig(
            max_workers=4,
            batch_size=10,
            memory_cleanup_interval=20,
            progress_report_interval=5,
            use_optimized_mode=True  # Enable by default for vector database
        )
        self.pdf_parser = PDFParser(config)
        
        # Cache file paths (following existing pattern)
        self.index_cache = self.cache_dir / "pdf_index.faiss"
        self.embeddings_cache = self.cache_dir / "pdf_embeddings.pkl"
        self.data_cache = self.cache_dir / "pdf_chunks.pkl"
        self.metadata_cache = self.cache_dir / "pdf_metadata.json"
        
        # Indexed files tracking
        self.indexed_files = {}
    
    def initialize_model(self):
        """Initialize the sentence transformer model (same as other DBs)"""
        if self.model is None:
            logger.info("Loading sentence transformer model...")
            try:
                from sentence_transformers import SentenceTransformer
                self.model = SentenceTransformer('all-MiniLM-L6-v2')
                logger.info("Model loaded successfully")
            except Exception as e:
                logger.error(f"Failed to load sentence transformer: {e}")
                self.model = None
    
    def index_pdf_file(self, pdf_file_path: str, force_rebuild: bool = False,
                      use_vision_ai: bool = False, max_pages: Optional[int] = None) -> bool:
        """
        Index a PDF technical drawings file for semantic search
        
        Args:
            pdf_file_path: Path to PDF file
            force_rebuild: Force re-indexing even if cached
            use_vision_ai: Enable vision AI analysis (future enhancement)
            max_pages: Limit processing to first N pages (for testing)
            
        Returns:
            True if indexing successful
        """
        if not os.path.exists(pdf_file_path):
            logger.error(f"PDF file not found: {pdf_file_path}")
            return False
        
        # Check if already indexed and current
        file_key = os.path.abspath(pdf_file_path)
        file_mtime = os.path.getmtime(pdf_file_path)
        
        if not force_rebuild and self._is_file_current(file_key, file_mtime):
            logger.info(f"PDF file already indexed: {os.path.basename(pdf_file_path)}")
            return True
        
        logger.info(f"🔍 Indexing PDF file: {os.path.basename(pdf_file_path)}")
        start_time = time.time()
        
        try:
            # Parse PDF into chunks
            chunks, stats = self.pdf_parser.parse_pdf_file(
                pdf_file_path, max_pages=max_pages, sample_complex_pages=True
            )
            
            if not chunks:
                logger.warning("No chunks extracted from PDF file")
                return False
            
            # Add file path to chunks
            for chunk in chunks:
                chunk.metadata['source_file'] = pdf_file_path
            
            # Add chunks to existing data
            self.chunks_data.extend(chunks)
            
            # Update indexed files tracking
            self.indexed_files[file_key] = {
                'mtime': file_mtime,
                'chunks_count': len(chunks),
                'processing_time': stats.processing_time
            }
            
            # Rebuild vector database with all chunks
            self.build_vector_database(self.chunks_data, force_rebuild=True)
            
            indexing_time = time.time() - start_time
            logger.info(f"✅ PDF indexing completed in {indexing_time:.1f} seconds")
            logger.info(f"   📊 Added {len(chunks)} chunks from {stats.pages_processed} pages")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to index PDF file: {e}")
            return False
    
    def build_vector_database(self, pdf_chunks: List[PDFChunk], force_rebuild: bool = False):
        """Build or load the vector database from PDF chunks (same pattern as other DBs)"""
        
        # Check if cached version exists and is recent
        if not force_rebuild and self._cache_exists() and self._cache_is_recent():
            logger.info("Loading cached PDF vector database...")
            self._load_from_cache()
            return
        
        logger.info(f"Building vector database for {len(pdf_chunks)} PDF chunks...")
        
        self.chunks_data = pdf_chunks
        self.initialize_model()
        
        if self.model is None or not FAISS_AVAILABLE:
            logger.warning("Vector search not available, using text-only search")
            self._save_to_cache()
            return
        
        # Create embeddings for all chunks
        texts_to_embed = []
        for chunk in pdf_chunks:
            text = chunk.searchable_text
            texts_to_embed.append(text)
        
        logger.info("Creating embeddings...")
        start_time = time.time()
        self.embeddings = self.model.encode(texts_to_embed, show_progress_bar=True)
        embedding_time = time.time() - start_time
        logger.info(f"Created {len(self.embeddings)} embeddings in {embedding_time:.2f} seconds")
        
        # Build FAISS index for fast similarity search (same as other DBs)
        logger.info("Building FAISS index...")
        dimension = self.embeddings.shape[1]
        self.index = faiss.IndexFlatIP(dimension)  # Inner product for cosine similarity
        
        # Normalize embeddings for cosine similarity
        faiss.normalize_L2(self.embeddings)
        self.index.add(self.embeddings.astype(np.float32))
        
        # Save to cache
        self._save_to_cache()
        logger.info("PDF vector database built and cached successfully")
    
    def search_drawings(self, query: str, limit: int = 20, score_threshold: float = 0.3,
                       drawing_type_filter: Optional[PDFChunkType] = None,
                       equipment_filter: Optional[str] = None) -> List[PDFSearchResult]:
        """
        Search PDF drawings using semantic similarity
        
        Args:
            query: Natural language search query
            limit: Maximum number of results
            score_threshold: Minimum similarity score
            drawing_type_filter: Filter by drawing type
            equipment_filter: Filter by equipment tag
            
        Returns:
            List of search results ranked by relevance
        """
        if not self.chunks_data:
            logger.warning("No PDF data indexed")
            return []
        
        # Use vector search if available, otherwise fallback to text search
        if self.model is not None and self.index is not None and FAISS_AVAILABLE:
            return self._vector_search(query, limit, score_threshold, drawing_type_filter, equipment_filter)
        else:
            return self._text_search(query, limit, drawing_type_filter, equipment_filter)
    
    def find_equipment_context(self, equipment_tag: str, context_type: Optional[str] = None) -> List[PDFSearchResult]:
        """
        Find all drawings and context related to specific equipment
        
        Args:
            equipment_tag: Equipment identifier (e.g., "MCM01", "PDP01")
            context_type: Type of context (electrical, process, safety)
            
        Returns:
            List of relevant drawing search results
        """
        # Search for equipment tag in content and tags
        query = f"equipment {equipment_tag}"
        if context_type:
            query += f" {context_type}"
        
        results = self.search_drawings(query, limit=50, score_threshold=0.2)
        
        # Filter results that actually contain the equipment tag
        filtered_results = []
        for result in results:
            if (equipment_tag.upper() in result.equipment_tags or 
                equipment_tag.upper() in result.content.upper()):
                filtered_results.append(result)
        
        return filtered_results
    
    def get_drawing_details(self, drawing_number: Optional[str] = None, 
                           page_number: Optional[int] = None) -> List[PDFSearchResult]:
        """
        Get detailed information about a specific drawing
        
        Args:
            drawing_number: Drawing reference number
            page_number: Page number to retrieve
            
        Returns:
            List of chunks for the specified drawing/page
        """
        results = []
        
        for i, chunk in enumerate(self.chunks_data):
            match = False
            
            if drawing_number and chunk.drawing_number:
                if drawing_number.upper() in chunk.drawing_number.upper():
                    match = True
            
            if page_number and chunk.page_number == page_number:
                match = True
            
            if match:
                result = PDFSearchResult(
                    chunk_id=chunk.id,
                    chunk_type=chunk.chunk_type,
                    page_number=chunk.page_number,
                    drawing_number=chunk.drawing_number,
                    title=chunk.title,
                    description=chunk.searchable_text[:200] + "...",
                    score=1.0,  # Exact match
                    content=chunk.content,
                    equipment_tags=chunk.equipment_tags,
                    location=chunk.location,
                    file_path=chunk.metadata.get('source_file', '')
                )
                results.append(result)
        
        return results
    
    def _vector_search(self, query: str, limit: int, score_threshold: float,
                      drawing_type_filter: Optional[PDFChunkType],
                      equipment_filter: Optional[str]) -> List[PDFSearchResult]:
        """Vector-based semantic search"""
        
        # Create query embedding
        query_embedding = self.model.encode([query])
        faiss.normalize_L2(query_embedding)
        
        # Search for similar chunks
        search_limit = min(limit * 3, len(self.chunks_data))  # Get more to allow filtering
        scores, indices = self.index.search(query_embedding.astype(np.float32), search_limit)
        
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if score < score_threshold:
                continue
                
            chunk = self.chunks_data[idx]
            
            # Apply filters
            if drawing_type_filter and chunk.chunk_type != drawing_type_filter:
                continue
            if equipment_filter and equipment_filter.upper() not in chunk.equipment_tags:
                continue
            
            result = PDFSearchResult(
                chunk_id=chunk.id,
                chunk_type=chunk.chunk_type,
                page_number=chunk.page_number,
                drawing_number=chunk.drawing_number,
                title=chunk.title,
                description=chunk.searchable_text[:200] + "...",
                score=float(score),
                content=chunk.content,
                equipment_tags=chunk.equipment_tags,
                location=chunk.location,
                file_path=chunk.metadata.get('source_file', '')
            )
            results.append(result)
            
            if len(results) >= limit:
                break
        
        return results
    
    def _text_search(self, query: str, limit: int,
                    drawing_type_filter: Optional[PDFChunkType],
                    equipment_filter: Optional[str]) -> List[PDFSearchResult]:
        """Fallback text-based search"""
        
        query_lower = query.lower()
        results = []
        
        for chunk in self.chunks_data:
            # Apply filters first
            if drawing_type_filter and chunk.chunk_type != drawing_type_filter:
                continue
            if equipment_filter and equipment_filter.upper() not in chunk.equipment_tags:
                continue
            
            # Simple text matching
            searchable_text = chunk.searchable_text.lower()
            if query_lower in searchable_text:
                # Simple scoring based on term frequency
                score = searchable_text.count(query_lower) / len(searchable_text.split())
                
                result = PDFSearchResult(
                    chunk_id=chunk.id,
                    chunk_type=chunk.chunk_type,
                    page_number=chunk.page_number,
                    drawing_number=chunk.drawing_number,
                    title=chunk.title,
                    description=chunk.searchable_text[:200] + "...",
                    score=score,
                    content=chunk.content,
                    equipment_tags=chunk.equipment_tags,
                    location=chunk.location,
                    file_path=chunk.metadata.get('source_file', '')
                )
                results.append(result)
        
        # Sort by score and limit
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:limit]
    
    def _cache_exists(self) -> bool:
        """Check if cache files exist"""
        return (self.data_cache.exists() and 
                self.metadata_cache.exists() and
                (not FAISS_AVAILABLE or self.index_cache.exists()))
    
    def _cache_is_recent(self) -> bool:
        """Check if cache is recent enough"""
        try:
            cache_time = self.data_cache.stat().st_mtime
            # Cache is valid for 24 hours
            return (time.time() - cache_time) < 86400
        except:
            return False
    
    def _is_file_current(self, file_key: str, file_mtime: float) -> bool:
        """Check if file is already indexed and current"""
        if file_key not in self.indexed_files:
            return False
        return self.indexed_files[file_key]['mtime'] >= file_mtime
    
    def _save_to_cache(self):
        """Save vector database to cache files"""
        try:
            # Save chunks data
            with open(self.data_cache, 'wb') as f:
                pickle.dump(self.chunks_data, f)
            
            # Save metadata
            metadata = {
                'indexed_files': self.indexed_files,
                'total_chunks': len(self.chunks_data),
                'cache_time': time.time()
            }
            with open(self.metadata_cache, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            # Save FAISS index and embeddings if available
            if FAISS_AVAILABLE and self.index is not None:
                faiss.write_index(self.index, str(self.index_cache))
                
            if self.embeddings is not None:
                with open(self.embeddings_cache, 'wb') as f:
                    pickle.dump(self.embeddings, f)
                    
            logger.info("PDF vector database cached successfully")
        except Exception as e:
            logger.error(f"Failed to save cache: {e}")
    
    def _load_from_cache(self):
        """Load vector database from cache files"""
        try:
            # Load chunks data
            with open(self.data_cache, 'rb') as f:
                self.chunks_data = pickle.load(f)
            
            # Load metadata
            with open(self.metadata_cache, 'r') as f:
                metadata = json.load(f)
                self.indexed_files = metadata.get('indexed_files', {})
            
            # Load FAISS index if available
            if FAISS_AVAILABLE and self.index_cache.exists():
                self.index = faiss.read_index(str(self.index_cache))
                
            # Load embeddings if available
            if self.embeddings_cache.exists():
                with open(self.embeddings_cache, 'rb') as f:
                    self.embeddings = pickle.load(f)
            
            # Initialize model for future searches
            self.initialize_model()
            
            logger.info(f"Loaded cached PDF database with {len(self.chunks_data)} chunks")
        except Exception as e:
            logger.error(f"Failed to load cache: {e}")
            self.chunks_data = []
            self.indexed_files = {}
