"""
Deterministic Provision ID Generation

Implements stable, auditable provision IDs that:
1. Are reproducible across re-extractions (same provision → same ID)
2. Are globally unique (vendor + doctype + section + content hash)
3. Are human-readable (contain semantic anchors)
4. Support traceability (can reverse-lookup from ID to source)

ID Recipe:
    provision_id = vendor : doctype : section_path : sha1(provision_text[:512])

Examples:
    relius:bpd:ARTICLE_I.1.01:a3f2b9c1...
    ascensus:aa:Q_1.04:d7e8f2a3...
    relius:bpd:ARTICLE_III.UNK_1:c9d1e3f5...

Red Team Requirement:
    "Emit deterministic provision_ids... ID recipe (stable across runs)"
    - GPT-5 Pro Red Team Report, Oct 30, 2025
"""

import hashlib
import re
from typing import Dict, Any


def normalize_section_path(section_path: str) -> str:
    """
    Normalize section_path for consistent ID generation.

    Handles:
    - Whitespace normalization
    - Case normalization (preserve intent: ARTICLE_I vs Q_1.04)
    - Separator normalization (dots)

    Args:
        section_path: Raw section path from extraction

    Returns:
        Normalized section path

    Examples:
        >>> normalize_section_path("Article I.1.01")
        "ARTICLE_I.1.01"
        >>> normalize_section_path("Q 1.04")
        "Q_1.04"
        >>> normalize_section_path("  2.03  ")
        "2.03"
    """
    if not section_path:
        return ""

    # Strip whitespace
    path = section_path.strip()

    # Normalize "Article" prefix
    path = re.sub(r'^article\s+', 'ARTICLE_', path, flags=re.IGNORECASE)

    # Normalize "Q" prefix for AA elections
    path = re.sub(r'^q\s+', 'Q_', path, flags=re.IGNORECASE)

    # Normalize section separators to dots
    path = path.replace('-', '.')

    # Normalize whitespace within path
    path = re.sub(r'\s+', '_', path)

    return path


def generate_provision_hash(provision_text: str, length: int = 8) -> str:
    """
    Generate content hash for provision text.

    Uses first 512 chars to balance uniqueness vs stability
    (full text may change slightly at edges due to OCR/vision variance).

    Args:
        provision_text: Full provision text
        length: Hash prefix length (default 8 chars)

    Returns:
        Hex hash prefix

    Example:
        >>> generate_provision_hash("An Employee shall be eligible...")
        "a3f2b9c1"
    """
    # Normalize text before hashing
    text = provision_text.strip()
    text = re.sub(r'\s+', ' ', text)  # Normalize whitespace
    text = text[:512]  # First 512 chars for stability

    # SHA-1 hash (sufficient for non-cryptographic use)
    hash_obj = hashlib.sha1(text.encode('utf-8'))
    return hash_obj.hexdigest()[:length]


def generate_provision_id(
    vendor: str,
    doc_type: str,
    section_path: str,
    provision_text: str,
    page_number: int = None,
    ordinal: int = None
) -> str:
    """
    Generate deterministic provision ID.

    ID Structure:
        {vendor}:{doc_type}:{section_path}:{content_hash}

    Args:
        vendor: Vendor name (relius, ascensus, ftwilliam, datair)
        doc_type: Document type (bpd, aa)
        section_path: Normalized section path (e.g., "ARTICLE_I.1.01", "Q_1.04")
        provision_text: Full provision text (will be hashed)
        page_number: PDF page number (used for fallback anchoring if section_path empty)
        ordinal: Provision ordinal on page (used for fallback anchoring if section_path empty)

    Returns:
        Deterministic provision ID

    Examples:
        >>> generate_provision_id(
        ...     vendor="relius",
        ...     doc_type="bpd",
        ...     section_path="ARTICLE_I.1.01",
        ...     provision_text="\"Plan\" means the retirement plan..."
        ... )
        "relius:bpd:ARTICLE_I.1.01:a3f2b9c1"

        >>> generate_provision_id(
        ...     vendor="ascensus",
        ...     doc_type="aa",
        ...     section_path="",  # Missing section
        ...     provision_text="Employer contributions will be...",
        ...     page_number=15,
        ...     ordinal=2
        ... )
        "ascensus:aa:PAGE_15.ORD_2:d7e8f2a3"
    """
    # Normalize inputs
    vendor = vendor.lower().strip()
    doc_type = doc_type.lower().strip()
    section = normalize_section_path(section_path)

    # Fallback anchoring if section path missing
    if not section:
        if page_number is not None and ordinal is not None:
            section = f"PAGE_{page_number}.ORD_{ordinal}"
        elif page_number is not None:
            section = f"PAGE_{page_number}"
        else:
            section = "UNKNOWN"

    # Generate content hash
    content_hash = generate_provision_hash(provision_text)

    # Construct ID
    provision_id = f"{vendor}:{doc_type}:{section}:{content_hash}"

    return provision_id


def generate_mapping_id(source_provision_id: str, target_provision_id: str) -> str:
    """
    Generate deterministic mapping ID for crosswalk entries.

    Args:
        source_provision_id: Source provision ID
        target_provision_id: Target provision ID

    Returns:
        Mapping ID

    Example:
        >>> generate_mapping_id(
        ...     "relius:bpd:ARTICLE_I.1.01:a3f2b9c1",
        ...     "ascensus:bpd:1.01:d7e8f2a3"
        ... )
        "map:relius:bpd:ARTICLE_I.1.01:a3f2b9c1→ascensus:bpd:1.01:d7e8f2a3:c4f9a2b7"
    """
    # Create stable hash of both IDs
    combined = f"{source_provision_id}→{target_provision_id}"
    mapping_hash = hashlib.sha1(combined.encode('utf-8')).hexdigest()[:8]

    return f"map:{combined}:{mapping_hash}"


def parse_provision_id(provision_id: str) -> Dict[str, str]:
    """
    Parse provision ID back into components.

    Args:
        provision_id: Provision ID string

    Returns:
        Dictionary with components: vendor, doc_type, section_path, content_hash

    Example:
        >>> parse_provision_id("relius:bpd:ARTICLE_I.1.01:a3f2b9c1")
        {
            'vendor': 'relius',
            'doc_type': 'bpd',
            'section_path': 'ARTICLE_I.1.01',
            'content_hash': 'a3f2b9c1'
        }
    """
    parts = provision_id.split(':', 3)
    if len(parts) != 4:
        raise ValueError(f"Invalid provision ID format: {provision_id}")

    return {
        'vendor': parts[0],
        'doc_type': parts[1],
        'section_path': parts[2],
        'content_hash': parts[3]
    }


def add_provision_ids_to_extraction(
    extraction_data: Dict[str, Any],
    vendor: str,
    doc_type: str
) -> Dict[str, Any]:
    """
    Add deterministic provision IDs to extraction JSON.

    Modifies extraction data in-place, adding 'provision_id' field to each provision.

    Args:
        extraction_data: Extraction JSON dict (with 'provisions' or 'bpds' or 'aas' key)
        vendor: Vendor name (relius, ascensus, etc.)
        doc_type: Document type (bpd, aa)

    Returns:
        Modified extraction data with provision_ids added

    Example:
        >>> extraction = {
        ...     "provisions": [
        ...         {
        ...             "section_path": "ARTICLE_I.1.01",
        ...             "provision_text": "\"Plan\" means...",
        ...             "pdf_page": 5,
        ...             "page_sequence": 1
        ...         }
        ...     ]
        ... }
        >>> add_provision_ids_to_extraction(extraction, "relius", "bpd")
        {
            "provisions": [
                {
                    "section_path": "ARTICLE_I.1.01",
                    "provision_text": "\"Plan\" means...",
                    "pdf_page": 5,
                    "page_sequence": 1,
                    "provision_id": "relius:bpd:ARTICLE_I.1.01:a3f2b9c1"
                }
            ]
        }
    """
    # Detect provisions key
    if 'provisions' in extraction_data:
        provisions_key = 'provisions'
    elif 'bpds' in extraction_data:
        provisions_key = 'bpds'
    elif 'aas' in extraction_data:
        provisions_key = 'aas'
    else:
        raise ValueError("No provisions/bpds/aas key found in extraction data")

    provisions = extraction_data[provisions_key]

    for prov in provisions:
        # Get section path (may be missing)
        section_path = prov.get('section_path', '')

        # Get provision text
        provision_text = prov.get('provision_text', '')
        if not provision_text:
            raise ValueError(f"Provision missing provision_text: {prov}")

        # Get fallback anchors
        page_number = prov.get('pdf_page')
        ordinal = prov.get('page_sequence')

        # Generate ID
        provision_id = generate_provision_id(
            vendor=vendor,
            doc_type=doc_type,
            section_path=section_path,
            provision_text=provision_text,
            page_number=page_number,
            ordinal=ordinal
        )

        # Add to provision
        prov['provision_id'] = provision_id

    return extraction_data


# Debug helper for Red Team review
def generate_provision_id_debug(
    vendor: str,
    doc_type: str,
    section_path: str,
    provision_text: str,
    page_number: int = None,
    ordinal: int = None
) -> Dict[str, str]:
    """
    Generate provision ID with debug information showing ingredients.

    Red Team Requirement:
        "add a provision_id_debug column that echoes the ingredients so reviewers can trust it"

    Returns:
        Dictionary with 'provision_id' and 'id_ingredients' keys

    Example:
        >>> debug = generate_provision_id_debug(
        ...     vendor="relius",
        ...     doc_type="bpd",
        ...     section_path="ARTICLE_I.1.01",
        ...     provision_text="\"Plan\" means the retirement plan..."
        ... )
        >>> debug['provision_id']
        "relius:bpd:ARTICLE_I.1.01:a3f2b9c1"
        >>> debug['id_ingredients']
        "vendor=relius | doc_type=bpd | section=ARTICLE_I.1.01 | hash=sha1('Plan' means the retirement plan...[:512])"
    """
    provision_id = generate_provision_id(
        vendor=vendor,
        doc_type=doc_type,
        section_path=section_path,
        provision_text=provision_text,
        page_number=page_number,
        ordinal=ordinal
    )

    # Build ingredients string
    normalized_section = normalize_section_path(section_path)
    text_preview = provision_text.strip()[:50].replace('\n', ' ')

    if not normalized_section and page_number and ordinal:
        normalized_section = f"PAGE_{page_number}.ORD_{ordinal} (fallback)"

    ingredients = (
        f"vendor={vendor} | "
        f"doc_type={doc_type} | "
        f"section={normalized_section} | "
        f"hash=sha1('{text_preview}...'[:512])"
    )

    return {
        'provision_id': provision_id,
        'id_ingredients': ingredients
    }
