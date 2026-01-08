"""Utility functions for the application."""
import re
import unicodedata


def generate_slug(title: str) -> str:
    """
    Generate a URL-safe slug from a title.
    
    Args:
        title: The title to convert to a slug
        
    Returns:
        A URL-safe slug
    """
    # Convert to lowercase
    slug = title.lower()
    
    # Normalize unicode characters
    slug = unicodedata.normalize('NFKD', slug)
    slug = slug.encode('ascii', 'ignore').decode('ascii')
    
    # Replace spaces and special characters with hyphens
    slug = re.sub(r'[^\w\s-]', '', slug)
    slug = re.sub(r'[-\s]+', '-', slug)
    
    # Remove leading/trailing hyphens
    slug = slug.strip('-')
    
    return slug
