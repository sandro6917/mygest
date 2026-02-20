"""
Modulo Utils - Funzioni comuni di utilità
"""
from .file_utils import get_unique_filename, move_to_orphaned, ensure_directory
from .string_utils import normalize_string, slugify_italian, truncate_string
from .date_utils import parse_date_flexible, format_date_italian, get_fiscal_year
from .navigation_utils import get_referrer_from_request, build_back_url

__all__ = [
    # File utilities
    'get_unique_filename',
    'move_to_orphaned',
    'ensure_directory',
    
    # String utilities
    'normalize_string',
    'slugify_italian',
    'truncate_string',
    
    # Date utilities
    'parse_date_flexible',
    'format_date_italian',
    'get_fiscal_year',
    
    # Navigation utilities
    'get_referrer_from_request',
    'build_back_url',
]
