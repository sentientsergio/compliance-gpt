#!/usr/bin/env python3
"""
Run Full Crosswalk on ALL Plan Provisions
Generates complete Relius → Ascensus mapping document
"""

import json
import os
from openai import OpenAI
from typing import List, Dict, Tuple
import numpy as np
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

def load_plan_provisions(filepath: str) -> List[Dict]:
    """Load Plan Provisions from JSON file."""
    with open(filepath, 'r') as f:
        data = json.load(f)
    return data.get('plan_provisions', [])

def build_embedding_text(provision: Dict) -> str:
    """
    Build semantic text for embedding generation.
    Combines BPD + AA context (template level, no values).
    """
    bpd = provision['bpd_component']
    aa_list = provision.get('aa_components', [])

    # Start with BPD text
    parts = [
        f"Category: {provision['provision_category']}",
        f"Section: {bpd.get('section_number', 'N/A')} - {bpd.get('section_title', 'N/A')}",
        f"BPD Text: {bpd.get('provision_text', '')}"
    ]

    # Add AA context (structure and options, no values)
    if aa_list:
        parts.append("Related Adoption Agreement Elections:")
        for aa in aa_list[:3]:  # Max 3 AA elections to keep embedding size reasonable
            aa_text = aa.get('provision_text', '')
            aa_section = aa.get('section_number', 'N/A')
            aa_title = aa.get('section_title', 'N/A')
            if aa_text:
                # Truncate long AA text
                aa_text_short = aa_text[:200] + "..." if len(aa_text) > 200 else aa_text
                parts.append(f"  AA {aa_section} ({aa_title}): {aa_text_short}")
            else:
                parts.append(f"  AA {aa_section} ({aa_title})")

    return "\n".join(parts)

def generate_embedding(text: str) -> List[float]:
    """Generate embedding using OpenAI text-embedding-3-small."""
    response = client.embeddings.create(
        input=text,
        model="text-embedding-3-small"
    )
    return response.data[0].embedding

def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """Calculate cosine similarity between two vectors."""
    a = np.array(vec1)
    b = np.array(vec2)
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def find_top_k_candidates(
    source_embedding: List[float],
    target_provisions: List[Dict],
    target_embeddings: List[List[float]],
    k: int = 5
) -> List[Tuple[int, float]]:
    """
    Find top-k most similar target provisions.
    Returns list of (index, similarity_score) tuples.
    """
    similarities = [
        (idx, cosine_similarity(source_embedding, target_emb))
        for idx, target_emb in enumerate(target_embeddings)
    ]
    # Sort by similarity descending
    similarities.sort(key=lambda x: x[1], reverse=True)
    return similarities[:k]

def verify_semantic_match(
    source_provision: Dict,
    target_provision: Dict,
    cosine_sim: float
) -> Dict:
    """
    Use LLM to verify if provisions are semantically equivalent.
    Returns match result with confidence and reasoning.
    """
    source_text = build_embedding_text(source_provision)
    target_text = build_embedding_text(target_provision)

    prompt = f"""You are a retirement plan compliance expert comparing provisions across vendor documents.

SOURCE PROVISION (Relius):
{source_text}

TARGET PROVISION (Ascensus):
{target_text}

COSINE SIMILARITY: {cosine_sim:.3f}

Task: Determine if these provisions are semantically equivalent.

Consider:
1. Do they govern the same plan feature/requirement?
2. Are the available options/elections comparable?
3. Would selecting the same semantic choice in each produce the same plan outcome?

Note: These are TEMPLATES - no values selected yet. Focus on structure and option space.

Respond in JSON format:
{{
  "is_match": true/false,
  "confidence": 0.0-1.0,
  "match_type": "exact" | "close" | "none",
  "reasoning": "brief explanation",
  "variance_notes": "key differences if close match"
}}
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        temperature=0.0
    )

    return json.loads(response.choices[0].message.content)

def process_source_provision(
    src_idx: int,
    source_prov: Dict,
    source_embedding: List[float],
    target_provisions: List[Dict],
    target_embeddings: List[List[float]],
    top_k: int = 3
) -> Dict:
    """Process a single source provision (for parallel execution)."""

    # Find top-k candidates
    candidates = find_top_k_candidates(
        source_embedding,
        target_provisions,
        target_embeddings,
        k=top_k
    )

    # Verify best candidate with LLM
    if candidates:
        best_idx, best_sim = candidates[0]
        best_target = target_provisions[best_idx]

        verification = verify_semantic_match(source_prov, best_target, best_sim)

        mapping = {
            "source_provision_id": source_prov['plan_provision_id'],
            "source_category": source_prov['provision_category'],
            "source_section": source_prov['bpd_component'].get('section_number'),
            "target_provision_id": best_target['plan_provision_id'],
            "target_category": best_target['provision_category'],
            "target_section": best_target['bpd_component'].get('section_number'),
            "cosine_similarity": best_sim,
            "llm_verification": verification,
            "all_candidates": [
                {
                    "target_provision_id": target_provisions[idx]['plan_provision_id'],
                    "cosine_similarity": sim
                }
                for idx, sim in candidates
            ]
        }

        return mapping
    else:
        return None

def generate_crosswalk(
    source_provisions: List[Dict],
    target_provisions: List[Dict],
    workers: int = 16
) -> Dict:
    """
    Generate complete crosswalk mapping document with parallel processing.
    """
    print(f"\n{'='*80}")
    print(f"FULL CROSSWALK: Relius → Ascensus")
    print(f"{'='*80}")
    print(f"Source provisions: {len(source_provisions)}")
    print(f"Target provisions: {len(target_provisions)}")
    print(f"Workers: {workers}")

    # Step 1: Generate embeddings for all provisions
    print(f"\nStep 1: Generating embeddings...")
    print(f"  Source embeddings...")
    source_embeddings = []
    for idx, prov in enumerate(source_provisions, 1):
        text = build_embedding_text(prov)
        emb = generate_embedding(text)
        source_embeddings.append(emb)
        if idx % 50 == 0:
            print(f"    {idx}/{len(source_provisions)} completed...")

    print(f"  Target embeddings...")
    target_embeddings = []
    for idx, prov in enumerate(target_provisions, 1):
        text = build_embedding_text(prov)
        emb = generate_embedding(text)
        target_embeddings.append(emb)
        if idx % 50 == 0:
            print(f"    {idx}/{len(target_provisions)} completed...")

    print(f"  ✓ Embeddings complete")

    # Step 2: Parallel crosswalk processing
    print(f"\nStep 2: Running semantic crosswalk (parallel processing)...")

    mappings = []
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {
            executor.submit(
                process_source_provision,
                idx,
                source_prov,
                source_embeddings[idx],
                target_provisions,
                target_embeddings,
                top_k=3
            ): idx
            for idx, source_prov in enumerate(source_provisions)
        }

        completed = 0
        for future in as_completed(futures):
            result = future.result()
            if result:
                mappings.append(result)
            completed += 1
            if completed % 50 == 0:
                print(f"    {completed}/{len(source_provisions)} provisions processed...")

    print(f"  ✓ Crosswalk complete: {len(mappings)} mappings generated")

    # Step 3: Identify unmapped provisions
    mapped_target_ids = {m['target_provision_id'] for m in mappings if m['llm_verification']['is_match']}
    unmapped_targets = [
        {
            "provision_id": prov['plan_provision_id'],
            "category": prov['provision_category'],
            "section": prov['bpd_component'].get('section_number'),
            "reason": "No semantic match found in source"
        }
        for prov in target_provisions
        if prov['plan_provision_id'] not in mapped_target_ids
    ]

    unmapped_sources = [
        {
            "provision_id": m['source_provision_id'],
            "category": m['source_category'],
            "section": m['source_section'],
            "reason": "No semantic match found in target"
        }
        for m in mappings
        if not m['llm_verification']['is_match']
    ]

    # Build final crosswalk document
    crosswalk = {
        "metadata": {
            "phase": "Phase 2 - Full Crosswalk",
            "source_vendor": "Relius",
            "target_vendor": "Ascensus",
            "source_provision_count": len(source_provisions),
            "target_provision_count": len(target_provisions),
            "mapping_method": "embeddings + LLM verification",
            "workers": workers,
            "generation_timestamp": datetime.now().isoformat()
        },
        "summary": {
            "exact_matches": sum(1 for m in mappings if m['llm_verification']['match_type'] == 'exact'),
            "close_matches": sum(1 for m in mappings if m['llm_verification']['match_type'] == 'close'),
            "no_matches": sum(1 for m in mappings if m['llm_verification']['match_type'] == 'none'),
            "unmapped_sources": len(unmapped_sources),
            "unmapped_targets": len(unmapped_targets),
            "total_mappings": len(mappings)
        },
        "mappings": mappings,
        "unmapped_sources": unmapped_sources,
        "unmapped_targets": unmapped_targets
    }

    return crosswalk

def main():
    """Main entry point."""

    # Paths
    base_dir = Path(__file__).parent.parent
    relius_path = base_dir / "test_data/plan_provisions/relius_plan_provisions_full.json"
    ascensus_path = base_dir / "test_data/plan_provisions/ascensus_plan_provisions_full.json"
    output_path = base_dir / "test_data/crosswalks/full_plan_provision_crosswalk.json"

    # Create output directory
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Load Plan Provisions
    print("Loading Plan Provisions...")
    relius_provisions = load_plan_provisions(str(relius_path))
    ascensus_provisions = load_plan_provisions(str(ascensus_path))
    print(f"  Relius: {len(relius_provisions)} Plan Provisions")
    print(f"  Ascensus: {len(ascensus_provisions)} Plan Provisions")

    # Generate crosswalk
    crosswalk = generate_crosswalk(relius_provisions, ascensus_provisions, workers=16)

    # Save results
    print(f"\nSaving crosswalk to: {output_path}")
    with open(output_path, 'w') as f:
        json.dump(crosswalk, f, indent=2)
    print(f"  ✓ Saved successfully")

    # Print summary
    print(f"\n{'='*80}")
    print("CROSSWALK SUMMARY")
    print(f"{'='*80}")
    print(f"\nMatches:")
    print(f"  Exact matches:    {crosswalk['summary']['exact_matches']:4d}")
    print(f"  Close matches:    {crosswalk['summary']['close_matches']:4d}")
    print(f"  No matches:       {crosswalk['summary']['no_matches']:4d}")
    print(f"\nUnmapped:")
    print(f"  Unmapped sources: {crosswalk['summary']['unmapped_sources']:4d} (Relius provisions without Ascensus equivalent)")
    print(f"  Unmapped targets: {crosswalk['summary']['unmapped_targets']:4d} (Ascensus provisions without Relius equivalent)")
    print(f"\nTotal mappings generated: {crosswalk['summary']['total_mappings']}")
    print(f"\n{'='*80}\n")

if __name__ == "__main__":
    main()
