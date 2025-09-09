#!/usr/bin/env python3
"""
L5X Analyzer Package

This package provides AI-powered analysis and modification capabilities for Studio 5000 L5X files
using vector databases and the official Studio 5000 SDK for production-scale projects.
"""

from .l5x_chunk import L5XChunk, L5XChunkType
from .sdk_powered_analyzer import SDKPoweredL5XAnalyzer
from .l5x_vector_db import L5XVectorDatabase, L5XSearchResult
from .l5x_mcp_integration import L5XSDKMCPIntegration, L5XMCPTools

__all__ = [
    'L5XChunk',
    'L5XChunkType', 
    'SDKPoweredL5XAnalyzer',
    'L5XVectorDatabase',
    'L5XSearchResult',
    'L5XSDKMCPIntegration',
    'L5XMCPTools'
]

__version__ = '1.0.0'
