"""Custom ID generators for Kyros workflow."""

import random
import secrets
import string
from typing import Set


def generate_season_id(existing_ids: Set[str] = None) -> str:
    """
    Generate a unique Season ID in format: XXXX-XXXX
    Example: F9J1-KKG2
    
    Format: 4 alphanumeric characters - 4 alphanumeric characters
    Uses uppercase letters and digits only.
    """
    if existing_ids is None:
        existing_ids = set()
    
    chars = string.ascii_uppercase + string.digits
    
    max_attempts = 1000
    for _ in range(max_attempts):
        part1 = ''.join(random.choices(chars, k=4))
        part2 = ''.join(random.choices(chars, k=4))
        season_id = f"{part1}-{part2}"
        
        if season_id not in existing_ids:
            return season_id
    
    # Fallback with more entropy if somehow we can't generate unique
    part1 = ''.join(secrets.choice(chars) for _ in range(4))
    part2 = ''.join(secrets.choice(chars) for _ in range(4))
    return f"{part1}-{part2}"


def generate_location_id(existing_ids: Set[str] = None) -> str:
    """
    Generate a unique 16-character Location ID.
    
    Format: 16 alphanumeric characters (uppercase + digits)
    Example: A7B3C9D1E5F2G8H4
    """
    if existing_ids is None:
        existing_ids = set()
    
    chars = string.ascii_uppercase + string.digits
    
    max_attempts = 1000
    for _ in range(max_attempts):
        location_id = ''.join(random.choices(chars, k=16))
        
        if location_id not in existing_ids:
            return location_id
    
    # Fallback with cryptographic randomness
    return ''.join(secrets.choice(chars) for _ in range(16))


def generate_po_number(existing_ids: Set[str] = None) -> str:
    """
    Generate a unique PO Number.
    
    Format: PO-YYYYMMDD-XXXXXX
    Example: PO-20260127-A1B2C3
    """
    from datetime import date
    
    if existing_ids is None:
        existing_ids = set()
    
    today = date.today().strftime("%Y%m%d")
    chars = string.ascii_uppercase + string.digits
    
    max_attempts = 1000
    for _ in range(max_attempts):
        suffix = ''.join(random.choices(chars, k=6))
        po_number = f"PO-{today}-{suffix}"
        
        if po_number not in existing_ids:
            return po_number
    
    suffix = ''.join(secrets.choice(chars) for _ in range(6))
    return f"PO-{today}-{suffix}"


def validate_season_id_format(season_id: str) -> bool:
    """Validate that a season ID matches the expected format."""
    if not season_id or len(season_id) != 9:
        return False
    
    if season_id[4] != '-':
        return False
    
    valid_chars = set(string.ascii_uppercase + string.digits)
    part1, part2 = season_id[:4], season_id[5:]
    
    return all(c in valid_chars for c in part1 + part2)


def validate_location_id_format(location_id: str) -> bool:
    """Validate that a location ID matches the expected format."""
    if not location_id or len(location_id) != 16:
        return False
    
    valid_chars = set(string.ascii_uppercase + string.digits)
    return all(c in valid_chars for c in location_id)
