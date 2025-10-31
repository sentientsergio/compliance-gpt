#!/usr/bin/env python3
"""
Generate TPA-facing mapping document for compliance analyst review
Includes full provision text, page numbers, and reasoning
"""

import json
import csv
from pathlib import Path
from typing import Dict, List

def load_json(filepath: str) -> Dict:
    """Load JSON file."""
    with open(filepath, 'r') as f:
        return json.load(f)

def get_provision_details(provision_id: str, provisions: List[Dict]) -> Dict:
    """
    Get full details for a provision by ID.
    Returns BPD text, page number, section title, and AA context.
    """
    for prov in provisions:
        if prov['plan_provision_id'] == provision_id:
            bpd = prov['bpd_component']

            # Build full provision text (BPD + AA context)
            provision_text = bpd.get('provision_text', '')

            # Add AA context if present
            aa_components = prov.get('aa_components', [])
            if aa_components:
                aa_summary = f" [Linked to {len(aa_components)} AA election(s)]"
                provision_text += aa_summary

            return {
                'section_number': bpd.get('section_number', 'N/A'),
                'section_title': bpd.get('section_title', 'N/A'),
                'provision_text': provision_text,
                'pdf_page': bpd.get('pdf_page', 'N/A'),
                'category': prov.get('provision_category', 'unknown'),
                'provision_id': bpd.get('provision_id', provision_id)
            }

    return None

def generate_matched_provisions_csv(
    crosswalk: Dict,
    relius_provisions: List[Dict],
    ascensus_provisions: List[Dict],
    output_path: str
):
    """
    Generate CSV of matched provisions with full text and provenance.
    For Lauren to review and verify matches.
    """
    print("Generating matched_provisions.csv...")

    rows = []

    for mapping in crosswalk['mappings']:
        llm_verification = mapping['llm_verification']
        match_type = llm_verification['match_type']

        # Only include exact and close matches
        if match_type in ['exact', 'close']:
            # Get Relius details
            relius = get_provision_details(
                mapping['source_provision_id'],
                relius_provisions
            )

            # Get Ascensus details
            ascensus = get_provision_details(
                mapping['target_provision_id'],
                ascensus_provisions
            )

            if relius and ascensus:
                row = {
                    'relius_section': relius['section_number'],
                    'relius_title': relius['section_title'],
                    'relius_page': relius['pdf_page'],
                    'relius_category': relius['category'],
                    'relius_provision_text': relius['provision_text'],

                    'ascensus_section': ascensus['section_number'],
                    'ascensus_title': ascensus['section_title'],
                    'ascensus_page': ascensus['pdf_page'],
                    'ascensus_category': ascensus['category'],
                    'ascensus_provision_text': ascensus['provision_text'],

                    'match_quality': match_type,
                    'confidence': f"{llm_verification['confidence']:.2f}",
                    'reasoning': llm_verification['reasoning'],
                    'variance_notes': llm_verification.get('variance_notes', ''),

                    # Technical provenance (for debugging)
                    'relius_provision_id': relius['provision_id'],
                    'ascensus_provision_id': ascensus['provision_id']
                }
                rows.append(row)

    # Sort by Relius section number (natural sort)
    def sort_key(row):
        section = row['relius_section']
        # Try to convert to float for numeric sorting
        try:
            return (0, float(section.replace('.', '')))
        except:
            return (1, section)

    rows.sort(key=sort_key)

    # Write CSV
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        fieldnames = [
            'relius_section', 'relius_title', 'relius_page', 'relius_category',
            'relius_provision_text',
            'ascensus_section', 'ascensus_title', 'ascensus_page', 'ascensus_category',
            'ascensus_provision_text',
            'match_quality', 'confidence', 'reasoning', 'variance_notes',
            'relius_provision_id', 'ascensus_provision_id'
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"  ✓ {len(rows)} matched provisions written")
    return len(rows)

def generate_unmapped_provisions_csv(
    crosswalk: Dict,
    relius_provisions: List[Dict],
    ascensus_provisions: List[Dict],
    output_path: str
):
    """
    Generate CSV of unmapped Relius provisions.
    Shows closest candidate that was rejected and why.
    """
    print("Generating unmapped_relius_provisions.csv...")

    rows = []

    for mapping in crosswalk['mappings']:
        llm_verification = mapping['llm_verification']
        match_type = llm_verification['match_type']

        # Only include no-match provisions
        if match_type == 'none':
            # Get Relius details
            relius = get_provision_details(
                mapping['source_provision_id'],
                relius_provisions
            )

            # Get closest Ascensus candidate (even though rejected)
            ascensus = get_provision_details(
                mapping['target_provision_id'],
                ascensus_provisions
            )

            if relius:
                row = {
                    'relius_section': relius['section_number'],
                    'relius_title': relius['section_title'],
                    'relius_page': relius['pdf_page'],
                    'relius_category': relius['category'],
                    'relius_provision_text': relius['provision_text'],

                    'closest_ascensus_section': ascensus['section_number'] if ascensus else 'N/A',
                    'closest_ascensus_title': ascensus['section_title'] if ascensus else 'N/A',
                    'closest_ascensus_page': ascensus['pdf_page'] if ascensus else 'N/A',
                    'closest_ascensus_text': ascensus['provision_text'] if ascensus else 'N/A',

                    'why_rejected': llm_verification['reasoning'],
                    'action_needed': 'Manually locate equivalent Ascensus provision or confirm provision not needed in target',

                    # Technical provenance
                    'relius_provision_id': relius['provision_id'],
                    'cosine_similarity': f"{mapping['cosine_similarity']:.4f}"
                }
                rows.append(row)

    # Sort by Relius section number
    def sort_key(row):
        section = row['relius_section']
        try:
            return (0, float(section.replace('.', '')))
        except:
            return (1, section)

    rows.sort(key=sort_key)

    # Write CSV
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        fieldnames = [
            'relius_section', 'relius_title', 'relius_page', 'relius_category',
            'relius_provision_text',
            'closest_ascensus_section', 'closest_ascensus_title', 'closest_ascensus_page',
            'closest_ascensus_text',
            'why_rejected', 'action_needed',
            'relius_provision_id', 'cosine_similarity'
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"  ✓ {len(rows)} unmapped provisions written")
    return len(rows)

def generate_new_ascensus_provisions_csv(
    crosswalk: Dict,
    ascensus_provisions: List[Dict],
    output_path: str
):
    """
    Generate CSV of Ascensus provisions that have no Relius equivalent.
    These are new provisions in the target document.
    """
    print("Generating new_ascensus_provisions.csv...")

    # Get set of matched Ascensus provision IDs
    matched_ascensus_ids = set()
    for mapping in crosswalk['mappings']:
        if mapping['llm_verification']['match_type'] in ['exact', 'close']:
            matched_ascensus_ids.add(mapping['target_provision_id'])

    rows = []

    for prov in ascensus_provisions:
        prov_id = prov['plan_provision_id']

        # Skip if this provision was matched
        if prov_id in matched_ascensus_ids:
            continue

        bpd = prov['bpd_component']
        provision_text = bpd.get('provision_text', '')

        # Add AA context if present
        aa_components = prov.get('aa_components', [])
        if aa_components:
            aa_summary = f" [Linked to {len(aa_components)} AA election(s)]"
            provision_text += aa_summary

        row = {
            'ascensus_section': bpd.get('section_number', 'N/A'),
            'ascensus_title': bpd.get('section_title', 'N/A'),
            'ascensus_page': bpd.get('pdf_page', 'N/A'),
            'ascensus_category': prov.get('provision_category', 'unknown'),
            'ascensus_provision_text': provision_text,
            'action_needed': 'New provision in Ascensus - determine if Relius equivalent exists or if this is a new requirement',
            'ascensus_provision_id': bpd.get('provision_id', prov_id)
        }
        rows.append(row)

    # Sort by Ascensus section number
    def sort_key(row):
        section = row['ascensus_section']
        try:
            return (0, float(section.replace('.', '')))
        except:
            return (1, section)

    rows.sort(key=sort_key)

    # Write CSV
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        fieldnames = [
            'ascensus_section', 'ascensus_title', 'ascensus_page', 'ascensus_category',
            'ascensus_provision_text',
            'action_needed',
            'ascensus_provision_id'
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"  ✓ {len(rows)} new Ascensus provisions written")
    return len(rows)

def main():
    """Main entry point."""

    # Paths
    base_dir = Path(__file__).parent.parent
    crosswalk_path = base_dir / "test_data/crosswalks/full_plan_provision_crosswalk.json"
    relius_path = base_dir / "test_data/plan_provisions/relius_plan_provisions_full.json"
    ascensus_path = base_dir / "test_data/plan_provisions/ascensus_plan_provisions_full.json"
    output_dir = base_dir / "test_data/crosswalks/lauren_view"

    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load data
    print("Loading data...")
    crosswalk = load_json(str(crosswalk_path))
    relius_data = load_json(str(relius_path))
    ascensus_data = load_json(str(ascensus_path))

    relius_provisions = relius_data['plan_provisions']
    ascensus_provisions = ascensus_data['plan_provisions']

    print(f"  Crosswalk: {crosswalk['summary']['total_mappings']} mappings")
    print(f"  Relius: {len(relius_provisions)} provisions")
    print(f"  Ascensus: {len(ascensus_provisions)} provisions")

    # Generate mapping documents
    print(f"\nGenerating Lauren's mapping documents...")
    print("="*60)

    matched_count = generate_matched_provisions_csv(
        crosswalk,
        relius_provisions,
        ascensus_provisions,
        str(output_dir / "matched_provisions.csv")
    )

    unmapped_count = generate_unmapped_provisions_csv(
        crosswalk,
        relius_provisions,
        ascensus_provisions,
        str(output_dir / "unmapped_relius_provisions.csv")
    )

    new_count = generate_new_ascensus_provisions_csv(
        crosswalk,
        ascensus_provisions,
        str(output_dir / "new_ascensus_provisions.csv")
    )

    print("="*60)
    print("\n✓ Lauren's mapping documents generated successfully")
    print(f"\nLocation: {output_dir}")
    print(f"\nFiles created:")
    print(f"  1. matched_provisions.csv           - {matched_count} provisions with Relius↔Ascensus matches")
    print(f"  2. unmapped_relius_provisions.csv   - {unmapped_count} Relius provisions without Ascensus equivalent")
    print(f"  3. new_ascensus_provisions.csv      - {new_count} Ascensus provisions not in Relius")
    print(f"\nTotal coverage:")
    print(f"  Matched: {matched_count}/{len(relius_provisions)} Relius provisions ({matched_count/len(relius_provisions)*100:.1f}%)")
    print(f"  Unmapped: {unmapped_count}/{len(relius_provisions)} Relius provisions ({unmapped_count/len(relius_provisions)*100:.1f}%)")
    print(f"  New in Ascensus: {new_count}/{len(ascensus_provisions)} Ascensus provisions ({new_count/len(ascensus_provisions)*100:.1f}%)")
    print(f"\nReady for Lauren's quality control review.\n")

if __name__ == "__main__":
    main()
