#!/usr/bin/env python3
"""
Extract diagnostic CSVs from full crosswalk JSON for advisor analysis
"""

import json
import csv
from pathlib import Path
from typing import List, Dict

def load_crosswalk(filepath: str) -> Dict:
    """Load crosswalk JSON."""
    with open(filepath, 'r') as f:
        return json.load(f)

def extract_candidate_analysis(crosswalk: Dict, output_path: str):
    """
    CSV #1: Every candidate pair evaluated
    Shows full two-stage funnel (embeddings → LLM)
    """
    print("Extracting candidate_analysis.csv...")

    rows = []
    for mapping in crosswalk['mappings']:
        relius_section = mapping['source_section']
        relius_category = mapping['source_category']

        # Get Relius title from best candidate (we don't store source title in mapping)
        # For now, use section number as identifier
        relius_title = f"Section {relius_section}"

        # Best candidate (the one that was LLM-verified)
        ascensus_section = mapping['target_section']
        ascensus_category = mapping['target_category']
        ascensus_title = f"Section {ascensus_section}"

        cosine_sim = mapping['cosine_similarity']
        llm_verification = mapping['llm_verification']

        row = {
            'relius_section': relius_section,
            'relius_title': relius_title,
            'relius_category': relius_category,
            'ascensus_section': ascensus_section,
            'ascensus_title': ascensus_title,
            'ascensus_category': ascensus_category,
            'cosine_similarity': f"{cosine_sim:.4f}",
            'llm_match_quality': llm_verification['match_type'],
            'llm_confidence': f"{llm_verification['confidence']:.2f}",
            'llm_reasoning': llm_verification['reasoning'],
            'variance_notes': llm_verification.get('variance_notes', '')
        }
        rows.append(row)

    # Write CSV
    with open(output_path, 'w', newline='') as f:
        fieldnames = [
            'relius_section', 'relius_title', 'relius_category',
            'ascensus_section', 'ascensus_title', 'ascensus_category',
            'cosine_similarity', 'llm_match_quality', 'llm_confidence',
            'llm_reasoning', 'variance_notes'
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"  ✓ {len(rows)} candidate pairs written")

def extract_high_cosine_rejections(crosswalk: Dict, output_path: str):
    """
    CSV #2: High cosine similarity but LLM rejected
    Filter: cosine > 0.75 AND llm_match_quality = "none"
    """
    print("Extracting high_cosine_rejections.csv...")

    rows = []
    for mapping in crosswalk['mappings']:
        cosine_sim = mapping['cosine_similarity']
        llm_verification = mapping['llm_verification']
        match_type = llm_verification['match_type']

        # Filter: high cosine but LLM said "none"
        if cosine_sim > 0.75 and match_type == 'none':
            relius_section = mapping['source_section']
            relius_category = mapping['source_category']
            relius_title = f"Section {relius_section}"

            ascensus_section = mapping['target_section']
            ascensus_category = mapping['target_category']
            ascensus_title = f"Section {ascensus_section}"

            row = {
                'relius_section': relius_section,
                'relius_title': relius_title,
                'relius_category': relius_category,
                'ascensus_section': ascensus_section,
                'ascensus_title': ascensus_title,
                'ascensus_category': ascensus_category,
                'cosine_similarity': f"{cosine_sim:.4f}",
                'llm_match_quality': match_type,
                'llm_confidence': f"{llm_verification['confidence']:.2f}",
                'llm_reasoning': llm_verification['reasoning'],
                'variance_notes': llm_verification.get('variance_notes', '')
            }
            rows.append(row)

    # Sort by cosine similarity descending
    rows.sort(key=lambda x: float(x['cosine_similarity']), reverse=True)

    # Write CSV
    with open(output_path, 'w', newline='') as f:
        fieldnames = [
            'relius_section', 'relius_title', 'relius_category',
            'ascensus_section', 'ascensus_title', 'ascensus_category',
            'cosine_similarity', 'llm_match_quality', 'llm_confidence',
            'llm_reasoning', 'variance_notes'
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"  ✓ {len(rows)} high-cosine rejections found")

def extract_provision_stats(crosswalk: Dict, output_path: str):
    """
    CSV #3: Per-provision statistics
    One row per Relius provision showing candidate counts and acceptance rates
    """
    print("Extracting provision_stats.csv...")

    rows = []
    for mapping in crosswalk['mappings']:
        relius_section = mapping['source_section']
        relius_category = mapping['source_category']
        relius_title = f"Section {relius_section}"

        # Number of candidates (from all_candidates list)
        num_candidates = len(mapping.get('all_candidates', []))

        # Number accepted (1 if match_type is exact or close, 0 if none)
        match_type = mapping['llm_verification']['match_type']
        num_accepted = 1 if match_type in ['exact', 'close'] else 0
        acceptance_rate = num_accepted / num_candidates if num_candidates > 0 else 0

        # Best candidate info
        best_cosine = mapping['cosine_similarity']
        best_match_section = mapping['target_section']
        best_match_category = mapping['target_category']

        row = {
            'relius_section': relius_section,
            'relius_title': relius_title,
            'relius_category': relius_category,
            'num_candidates': num_candidates,
            'num_accepted': num_accepted,
            'acceptance_rate': f"{acceptance_rate:.2f}",
            'best_cosine': f"{best_cosine:.4f}",
            'best_match_section': best_match_section,
            'best_match_category': best_match_category,
            'llm_match_quality': match_type
        }
        rows.append(row)

    # Write CSV
    with open(output_path, 'w', newline='') as f:
        fieldnames = [
            'relius_section', 'relius_title', 'relius_category',
            'num_candidates', 'num_accepted', 'acceptance_rate',
            'best_cosine', 'best_match_section', 'best_match_category',
            'llm_match_quality'
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"  ✓ {len(rows)} provision stats written")

def extract_unmapped_provisions(crosswalk: Dict, output_path: str):
    """
    CSV #4: Provisions with no good candidates (cosine < 0.7 threshold)
    Shows potential false negatives from embedding filter
    """
    print("Extracting unmapped_provisions.csv...")

    COSINE_THRESHOLD = 0.7

    rows = []
    for mapping in crosswalk['mappings']:
        best_cosine = mapping['cosine_similarity']

        # Filter: best candidate below threshold
        if best_cosine < COSINE_THRESHOLD:
            relius_section = mapping['source_section']
            relius_category = mapping['source_category']
            relius_title = f"Section {relius_section}"

            highest_candidate_section = mapping['target_section']
            highest_candidate_category = mapping['target_category']
            highest_candidate_title = f"Section {highest_candidate_section}"
            highest_candidate_cosine = best_cosine

            row = {
                'relius_section': relius_section,
                'relius_title': relius_title,
                'relius_category': relius_category,
                'highest_candidate_section': highest_candidate_section,
                'highest_candidate_title': highest_candidate_title,
                'highest_candidate_category': highest_candidate_category,
                'highest_candidate_cosine': f"{highest_candidate_cosine:.4f}",
                'llm_match_quality': mapping['llm_verification']['match_type'],
                'llm_reasoning': mapping['llm_verification']['reasoning']
            }
            rows.append(row)

    # Sort by cosine ascending (worst matches first)
    rows.sort(key=lambda x: float(x['highest_candidate_cosine']))

    # Write CSV
    with open(output_path, 'w', newline='') as f:
        fieldnames = [
            'relius_section', 'relius_title', 'relius_category',
            'highest_candidate_section', 'highest_candidate_title', 'highest_candidate_category',
            'highest_candidate_cosine', 'llm_match_quality', 'llm_reasoning'
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"  ✓ {len(rows)} unmapped provisions (cosine < {COSINE_THRESHOLD})")

def main():
    """Main entry point."""

    # Paths
    base_dir = Path(__file__).parent.parent
    crosswalk_path = base_dir / "test_data/crosswalks/full_plan_provision_crosswalk.json"
    output_dir = base_dir / "test_data/crosswalks/diagnostics"

    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load crosswalk
    print(f"Loading crosswalk from: {crosswalk_path}")
    crosswalk = load_crosswalk(str(crosswalk_path))
    print(f"  Loaded: {crosswalk['metadata']['source_provision_count']} source provisions")
    print(f"          {crosswalk['metadata']['target_provision_count']} target provisions")
    print(f"          {crosswalk['summary']['total_mappings']} mappings")

    # Extract diagnostics
    print(f"\nExtracting diagnostic CSVs to: {output_dir}")
    print("="*60)

    extract_candidate_analysis(
        crosswalk,
        str(output_dir / "candidate_analysis.csv")
    )

    extract_high_cosine_rejections(
        crosswalk,
        str(output_dir / "high_cosine_rejections.csv")
    )

    extract_provision_stats(
        crosswalk,
        str(output_dir / "provision_stats.csv")
    )

    extract_unmapped_provisions(
        crosswalk,
        str(output_dir / "unmapped_provisions.csv")
    )

    print("="*60)
    print("\n✓ All diagnostic CSVs extracted successfully")
    print(f"\nFiles created:")
    print(f"  1. candidate_analysis.csv       - All {crosswalk['summary']['total_mappings']} candidate pairs")
    print(f"  2. high_cosine_rejections.csv   - Suspicious rejections (cosine>0.75, LLM='none')")
    print(f"  3. provision_stats.csv          - Per-provision statistics")
    print(f"  4. unmapped_provisions.csv      - Low-cosine provisions (potential false negatives)")
    print(f"\nReady for advisor analysis.\n")

if __name__ == "__main__":
    main()
