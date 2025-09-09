#!/usr/bin/env python3
"""
Tag Analyzer Package

This package provides AI-powered analysis and search capabilities for Studio 5000 tag CSV exports,
enabling semantic search through thousands of I/O points and device mappings.
"""

from .tag_chunk import TagChunk, TagChunkType
from .csv_tag_parser import CSVTagParser
from .tag_vector_db import TagVectorDatabase, TagSearchResult
from .tag_mcp_integration import TagMCPIntegration, TagMCPTools

__all__ = [
    'TagChunk',
    'TagChunkType',
    'CSVTagParser', 
    'TagVectorDatabase',
    'TagSearchResult',
    'TagMCPIntegration',
    'TagMCPTools'
]

__version__ = '1.0.0'
