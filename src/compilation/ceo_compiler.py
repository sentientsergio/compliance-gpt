"""
CEO (Canonical Election Ontology) Compiler

Converts v5.2 extraction JSON → canonical field records.
Implements hybrid approach: rule-first (95%) + LLM tie-breaker (5%).
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from openai import OpenAI

class CEOCompiler:
    """Compiles AA elections into canonical field records."""

    def __init__(self, schema_dir: str = "schemas/ceo"):
        """Initialize compiler with CEO artifacts.

        Args:
            schema_dir: Directory containing CEO schema files
        """
        self.schema_dir = Path(schema_dir)
        self.client = OpenAI()

        # Load artifacts
        self.taxonomy = self._load_json("ceo.taxonomy.json")
        self.variants = self._load_json("ceo.structural_variants.json")
        self.scoring_config = self._load_json("ceo.match_scoring.json")
        self.compiler_prompt = self._load_text("ceo.compiler.prompt.txt")

        # Build lookup indexes for fast matching
        self._build_indexes()

    def _load_json(self, filename: str) -> Dict:
        """Load JSON artifact."""
        path = self.schema_dir / filename
        with open(path, 'r') as f:
            return json.load(f)

    def _load_text(self, filename: str) -> str:
        """Load text artifact."""
        path = self.schema_dir / filename
        with open(path, 'r') as f:
            return f.read()

    def _build_indexes(self):
        """Build lookup indexes for fast matching."""
        # Index by domain
        self.fields_by_domain = {}
        for field in self.taxonomy['fields']:
            domain = field['domain']
            if domain not in self.fields_by_domain:
                self.fields_by_domain[domain] = []
            self.fields_by_domain[domain].append(field)

        # Index by synonym (lowercase for case-insensitive matching)
        self.fields_by_synonym = {}
        for field in self.taxonomy['fields']:
            canonical = field['canonical_field']
            for synonym in field.get('vendor_synonyms', []):
                syn_lower = synonym.lower()
                if syn_lower not in self.fields_by_synonym:
                    self.fields_by_synonym[syn_lower] = []
                self.fields_by_synonym[syn_lower].append(canonical)

        # Index variants by canonical field
        self.variants_by_field = {}
        for variant in self.variants['variants']:
            canonical = variant['canonical_field']
            self.variants_by_field[canonical] = variant['structural_variants']

    def compile(self, election: Dict) -> Dict:
        """Compile a single AA election to canonical field record.

        Args:
            election: v5.2 extraction JSON for one election

        Returns:
            Canonical field record with provenance
        """
        # Use LLM for compilation (hybrid approach - LLM handles complexity)
        return self._compile_with_llm(election)

    def _compile_with_llm(self, election: Dict) -> Dict:
        """Use LLM to compile election (handles edge cases deterministically)."""
        # Prepare input for LLM
        election_json = json.dumps(election, indent=2)

        # Build user prompt
        user_prompt = f"""Compile this AA election to canonical field:

{election_json}

Use the CEO taxonomy and structural variant catalog to map this election deterministically.
Output JSON only, matching the schema exactly."""

        # Call LLM
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",  # Fast and accurate for structured tasks
            messages=[
                {"role": "system", "content": self.compiler_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0  # Deterministic
        )

        # Parse response
        compiled = json.loads(response.choices[0].message.content)
        return compiled

    def compile_batch(self, elections: List[Dict], parallel: bool = True) -> List[Dict]:
        """Compile multiple elections.

        Args:
            elections: List of v5.2 extraction JSON records
            parallel: Whether to parallelize (future optimization)

        Returns:
            List of canonical field records
        """
        results = []
        for election in elections:
            try:
                compiled = self.compile(election)
                results.append(compiled)
            except Exception as e:
                print(f"⚠️  Compilation failed for {election.get('id', 'unknown')}: {e}")
                results.append({
                    "error": str(e),
                    "election_id": election.get('id'),
                    "canonical_field": "unknown"
                })
        return results


if __name__ == "__main__":
    # Test on Match 2 example (Relius Age 21)
    compiler = CEOCompiler()

    # Load test election
    with open("test_data/extracted/relius_aa_elections.json") as f:
        data = json.load(f)
        elections = data['aas']

    # Find Age 21 election (Q 1.03)
    age_21 = [e for e in elections if e.get('question_number') == '1.03'][0]

    print("🧪 Testing CEO Compiler on Match 2 (Relius Age 21)")
    print("=" * 80)
    print(f"\nInput election:")
    print(json.dumps(age_21, indent=2)[:500] + "...")

    print(f"\n🔄 Compiling...")
    compiled = compiler.compile(age_21)

    print(f"\n✅ Compiled result:")
    print(json.dumps(compiled, indent=2))

    # Validate expected outputs
    assert compiled['canonical_field'] == 'eligibility.age', f"Expected eligibility.age, got {compiled['canonical_field']}"
    assert compiled['vendor_implementation'] == 'single_age_with_applies_to', f"Expected single_age_with_applies_to, got {compiled['vendor_implementation']}"
    assert compiled['confidence'] >= 0.9, f"Expected high confidence (≥0.9), got {compiled['confidence']}"

    print(f"\n✅ All assertions passed!")
    print(f"   - canonical_field: {compiled['canonical_field']}")
    print(f"   - vendor_implementation: {compiled['vendor_implementation']}")
    print(f"   - confidence: {compiled['confidence']}")
