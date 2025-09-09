#!/usr/bin/env python3
"""
PDF Technical Drawings Parser

Extracts and analyzes content from technical PDF drawings.
Handles complex AutoCAD Electrical drawings with massive vector graphics.

Optimized for production-scale processing following existing architecture patterns.
"""

import os
import re
import time
import logging
import signal
import threading
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed

from .pdf_chunk import PDFChunk, PDFChunkType, PDFLocation

# PyMuPDF import with error handling
try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False
    logging.warning("PyMuPDF not available - PDF parsing disabled")

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class PDFParsingStats:
    """Statistics from PDF parsing operation"""
    total_pages: int
    pages_processed: int
    total_chunks: int
    processing_time: float
    text_chars_extracted: int
    drawings_analyzed: int
    complex_pages: int
    errors: List[str]

@dataclass
class OptimizedProcessingConfig:
    """Configuration for optimized PDF processing"""
    max_workers: int = 4  # Number of parallel workers
    batch_size: int = 10  # Pages per batch
    memory_cleanup_interval: int = 20  # Pages between memory cleanup
    progress_report_interval: int = 5  # Pages between progress reports
    sample_complex_pages: bool = True  # Use sampling for complex pages
    enable_early_termination: bool = True  # Allow Ctrl+C to stop gracefully
    use_optimized_mode: bool = False  # Enable optimized processing for large PDFs

class PDFParser:
    """
    Parser for technical PDF drawings with performance optimization
    
    Designed to handle AutoCAD Electrical PDFs with:
    - Rich text content (10k+ characters per page)
    - Massive vector graphics (400k+ drawings per page)
    - Complex engineering drawings and schematics
    - Optimized multi-threaded processing for large documents
    """
    
    def __init__(self, config: OptimizedProcessingConfig = None):
        self.config = config or OptimizedProcessingConfig()
        self.cancelled = False
        self.processed_pages = 0
        self.total_pages = 0
        self.start_time = None
        
        # Set up signal handler for graceful cancellation
        if self.config.enable_early_termination:
            try:
                signal.signal(signal.SIGINT, self._signal_handler)
            except ValueError:
                # Signal handlers can only be set in main thread
                pass
        
        self.equipment_tag_patterns = [
            r'\b[A-Z]{1,3}[-_]?\d{1,4}[A-Z]?\b',  # M001, CV-001, etc.
            r'\b[A-Z]{2,4}\d{2,4}\b',              # VFD01, PLC01, etc.
            r'\b\d{2,4}[A-Z]{1,3}\b',              # 001M, 001CV, etc.
        ]
        
        # Drawing type classification patterns
        self.drawing_type_patterns = {
            PDFChunkType.ELECTRICAL: [
                r'electrical', r'motor', r'power', r'control', r'mcc', r'starter',
                r'vfd', r'drive', r'panel', r'junction', r'conduit'
            ],
            PDFChunkType.PID: [
                r'process', r'flow', r'piping', r'instrumentation', r'p&id',
                r'valve', r'pump', r'tank', r'vessel', r'line'
            ],
            PDFChunkType.CONTROL_LOGIC: [
                r'logic', r'control', r'plc', r'program', r'routine',
                r'interlock', r'sequence', r'algorithm'
            ],
            PDFChunkType.IO_LIST: [
                r'i/o', r'input', r'output', r'signal', r'list', r'assignment',
                r'tag', r'address', r'rack', r'slot'
            ],
            PDFChunkType.LAYOUT: [
                r'layout', r'plan', r'elevation', r'section', r'detail',
                r'arrangement', r'location'
            ],
            PDFChunkType.SAFETY: [
                r'safety', r'emergency', r'stop', r'interlock', r'alarm',
                r'shutdown', r'protection'
            ]
        }
    
    def _signal_handler(self, signum, frame):
        """Handle Ctrl+C gracefully"""
        logger.info("\n🛑 Cancellation requested... finishing current batch...")
        self.cancelled = True
    
    def parse_pdf_file(self, file_path: str, max_pages: Optional[int] = None, 
                      sample_complex_pages: bool = True, use_optimized_mode: Optional[bool] = None) -> Tuple[List[PDFChunk], PDFParsingStats]:
        """
        Parse technical PDF drawings into searchable chunks
        
        Args:
            file_path: Path to PDF file
            max_pages: Limit processing to first N pages (for testing)
            sample_complex_pages: Use sampling for pages with >100k drawings
            use_optimized_mode: Use multi-threaded optimized processing (auto-detected for large PDFs)
            
        Returns:
            Tuple of (chunks_list, parsing_stats)
        """
        if not PYMUPDF_AVAILABLE:
            raise RuntimeError("PyMuPDF not available - cannot parse PDF files")
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"PDF file not found: {file_path}")
        
        # Auto-detect optimized mode for large PDFs
        if use_optimized_mode is None:
            try:
                with fitz.open(file_path) as doc:
                    total_pages = len(doc)
                    # Use optimized mode for PDFs with >50 pages
                    use_optimized_mode = total_pages > 50
            except:
                use_optimized_mode = False
        
        # Use optimized processing for large documents
        if use_optimized_mode:
            logger.info(f"🚀 Using optimized multi-threaded processing for: {file_path}")
            return self._parse_pdf_optimized(file_path, max_pages, sample_complex_pages)
        
        logger.info(f"🔍 Parsing PDF: {file_path}")
        start_time = time.time()
        
        chunks = []
        stats = PDFParsingStats(
            total_pages=0, pages_processed=0, total_chunks=0,
            processing_time=0, text_chars_extracted=0,
            drawings_analyzed=0, complex_pages=0, errors=[]
        )
        
        try:
            with fitz.open(file_path) as doc:
                stats.total_pages = len(doc)
                pages_to_process = min(max_pages or len(doc), len(doc))
                
                logger.info(f"📄 Processing {pages_to_process} of {len(doc)} pages...")
                
                for page_num in range(pages_to_process):
                    try:
                        page_chunks = self._parse_page(
                            doc[page_num], page_num + 1, 
                            sample_complex_pages=sample_complex_pages
                        )
                        chunks.extend(page_chunks)
                        stats.pages_processed += 1
                        
                        # Update statistics
                        for chunk in page_chunks:
                            stats.text_chars_extracted += len(chunk.content)
                        
                        # Check if this was a complex page
                        if len(page_chunks) > 0:
                            drawings_count = sum(1 for chunk in page_chunks 
                                               if chunk.chunk_type != PDFChunkType.NOTES)
                            if drawings_count > 50:  # Threshold for complex page
                                stats.complex_pages += 1
                        
                        if page_num % 10 == 0:
                            logger.info(f"  ✅ Processed page {page_num + 1}/{pages_to_process}")
                            
                    except Exception as e:
                        error_msg = f"Error processing page {page_num + 1}: {e}"
                        logger.error(error_msg)
                        stats.errors.append(error_msg)
                        continue
                
        except Exception as e:
            error_msg = f"Error opening PDF file: {e}"
            logger.error(error_msg)
            stats.errors.append(error_msg)
            raise
        
        stats.processing_time = time.time() - start_time
        stats.total_chunks = len(chunks)
        
        logger.info(f"✅ PDF parsing completed:")
        logger.info(f"   📊 {stats.total_chunks} chunks from {stats.pages_processed} pages")
        logger.info(f"   ⏱️  Processing time: {stats.processing_time:.1f} seconds")
        logger.info(f"   📝 Text extracted: {stats.text_chars_extracted:,} characters")
        
        return chunks, stats
    
    def _parse_page(self, page, page_number: int, sample_complex_pages: bool = True) -> List[PDFChunk]:
        """Parse a single PDF page into chunks"""
        chunks = []
        
        # Extract text content (this is always safe and reliable)
        text_content = page.get_text()
        text_length = len(text_content.strip())
        
        logger.info(f"  📄 Page {page_number}: extracted {text_length} characters of text")
        
        # Robust drawing analysis - this is CORE functionality, must work
        drawings_count = 0
        drawings_data = []
        
        logger.info(f"  🔍 Starting drawing analysis on page {page_number}...")
        start_time = time.time()
        
        try:
            # Use robust drawing analysis with chunked processing
            drawings_count, drawings_data = self._analyze_page_drawings_robust(page, page_number)
            analysis_time = time.time() - start_time
            
            logger.info(f"  ✅ Drawing analysis completed: {drawings_count:,} drawings in {analysis_time:.1f}s")
            
        except Exception as e:
            analysis_time = time.time() - start_time
            logger.error(f"  ❌ Drawing analysis failed on page {page_number} after {analysis_time:.1f}s: {e}")
            # Don't give up - try alternative analysis
            try:
                drawings_count = self._estimate_drawing_complexity(page, page_number)
                drawings_data = []  # No detailed data available from estimation
                logger.info(f"  📊 Estimated drawing complexity: {drawings_count:,}")
            except Exception as e2:
                logger.error(f"  ❌ Even complexity estimation failed: {e2}")
                drawings_count = 0
                drawings_data = []
        
        # Determine if this is a complex page
        is_complex = drawings_count > 100000
        
        if is_complex and sample_complex_pages:
            logger.info(f"  ⚠️  Complex page {page_number}: {drawings_count:,} drawings - using sampling")
            return self._parse_complex_page_sampled(page, page_number, text_content, drawings_count, drawings_data)
        else:
            return self._parse_standard_page(page, page_number, text_content, drawings_count, drawings_data)
    
    def _parse_standard_page(self, page, page_number: int, text_content: str, 
                           drawings_count: int, drawings_data: List[Dict]) -> List[PDFChunk]:
        """Parse a standard complexity page with drawing analysis"""
        chunks = []
        
        # Extract drawing title/number if present
        drawing_number, title = self._extract_title_info(text_content)
        
        # Classify drawing type based on content
        drawing_type = self._classify_drawing_type(text_content)
        
        # Extract equipment tags
        equipment_tags = self._extract_equipment_tags(text_content)
        
        # Create vision description based on drawing analysis
        vision_description = self._create_vision_description(drawings_count, drawings_data, drawing_type)
        
        # Create main content chunk
        if text_content.strip() or drawings_count > 0:
            chunk = PDFChunk(
                id=f"page_{page_number}",
                chunk_type=drawing_type,
                page_number=page_number,
                drawing_number=drawing_number,
                title=title,
                content=text_content,
                vision_description=vision_description,
                equipment_tags=equipment_tags,
                location=PDFLocation(page_number=page_number, drawing_number=drawing_number),
                metadata={
                    'text_length': len(text_content),
                    'drawings_count': drawings_count,
                    'drawings_analyzed': len(drawings_data),
                    'processing_method': 'standard'
                }
            )
            chunks.append(chunk)
        
        return chunks
    
    def _parse_complex_page_sampled(self, page, page_number: int, text_content: str,
                                  drawings_count: int, drawings_data: List[Dict]) -> List[PDFChunk]:
        """Parse a complex page using sampling and available drawing data"""
        chunks = []
        
        # Extract basic information 
        drawing_number, title = self._extract_title_info(text_content)
        drawing_type = self._classify_drawing_type(text_content)
        equipment_tags = self._extract_equipment_tags(text_content)
        
        # Create enhanced vision description for complex pages
        vision_description = self._create_vision_description(drawings_count, drawings_data, drawing_type, complex_page=True)
        
        # For complex pages, create a comprehensive chunk
        if text_content.strip() or drawings_count > 0:
            chunk = PDFChunk(
                id=f"page_{page_number}_complex",
                chunk_type=drawing_type,
                page_number=page_number,
                drawing_number=drawing_number,
                title=title,
                content=text_content,
                vision_description=vision_description,
                equipment_tags=equipment_tags,
                location=PDFLocation(page_number=page_number, drawing_number=drawing_number),
                metadata={
                    'text_length': len(text_content),
                    'drawings_count': drawings_count,
                    'drawings_analyzed': len(drawings_data),
                    'processing_method': 'sampled_complex',
                    'requires_vision_ai': True,
                    'complexity_level': 'high'
                }
            )
            chunks.append(chunk)
        
        return chunks
    
    def _create_vision_description(self, drawings_count: int, drawings_data: List[Dict], 
                                 drawing_type: PDFChunkType, complex_page: bool = False) -> str:
        """
        Create a vision description based on drawing analysis data
        """
        if drawings_count == 0:
            return "Text-based content with minimal graphics"
        
        # Analyze drawing types and patterns
        drawing_types = {}
        coordinate_ranges = []
        colors = set()
        
        for drawing in drawings_data[:100]:  # Sample first 100 for analysis
            if drawing.get('type'):
                drawing_types[drawing['type']] = drawing_types.get(drawing['type'], 0) + 1
            if drawing.get('coords'):
                coordinate_ranges.append(drawing['coords'])
            if drawing.get('color'):
                colors.add(drawing['color'])
        
        # Build description
        description_parts = []
        
        if complex_page:
            description_parts.append(f"Complex technical drawing with {drawings_count:,} vector elements")
        else:
            description_parts.append(f"Technical drawing with {drawings_count:,} vector elements")
        
        # Add drawing type information
        if drawing_types:
            common_types = sorted(drawing_types.items(), key=lambda x: x[1], reverse=True)[:3]
            type_desc = ", ".join([f"{count} {dtype}" for dtype, count in common_types])
            description_parts.append(f"Contains: {type_desc}")
        
        # Add drawing category context
        if drawing_type == PDFChunkType.ELECTRICAL:
            description_parts.append("Electrical schematic with motor controls, power distribution, and wiring diagrams")
        elif drawing_type == PDFChunkType.PID:
            description_parts.append("Process and instrumentation diagram showing equipment connections and flow paths")
        elif drawing_type == PDFChunkType.LAYOUT:
            description_parts.append("Layout drawing showing physical arrangement and spatial relationships")
        elif drawing_type == PDFChunkType.CONTROL_LOGIC:
            description_parts.append("Control logic diagram with programming elements and signal flows")
        
        # Add complexity indicator
        if drawings_count > 100000:
            description_parts.append("Extremely detailed with high-density technical information")
        elif drawings_count > 10000:
            description_parts.append("Detailed technical drawing with complex interconnections")
        elif drawings_count > 1000:
            description_parts.append("Standard technical drawing with moderate detail")
        
        return " | ".join(description_parts)
    
    def _extract_title_info(self, text: str) -> Tuple[Optional[str], Optional[str]]:
        """Extract drawing number and title from text"""
        lines = text.split('\n')
        
        drawing_number = None
        title = None
        
        for line in lines[:10]:  # Check first 10 lines
            line = line.strip()
            if not line:
                continue
                
            # Look for drawing number patterns
            drawing_match = re.search(r'\b(DWG|DRAWING|SH|SHEET)[\s\-_]*(\w+[-_]?\w*)\b', line, re.IGNORECASE)
            if drawing_match and not drawing_number:
                drawing_number = drawing_match.group(2)
            
            # Look for title (usually longest meaningful line in header)
            if len(line) > 10 and len(line) < 80 and not title:
                if not re.match(r'^\d+$', line):  # Not just numbers
                    title = line
        
        return drawing_number, title
    
    def _classify_drawing_type(self, text: str) -> PDFChunkType:
        """Classify the type of drawing based on text content"""
        text_lower = text.lower()
        
        # Score each type based on keyword matches
        type_scores = {}
        for drawing_type, keywords in self.drawing_type_patterns.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            if score > 0:
                type_scores[drawing_type] = score
        
        # Return the type with highest score, or GENERAL if no matches
        if type_scores:
            return max(type_scores.keys(), key=lambda k: type_scores[k])
        else:
            return PDFChunkType.GENERAL
    
    def _extract_equipment_tags(self, text: str) -> List[str]:
        """Extract equipment tags from text using pattern matching"""
        tags = set()
        
        for pattern in self.equipment_tag_patterns:
            matches = re.findall(pattern, text)
            tags.update(matches)
        
        # Filter out obvious false positives
        filtered_tags = []
        for tag in tags:
            # Skip if it's just numbers or too generic
            if not re.match(r'^\d+$', tag) and len(tag) >= 2:
                filtered_tags.append(tag)
        
        return sorted(list(set(filtered_tags)))
    
    def _analyze_page_drawings_robust(self, page, page_number: int) -> Tuple[int, List[Dict]]:
        """
        OPTIMIZED drawing analysis with smart filtering for massive drawing counts
        Filters out irrelevant drawings and focuses on meaningful content
        """
        import gc
        
        try:
            # First, get text locations to focus drawing analysis near equipment labels
            text_locations = self._get_text_locations(page)
            logger.info(f"    📝 Found {len(text_locations)} text regions for equipment context")
            
            logger.info(f"    🔍 Starting optimized drawing analysis on page {page_number}...")
            
            drawings_data = []
            drawings_count = 0
            filtered_count = 0
            batch_size = 5000  # Larger batches for efficiency
            
            # Get drawings with smart filtering
            try:
                all_drawings = page.get_drawings()
                total_drawings = len(all_drawings)
                logger.info(f"    📊 Found {total_drawings:,} total drawings")
                
                # Apply smart filtering based on drawing significance
                for batch_start in range(0, total_drawings, batch_size):
                    batch_end = min(batch_start + batch_size, total_drawings)
                    
                    logger.info(f"    📦 Filtering drawings {batch_start:,} to {batch_end:,}")
                    
                    batch_drawings = all_drawings[batch_start:batch_end]
                    
                    # Smart filtering and processing
                    for i, drawing in enumerate(batch_drawings):
                        try:
                            # SMART FILTER: Check if drawing is worth processing
                            if not self._is_drawing_significant(drawing, text_locations, batch_start + i):
                                filtered_count += 1
                                continue
                                
                            # Extract key drawing information safely
                            drawing_info = self._extract_drawing_info_safe(drawing, batch_start + i)
                            if drawing_info:
                                drawings_data.append(drawing_info)
                                drawings_count += 1
                                
                        except Exception as e:
                            logger.debug(f"    ⚠️  Error processing drawing {batch_start + i}: {e}")
                            continue
                    
                    # Memory cleanup and progress reporting
                    if batch_start > 0 and batch_start % 20000 == 0:
                        gc.collect()
                        filter_rate = (filtered_count / (batch_start + batch_size)) * 100
                        logger.info(f"    🧹 Memory cleanup after {batch_start:,} drawings")
                        logger.info(f"    📊 Filtering rate: {filter_rate:.1f}% (keeping meaningful content)")
                
                filter_rate = (filtered_count / total_drawings) * 100
                logger.info(f"    ✅ Smart filtering: {filtered_count:,} filtered out ({filter_rate:.1f}%)")
                logger.info(f"    ✅ Processed {drawings_count:,} meaningful drawings of {total_drawings:,} total")
                return drawings_count, drawings_data
                
            except Exception as e:
                logger.warning(f"    ⚠️  get_drawings() failed: {e}")
                raise e
                
        except Exception as e:
            logger.error(f"    ❌ Optimized drawing analysis failed: {e}")
            raise e
    
    def _get_text_locations(self, page) -> List[Dict]:
        """Get locations of text on the page to focus drawing analysis"""
        try:
            text_blocks = page.get_text("dict")
            text_locations = []
            
            for block in text_blocks.get("blocks", []):
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        if span.get("text", "").strip():
                            bbox = span.get("bbox")
                            if bbox:
                                text_locations.append({
                                    'bbox': bbox,
                                    'text': span.get("text", "").strip(),
                                    'x': (bbox[0] + bbox[2]) / 2,
                                    'y': (bbox[1] + bbox[3]) / 2
                                })
            
            return text_locations
        except:
            return []
    
    def _is_drawing_significant(self, drawing: Dict, text_locations: List[Dict], drawing_index: int) -> bool:
        """
        SMART FILTER: Determine if a drawing is significant enough to process
        
        Filters out:
        - Tiny decorative elements
        - Drawings far from text/equipment labels  
        - Repetitive grid/border elements
        - Construction lines and guides
        
        Keeps:
        - Equipment symbols and shapes
        - Drawings near text labels
        - Connection lines between equipment
        - Larger meaningful elements
        """
        try:
            # Get drawing bounds/area
            rect = drawing.get('rect')
            if not rect or len(rect) < 4:
                return False
            
            # Calculate drawing area
            width = abs(rect[2] - rect[0])
            height = abs(rect[3] - rect[1])
            area = width * height
            
            # Filter 1: Size threshold - skip tiny drawings
            if area < 50:  # Less than 50 square pixels
                return False
                
            # Filter 2: Skip extremely thin lines (construction/grid lines)
            if (width < 2 and height > 100) or (height < 2 and width > 100):
                return False
            
            # Filter 3: Equipment proximity - prioritize drawings near text
            if text_locations:
                drawing_center_x = (rect[0] + rect[2]) / 2
                drawing_center_y = (rect[1] + rect[3]) / 2
                
                # Check if within 200 pixels of any text
                near_text = False
                for text_loc in text_locations:
                    distance = ((drawing_center_x - text_loc['x'])**2 + 
                               (drawing_center_y - text_loc['y'])**2)**0.5
                    if distance < 200:  # Within 200 pixels of text
                        near_text = True
                        break
                
                # If not near text, apply stricter size filter
                if not near_text and area < 500:
                    return False
            
            # Filter 4: Sampling for very dense areas - keep every 5th drawing
            # This prevents over-processing in areas with thousands of tiny elements
            if area < 200 and drawing_index % 5 != 0:
                return False
                
            # Passed all filters - this drawing is significant
            return True
            
        except Exception as e:
            # If filtering fails, err on the side of including the drawing
            return True
    
    def _extract_drawing_info_safe(self, drawing, drawing_index: int) -> Optional[Dict]:
        """
        Safely extract information from a single drawing object
        Returns None if extraction fails
        """
        try:
            # Extract basic drawing information with safety checks
            drawing_info = {
                'index': drawing_index,
                'type': None,
                'coords': None,
                'color': None,
                'style': None
            }
            
            # Safely extract drawing type
            try:
                if 'type' in drawing:
                    drawing_info['type'] = str(drawing['type'])
            except:
                pass
            
            # Safely extract coordinates (this is where the original error occurred)
            try:
                if 'rect' in drawing and drawing['rect']:
                    # This is the problematic line from the traceback
                    # We'll handle it more carefully
                    rect_data = drawing['rect']
                    if isinstance(rect_data, (list, tuple)) and len(rect_data) >= 4:
                        try:
                            coords = [float(x) for x in rect_data[:4]]
                            drawing_info['coords'] = coords
                        except (ValueError, TypeError):
                            # Skip if coordinates can't be converted to float
                            pass
            except:
                pass
            
            # Safely extract other properties
            try:
                if 'color' in drawing:
                    drawing_info['color'] = str(drawing['color'])
                if 'width' in drawing:
                    drawing_info['width'] = float(drawing['width'])
            except:
                pass
            
            return drawing_info
            
        except Exception as e:
            # Return None for failed extractions
            logger.debug(f"Drawing {drawing_index} extraction failed: {e}")
            return None
    
    def _estimate_drawing_complexity(self, page, page_number: int) -> int:
        """
        Estimate drawing complexity using alternative methods when direct analysis fails
        """
        try:
            # Method 1: Try to estimate based on page content size
            logger.info(f"    📏 Estimating complexity for page {page_number}...")
            
            # Get basic page info
            page_rect = page.rect
            page_area = (page_rect.width * page_rect.height)
            
            # Try to get page content streams to estimate complexity
            try:
                # Get raw content (this might give us size info)
                content = page.get_contents()
                if content:
                    content_size = len(content)
                    # Rough estimation: more content = more drawings
                    estimated_drawings = content_size // 100  # Very rough heuristic
                    logger.info(f"    📊 Content-based estimate: {estimated_drawings:,} drawings")
                    return estimated_drawings
            except:
                pass
            
            # Method 2: Estimate based on text density and page area
            text_length = len(page.get_text().strip())
            
            if text_length > 5000:
                # Text-heavy page, likely fewer complex drawings
                return 1000
            elif text_length > 1000:
                # Mixed content
                return 10000
            else:
                # Drawing-heavy page
                return 100000
                
        except Exception as e:
            logger.warning(f"    ⚠️  Complexity estimation failed: {e}")
            return 0
    
    def _parse_pdf_optimized(self, file_path: str, max_pages: Optional[int] = None, 
                           sample_complex_pages: bool = True) -> Tuple[List[PDFChunk], PDFParsingStats]:
        """
        Optimized multi-threaded PDF parsing for large documents
        """
        self.start_time = time.time()
        self.cancelled = False
        
        try:
            with fitz.open(file_path) as doc:
                self.total_pages = len(doc)
                pages_to_process = min(max_pages or self.total_pages, self.total_pages)
                
                logger.info(f"📄 Processing {pages_to_process} pages with {self.config.max_workers} workers...")
                
                all_chunks = []
                
                # Process in batches
                for batch_start in range(0, pages_to_process, self.config.batch_size):
                    if self.cancelled:
                        logger.info(f"🛑 Processing cancelled at page {batch_start}")
                        break
                    
                    batch_end = min(batch_start + self.config.batch_size, pages_to_process)
                    logger.info(f"📦 Processing batch: pages {batch_start + 1}-{batch_end}")
                    
                    # Process batch in parallel
                    batch_chunks = self._process_batch_parallel(doc, batch_start, batch_end, file_path)
                    all_chunks.extend(batch_chunks)
                    
                    self.processed_pages = batch_end
                    self._report_progress()
                    
                    # Memory cleanup
                    if batch_start > 0 and batch_start % (self.config.memory_cleanup_interval * self.config.batch_size) == 0:
                        import gc
                        gc.collect()
                        logger.info(f"🧹 Memory cleanup after {batch_start} pages")
                
                # Create stats
                processing_time = time.time() - self.start_time
                stats = PDFParsingStats(
                    total_pages=self.total_pages,
                    pages_processed=self.processed_pages,
                    total_chunks=len(all_chunks),
                    processing_time=processing_time,
                    text_chars_extracted=sum(len(chunk.content) for chunk in all_chunks),
                    drawings_analyzed=0,  # Not available in optimized mode
                    complex_pages=0,
                    errors=[]
                )
                
                logger.info(f"✅ Optimized processing completed: {len(all_chunks)} chunks in {processing_time:.1f}s")
                return all_chunks, stats
                
        except Exception as e:
            logger.error(f"❌ Optimized processing failed: {e}")
            raise
    
    def _process_batch_parallel(self, doc, batch_start: int, batch_end: int, pdf_path: str) -> List[PDFChunk]:
        """Process a batch of pages in parallel"""
        batch_chunks = []
        
        # Extract page data for parallel processing
        page_data = []
        for page_num in range(batch_start, batch_end):
            try:
                page = doc[page_num]
                page_data.append({
                    'page_number': page_num + 1,
                    'text_content': page.get_text(),
                    'pdf_path': pdf_path
                })
            except Exception as e:
                logger.warning(f"Failed to extract page {page_num + 1}: {e}")
        
        # Process pages in parallel
        with ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
            future_to_page = {
                executor.submit(self._process_single_page_optimized, page_info): page_info
                for page_info in page_data
            }
            
            for future in as_completed(future_to_page):
                if self.cancelled:
                    break
                    
                page_info = future_to_page[future]
                try:
                    page_chunks = future.result()
                    if page_chunks:
                        batch_chunks.extend(page_chunks)
                except Exception as e:
                    logger.warning(f"Failed to process page {page_info['page_number']}: {e}")
        
        return batch_chunks
    
    def _process_single_page_optimized(self, page_info: Dict[str, Any]) -> List[PDFChunk]:
        """Process a single page optimized for speed (thread-safe)"""
        try:
            page_number = page_info['page_number']
            text_content = page_info['text_content']
            pdf_path = page_info['pdf_path']
            
            if not text_content.strip():
                return []
            
            # Fast extraction methods
            drawing_number, title = self._extract_title_info(text_content)
            drawing_type = self._classify_drawing_type(text_content)
            equipment_tags = self._extract_equipment_tags(text_content)
            
            # Create optimized chunk
            chunk = PDFChunk(
                id=f"page_{page_number}_optimized",
                chunk_type=drawing_type,
                page_number=page_number,
                drawing_number=drawing_number,
                title=title,
                content=text_content,
                vision_description=f"Technical drawing page {page_number} with {len(equipment_tags)} equipment tags",
                equipment_tags=equipment_tags,
                location=PDFLocation(page_number=page_number, drawing_number=drawing_number),
                metadata={
                    'text_length': len(text_content),
                    'processing_method': 'optimized_parallel',
                    'source_file': pdf_path,
                    'equipment_count': len(equipment_tags)
                }
            )
            
            return [chunk]
            
        except Exception as e:
            logger.debug(f"Error processing page {page_info.get('page_number', 'unknown')}: {e}")
            return []
    
    def _report_progress(self):
        """Report processing progress"""
        if self.processed_pages % self.config.progress_report_interval == 0:
            elapsed = time.time() - self.start_time
            pages_per_sec = self.processed_pages / elapsed if elapsed > 0 else 0
            remaining_pages = self.total_pages - self.processed_pages
            eta_seconds = remaining_pages / pages_per_sec if pages_per_sec > 0 else 0
            
            logger.info(f"📊 Progress: {self.processed_pages}/{self.total_pages} pages "
                       f"({self.processed_pages/self.total_pages*100:.1f}%) | "
                       f"{pages_per_sec:.1f} pages/sec | "
                       f"ETA: {eta_seconds/60:.1f} min")

# Quick test function
def test_parser_on_pdf(pdf_path: str, max_pages: int = 5):
    """Test the parser on a real PDF file with automatic optimization"""
    # Configure for large document optimization
    config = OptimizedProcessingConfig(
        max_workers=4,
        batch_size=5,
        use_optimized_mode=True
    )
    parser = PDFParser(config)
    
    try:
        chunks, stats = parser.parse_pdf_file(pdf_path, max_pages=max_pages)
        
        print(f"\n🎯 PDF Parser Test Results:")
        print(f"   📄 Pages processed: {stats.pages_processed}")
        print(f"   📦 Chunks created: {stats.total_chunks}")
        print(f"   ⏱️  Processing time: {stats.processing_time:.2f}s")
        print(f"   📝 Text extracted: {stats.text_chars_extracted:,} chars")
        
        if chunks:
            print(f"\n📋 Sample chunks:")
            for i, chunk in enumerate(chunks[:3]):
                print(f"   {i+1}. {chunk.display_name}")
                print(f"      Type: {chunk.chunk_type.value}")
                print(f"      Equipment: {chunk.equipment_tags}")
                print(f"      Text: {chunk.content[:100]}...")
                
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    # Test with the actual PDF
    pdf_path = r"C:\Users\kontr\OneDrive\Desktop\MCM_06_Real\2429_AMAZON-MTN6-MCM01_V10 (1).pdf"
    test_parser_on_pdf(pdf_path, max_pages=3)
