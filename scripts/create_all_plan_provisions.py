#!/usr/bin/env python3
"""
Create ALL Plan Provisions (BPD+AA merger at template level)
Scales Phase 1 POC to full production corpus
"""

import json
import sys
from pathlib import Path
from typing import List, Dict

def load_json(filepath: str) -> List[Dict]:
    """Load provisions/elections from JSON file."""
    with open(filepath, 'r') as f:
        data = json.load(f)

    # Handle different JSON structures
    if isinstance(data, list):
        return data
    elif 'bpds' in data:  # BPD v4.1 format
        return data['bpds']
    elif 'aas' in data:  # AA v5.1 format
        return data['aas']
    elif 'provisions' in data:
        return data['provisions']
    elif 'elections' in data:
        return data['elections']
    else:
        return []

def find_aa_elections_for_bpd(
    bpd_prov: Dict,
    aa_elections: List[Dict],
    domain_keywords: Dict[str, List[str]]
) -> List[Dict]:
    """
    Find AA elections that relate to this BPD provision using keyword matching.
    Returns list of (aa_election, confidence, method) tuples.
    """
    links = []

    bpd_title = (bpd_prov.get('section_title') or '').lower()
    bpd_text = (bpd_prov.get('provision_text') or '')[:500].lower()
    bpd_section = (bpd_prov.get('section_number') or '').lower()

    # Detect category from keywords
    detected_categories = []
    for category, keywords in domain_keywords.items():
        if any(kw in bpd_title or kw in bpd_text for kw in keywords):
            detected_categories.append(category)

    if not detected_categories:
        detected_categories = ['unknown']

    # Find matching AA elections for each detected category
    for category in detected_categories:
        category_keywords = domain_keywords.get(category, [])

        for aa in aa_elections:
            aa_title = (aa.get('section_title') or '').lower()
            aa_text = (aa.get('provision_text') or '')[:500].lower()
            aa_section = (aa.get('section_number') or '').lower()

            # Check for keyword overlap
            if any(kw in aa_title or kw in aa_text for kw in category_keywords):
                # Calculate simple confidence based on keyword density
                keyword_matches = sum(1 for kw in category_keywords if kw in aa_title or kw in aa_text)
                confidence = min(0.95, 0.6 + (keyword_matches * 0.1))

                links.append({
                    'aa_election': aa,
                    'confidence': confidence,
                    'method': 'keyword_matching',
                    'category': category
                })

    # Deduplicate and return top matches
    seen_ids = set()
    unique_links = []
    for link in sorted(links, key=lambda x: x['confidence'], reverse=True):
        aa_id = link['aa_election'].get('provision_id') or link['aa_election'].get('section_number')
        if aa_id and aa_id not in seen_ids:
            seen_ids.add(aa_id)
            unique_links.append(link)

    return unique_links[:5]  # Max 5 AA elections per BPD

def create_plan_provision(
    bpd_prov: Dict,
    aa_links: List[Dict],
    vendor: str,
    provision_counter: int
) -> Dict:
    """Create a Plan Provision from BPD + linked AA elections."""

    # Determine primary category
    categories = [link['category'] for link in aa_links if 'category' in link]
    primary_category = categories[0] if categories else 'unknown'

    # Build plan provision
    plan_provision = {
        'plan_provision_id': f"prov_{vendor.lower()}_{primary_category}_{provision_counter:04d}",
        'canonical_key': f"{primary_category}.template",
        'provision_category': primary_category,
        'source_vendor': vendor,
        'completeness': 'template',

        'bpd_component': {
            'section_number': bpd_prov.get('section_number'),
            'section_title': bpd_prov.get('section_title'),
            'provision_text': bpd_prov.get('provision_text'),
            'provision_type': bpd_prov.get('provision_type'),
            'pdf_page': bpd_prov.get('pdf_page'),
            'provision_id': bpd_prov.get('provision_id')
        },

        'aa_components': [],

        'linkage': {
            'link_method': 'keyword_matching',
            'confidence': 0.0,
            'category': primary_category,
            'aa_match_count': len(aa_links)
        }
    }

    # Add AA components
    for link in aa_links:
        aa = link['aa_election']
        plan_provision['aa_components'].append({
            'question_id': aa.get('provision_id') or aa.get('section_number'),
            'section_number': aa.get('section_number'),
            'section_title': aa.get('section_title'),
            'provision_text': aa.get('provision_text'),
            'provision_type': aa.get('provision_type'),
            'pdf_page': aa.get('pdf_page'),
            'form_elements': aa.get('form_elements', []),
            'selected_values': aa.get('selected_values'),
            'link_confidence': link['confidence']
        })

    # Calculate overall linkage confidence
    if aa_links:
        avg_confidence = sum(link['confidence'] for link in aa_links) / len(aa_links)
        plan_provision['linkage']['confidence'] = round(avg_confidence, 2)

    # Semantic summary
    aa_count = len(aa_links)
    plan_provision['semantic_summary'] = (
        f"{primary_category.title()} provision combining BPD template with "
        f"{aa_count} related AA election form(s)"
    )

    return plan_provision

def create_all_plan_provisions(vendor: str, bpd_path: str, aa_path: str, output_path: str):
    """
    Create all Plan Provisions for a vendor.

    Args:
        vendor: "Relius" or "Ascensus"
        bpd_path: Path to BPD provisions JSON
        aa_path: Path to AA elections JSON
        output_path: Path to save Plan Provisions JSON
    """

    print(f"\n{'='*60}")
    print(f"Creating Plan Provisions for {vendor}")
    print(f"{'='*60}")

    # Load data
    print(f"\nLoading BPD provisions from: {bpd_path}")
    bpd_provisions = load_json(bpd_path)
    print(f"  Loaded: {len(bpd_provisions)} BPD provisions")

    print(f"\nLoading AA elections from: {aa_path}")
    aa_elections = load_json(aa_path)
    print(f"  Loaded: {len(aa_elections)} AA elections")

    # Domain keywords for matching
    domain_keywords = {
        'eligibility': ['eligibility', 'eligible', 'conditions', 'entry', 'participate', 'participation'],
        'compensation': ['compensation', '415', 'w-2', 'wages', 'salary', 'pay', 'earnings'],
        'vesting': ['vesting', 'vested', 'forfeiture', 'forfeit', 'nonforfeitable'],
        'match': ['matching', 'match', 'qmac', 'elective', 'deferral'],
        'contribution': ['contribution', 'nonelective', 'profit sharing', 'employer', 'allocation'],
        'distribution': ['distribution', 'withdrawal', 'loan', 'hardship', 'rollover'],
        'top_heavy': ['top-heavy', 'top heavy', 'key employee'],
        'testing': ['adp', 'acp', 'coverage', 'test', 'testing', 'nondiscrimination'],
        'loan': ['loan', 'loans'],
        'hardship': ['hardship', 'financial hardship'],
    }

    # Create Plan Provisions
    print(f"\nCreating Plan Provisions (linking BPD provisions with AA elections)...")
    plan_provisions = []

    for idx, bpd_prov in enumerate(bpd_provisions, 1):
        # Find related AA elections
        aa_links = find_aa_elections_for_bpd(bpd_prov, aa_elections, domain_keywords)

        # Create Plan Provision
        plan_prov = create_plan_provision(bpd_prov, aa_links, vendor, idx)
        plan_provisions.append(plan_prov)

        # Progress update
        if idx % 50 == 0:
            print(f"  Processed {idx}/{len(bpd_provisions)} BPD provisions...")

    print(f"  ✓ Created {len(plan_provisions)} Plan Provisions")

    # Calculate statistics
    if not plan_provisions:
        print("\n⚠️  WARNING: No plan provisions were created!")
        print("   Check that BPD and AA files are in the correct format.")
        return

    total_aa_links = sum(len(pp['aa_components']) for pp in plan_provisions)
    provisions_with_links = sum(1 for pp in plan_provisions if pp['aa_components'])
    avg_links = total_aa_links / len(plan_provisions)

    print(f"\nStatistics:")
    print(f"  Total BPD provisions: {len(bpd_provisions)}")
    print(f"  Total AA elections available: {len(aa_elections)}")
    print(f"  Plan Provisions created: {len(plan_provisions)}")
    print(f"  Provisions with AA links: {provisions_with_links} ({provisions_with_links/len(plan_provisions)*100:.1f}%)")
    print(f"  Total AA links created: {total_aa_links}")
    print(f"  Average AA links per provision: {avg_links:.2f}")

    # Category breakdown
    category_counts = {}
    for pp in plan_provisions:
        cat = pp['provision_category']
        category_counts[cat] = category_counts.get(cat, 0) + 1

    print(f"\nCategory breakdown:")
    for cat, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {cat:20s}: {count:4d} ({count/len(plan_provisions)*100:.1f}%)")

    # Save output
    output = {
        'metadata': {
            'phase': 'Phase 1 - Plan Provisions (Full Corpus)',
            'vendor': vendor,
            'total_plan_provisions': len(plan_provisions),
            'total_bpd_provisions': len(bpd_provisions),
            'total_aa_elections': len(aa_elections),
            'completeness': 'template',
            'linkage_method': 'keyword_matching'
        },
        'plan_provisions': plan_provisions
    }

    print(f"\nSaving to: {output_path}")
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"  ✓ Saved successfully")
    print(f"\n{'='*60}\n")

def main():
    """Main entry point."""

    # Paths
    base_dir = Path(__file__).parent.parent

    # Relius paths (BPD from v4.1, AA from v5.1)
    relius_bpd = base_dir / "test_data/extracted_vision_v4.1/relius_bpd_provisions.json"
    relius_aa = base_dir / "test_data/extracted_vision_v5.1/relius_aa_provisions.json"
    relius_output = base_dir / "test_data/plan_provisions/relius_plan_provisions_full.json"

    # Ascensus paths (BPD from v4.1, AA from v5.1)
    ascensus_bpd = base_dir / "test_data/extracted_vision_v4.1/ascensus_bpd_provisions.json"
    ascensus_aa = base_dir / "test_data/extracted_vision_v5.1/ascensus_aa_provisions.json"
    ascensus_output = base_dir / "test_data/plan_provisions/ascensus_plan_provisions_full.json"

    # Create output directory
    (base_dir / "test_data/plan_provisions").mkdir(parents=True, exist_ok=True)

    # Create Plan Provisions for both vendors
    create_all_plan_provisions("Relius", str(relius_bpd), str(relius_aa), str(relius_output))
    create_all_plan_provisions("Ascensus", str(ascensus_bpd), str(ascensus_aa), str(ascensus_output))

    print("="*60)
    print("COMPLETE: All Plan Provisions created")
    print("="*60)
    print("\nNext step: Run full crosswalk")
    print("  python scripts/run_full_crosswalk.py")
    print()

if __name__ == "__main__":
    main()
