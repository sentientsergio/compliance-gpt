"""
CEO Compiler v2 - Discovery-First Architecture

Replaces lookup-table approach with runtime pattern discovery.
Uses structural signatures + generic operators instead of per-vendor variants.
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from collections import Counter

from signature_extractor import SignatureExtractor


class CEOCompilerV2:
    """Discovery-first compiler with generic operators."""

    def __init__(self, schema_dir: str = "schemas/ceo"):
        """Initialize compiler with CEO artifacts."""
        self.schema_dir = Path(schema_dir)

        # Load artifacts
        self.taxonomy = self._load_json("ceo.taxonomy.json")
        self.operators = self._load_json("ceo.operators.json")
        self.scoring_config = self._load_json("ceo.match_scoring.v0.2.json")

        # Initialize signature extractor
        self.sig_extractor = SignatureExtractor(schema_dir)

        # Build indexes
        self._build_indexes()

        # Metrics
        self.metrics = {
            "total_elections": 0,
            "by_domain": Counter(),
            "compile_success": 0,
            "compile_failure": 0,
            "unknown_field": 0,
            "unknown_shape": 0,
            "operators_used": Counter(),
            "novel_dimension_tokens": Counter(),
            "signature_families": Counter()
        }

    def _load_json(self, filename: str) -> Dict:
        """Load JSON artifact."""
        path = self.schema_dir / filename
        with open(path, 'r') as f:
            return json.load(f)

    def _build_indexes(self):
        """Build lookup indexes."""
        # Index fields by domain
        self.fields_by_domain = {}
        for field in self.taxonomy['fields']:
            domain = field['domain']
            if domain not in self.fields_by_domain:
                self.fields_by_domain[domain] = []
            self.fields_by_domain[domain].append(field)

        # Index by value_type for fast matching
        self.fields_by_value_type = {}
        for field in self.taxonomy['fields']:
            vtype = field['value_type']
            if vtype not in self.fields_by_value_type:
                self.fields_by_value_type[vtype] = []
            self.fields_by_value_type[vtype].append(field)

    def compile(self, election: Dict) -> Tuple[List[Dict], float, Dict]:
        """Compile election to canonical nodes.

        Args:
            election: v5.2 extraction JSON

        Returns:
            (canonical_nodes, confidence, signature)
        """
        self.metrics["total_elections"] += 1

        try:
            # 1) Extract structural signature
            sig = self.sig_extractor.extract_signature(election)

            # Track signature family
            sig_family = f"{sig['shape']}+{len(sig['dimension_hits']['contribution_type'])}contrib"
            self.metrics["signature_families"][sig_family] += 1

            # 2) Infer domain
            domain = self._infer_domain(election, sig)
            self.metrics["by_domain"][domain] += 1

            # 3) Find canonical field candidates
            candidates = self._find_canonical_candidates(domain, sig, election)

            if not candidates:
                self.metrics["unknown_field"] += 1
                self.metrics["compile_failure"] += 1
                return [], 0.0, sig

            # 4) Choose best canonical field
            canonical_field = self._choose_best_canonical(candidates, sig)

            # 5) Apply operators to generate nodes
            nodes = self._apply_operators(election, sig, canonical_field)

            # 6) Calculate confidence
            confidence = self._calculate_confidence(sig, canonical_field, nodes)

            self.metrics["compile_success"] += 1
            return nodes, confidence, sig

        except Exception as e:
            self.metrics["compile_failure"] += 1
            return [], 0.0, {}

    def _infer_domain(self, election: Dict, sig: Dict) -> str:
        """Infer domain from election context."""
        text = " ".join([
            election.get("section_context", ""),
            election.get("question_text", "")
        ]).lower()

        # Priority order matching
        if any(word in text for word in ["eligibility", "entry", "age"]):
            return "eligibility"
        if any(word in text for word in ["vesting", "years of service"]):
            return "vesting"
        if any(word in text for word in ["matching", "safe harbor", "qaca", "contribution"]):
            return "contributions"
        if "loan" in text:
            return "loans"
        if any(word in text for word in ["hardship", "in-service", "in service", "rmd", "distribution"]):
            return "distributions"

        # Default fallback
        return "eligibility"

    def _find_canonical_candidates(self, domain: str, sig: Dict, election: Dict) -> List[Dict]:
        """Find candidate canonical fields."""
        candidates = []

        # Get all fields in domain
        domain_fields = self.fields_by_domain.get(domain, [])

        for field in domain_fields:
            score = self._score_field_match(field, sig, election)
            if score > 0.3:  # Threshold
                candidates.append({"field": field, "score": score})

        # Sort by score
        candidates.sort(key=lambda x: x["score"], reverse=True)
        return candidates

    def _score_field_match(self, field: Dict, sig: Dict, election: Dict) -> float:
        """Score how well field matches signature."""
        score = 0.0

        # Value type match (25% weight)
        if self._value_types_compatible(field['value_type'], sig.get('value_hints', [])):
            score += 0.25

        # Unit match (15% weight)
        if field['units'] in sig.get('unit_hints', []) or field['units'] == 'N/A':
            score += 0.15

        # Label similarity (30% weight)
        label_sim = self._label_similarity(field, sig)
        score += 0.30 * label_sim

        # Dimension match (20% weight)
        if len(sig['dimension_hits']['contribution_type']) > 0:
            if 'contribution_type' in field.get('applies_to_dimensions', []):
                score += 0.20

        # Constraint compatibility (10% weight)
        if self._constraints_compatible(field, sig):
            score += 0.10

        return score

    def _value_types_compatible(self, field_vtype: str, value_hints: List[str]) -> bool:
        """Check if value types are compatible."""
        # Map hints to value types
        hint_to_type = {
            "age_years": "integer",
            "hours": "integer",
            "percent": "percentage",
            "dollars": "currency",
            "date": "string",
            "schedule": "schedule"
        }

        for hint in value_hints:
            expected_type = hint_to_type.get(hint)
            if expected_type == field_vtype:
                return True
            # Numeric compatibility
            if field_vtype in ["integer", "decimal"] and expected_type in ["integer", "decimal"]:
                return True

        return False

    def _label_similarity(self, field: Dict, sig: Dict) -> float:
        """Calculate label similarity (char trigrams)."""
        # Get field tokens
        field_tokens = set()
        for word in field['canonical_field'].split('.'):
            field_tokens.add(word.lower())
        for syn in field.get('vendor_synonyms', []):
            for word in syn.lower().split():
                field_tokens.add(word)

        # Get signature tokens
        sig_tokens = set(sig.get('label_tokens', []))

        # Jaccard similarity
        if not field_tokens or not sig_tokens:
            return 0.0

        intersection = len(field_tokens & sig_tokens)
        union = len(field_tokens | sig_tokens)

        return intersection / union if union > 0 else 0.0

    def _constraints_compatible(self, field: Dict, sig: Dict) -> bool:
        """Check if constraints are compatible."""
        field_constraints = field.get('constraints', {})
        sig_constraints = sig.get('constraints_hints', {})

        # Check max
        field_max = field_constraints.get('max')
        sig_max = sig_constraints.get('max_implied')

        if field_max and sig_max:
            return sig_max <= field_max

        return True  # Compatible if no constraints to check

    def _choose_best_canonical(self, candidates: List[Dict], sig: Dict) -> Dict:
        """Choose best canonical field from candidates."""
        if not candidates:
            return None

        # Return highest scoring
        return candidates[0]['field']

    def _apply_operators(self, election: Dict, sig: Dict, canonical_field: Dict) -> List[Dict]:
        """Apply generic operators to generate canonical nodes."""
        shape = sig['shape']
        canonical = canonical_field['canonical_field']

        # Operator: replicate_across_dimension
        if shape == "scalar_numeric" and len(sig['dimension_hits']['contribution_type']) > 1:
            self.metrics["operators_used"]["replicate_across_dimension"] += 1
            return self._replicate_across_dimension(election, sig, canonical_field)

        # Operator: bind_dimension_value
        if shape == "array_by_dimension":
            self.metrics["operators_used"]["bind_dimension_value"] += 1
            return self._bind_dimension_value(election, sig, canonical_field)

        # Operator: gate_by_toggle
        if shape == "toggle_plus_detail":
            self.metrics["operators_used"]["gate_by_toggle"] += 1
            return self._gate_by_toggle(election, sig, canonical_field)

        # Operator: aggregate_or_cap
        if any(h in sig.get('value_hints', []) for h in ["percent", "dollars"]):
            if any(token in sig.get('label_tokens', []) for token in ["maximum", "cap", "exceed"]):
                self.metrics["operators_used"]["aggregate_or_cap"] += 1
                return self._aggregate_or_cap(election, sig, canonical_field)

        # Default: single node
        return [self._create_canonical_node(election, sig, canonical_field)]

    def _replicate_across_dimension(self, election: Dict, sig: Dict, field: Dict) -> List[Dict]:
        """Replicate scalar value across contribution types."""
        nodes = []
        contrib_types = sig['dimension_hits']['contribution_type']

        for ctype in contrib_types:
            node = self._create_canonical_node(election, sig, field)
            node['dimension_values'] = {"contribution_type": ctype}
            nodes.append(node)

        return nodes

    def _bind_dimension_value(self, election: Dict, sig: Dict, field: Dict) -> List[Dict]:
        """Bind dimension value for per-type rows."""
        nodes = []
        contrib_types = sig['dimension_hits']['contribution_type']

        # Each option represents a different contribution type
        options = election.get('options', [])
        for i, opt in enumerate(options):
            if i < len(contrib_types):
                node = self._create_canonical_node(election, sig, field)
                node['dimension_values'] = {"contribution_type": contrib_types[i]}
                node['provenance']['option_text'] = opt.get('option_text', '')
                nodes.append(node)

        return nodes

    def _gate_by_toggle(self, election: Dict, sig: Dict, field: Dict) -> List[Dict]:
        """Create dependency bundle for toggle."""
        node = self._create_canonical_node(election, sig, field)
        node['dependency_bundle'] = {
            "parent": election.get('id'),
            "required_children": ["detail_elections"]  # Would be resolved later
        }
        return [node]

    def _aggregate_or_cap(self, election: Dict, sig: Dict, field: Dict) -> List[Dict]:
        """Normalize to max/cap field."""
        # Force canonical to .max variant if exists
        canonical = field['canonical_field']
        if not canonical.endswith('.max'):
            # Try to find .max variant
            base = canonical.rsplit('.', 1)[0] if '.' in canonical else canonical
            max_field = f"{base}.max"
            # Would look up in taxonomy, for now just use as-is

        return [self._create_canonical_node(election, sig, field)]

    def _create_canonical_node(self, election: Dict, sig: Dict, field: Dict) -> Dict:
        """Create a canonical node."""
        return {
            "canonical_field": field['canonical_field'],
            "field_type": self._map_shape_to_field_type(sig['shape']),
            "value_type": field['value_type'],
            "units": field['units'],
            "constraints": self._finalize_constraints(sig, field),
            "applies_to_dimensions": field.get('applies_to_dimensions', []),
            "dimension_values": {},
            "dependency_bundle": {
                "parent": None,
                "required_children": []
            },
            "provenance": {
                "vendor": "unknown",
                "section_path": election.get('section_path', election.get('id', '')),
                "section_context": election.get('section_context', ''),
                "question_number": election.get('question_number', ''),
                "evidence": election.get('question_text', '')[:200]
            },
            "signature": sig
        }

    def _map_shape_to_field_type(self, shape: str) -> str:
        """Map shape to field type."""
        mapping = {
            "scalar_boolean": "checkbox",
            "scalar_numeric": "text",
            "menu": "radio",
            "checklist": "checkboxes",
            "menu_plus_other": "combo",
            "array_by_dimension": "grid",
            "toggle_plus_detail": "radio",
            "schedule_grid": "grid",
            "text_block": "text"
        }
        return mapping.get(shape, "text")

    def _finalize_constraints(self, sig: Dict, field: Dict) -> Dict:
        """Finalize constraints from hints + field."""
        constraints = {}

        # Merge field constraints
        field_constraints = field.get('constraints', {})
        for key in ['min', 'max', 'step', 'allowed_enums']:
            if key in field_constraints:
                constraints[key] = field_constraints[key]

        # Apply signature hints
        sig_constraints = sig.get('constraints_hints', {})
        if sig_constraints.get('max_implied') is not None:
            constraints['max'] = sig_constraints['max_implied']
        if sig_constraints.get('min_implied') is not None:
            constraints['min'] = sig_constraints['min_implied']

        return constraints

    def _calculate_confidence(self, sig: Dict, field: Dict, nodes: List[Dict]) -> float:
        """Calculate compilation confidence."""
        # High confidence when:
        # - Shape is deterministic (not text_block)
        # - Value type matches
        # - Domain clear
        # - Operators applied successfully

        confidence = 0.5  # Base

        if sig['shape'] != 'text_block':
            confidence += 0.2

        if self._value_types_compatible(field['value_type'], sig.get('value_hints', [])):
            confidence += 0.2

        if len(nodes) > 0:
            confidence += 0.1

        return min(confidence, 1.0)

    def compile_batch(self, elections: List[Dict]) -> List[Tuple[List[Dict], float, Dict]]:
        """Compile multiple elections."""
        results = []
        for election in elections:
            nodes, confidence, sig = self.compile(election)
            results.append((nodes, confidence, sig))
        return results

    def print_metrics(self):
        """Print compilation metrics."""
        print("\n" + "="*80)
        print("CEO Compiler v2 - Discovery Metrics")
        print("="*80)

        total = self.metrics["total_elections"]
        success = self.metrics["compile_success"]
        failure = self.metrics["compile_failure"]

        print(f"\n📊 Overall:")
        print(f"   Total elections: {total}")
        print(f"   Compile success: {success} ({success/total*100:.1f}%)")
        print(f"   Compile failure: {failure} ({failure/total*100:.1f}%)")
        print(f"   Unknown field: {self.metrics['unknown_field']}")
        print(f"   Unknown shape: {self.metrics['unknown_shape']}")

        print(f"\n🏷️  By Domain:")
        for domain, count in self.metrics["by_domain"].most_common():
            print(f"   {domain}: {count} ({count/total*100:.1f}%)")

        print(f"\n⚙️  Operators Used:")
        for op, count in self.metrics["operators_used"].most_common():
            print(f"   {op}: {count}")

        print(f"\n📐 Top 10 Signature Families:")
        for sig_family, count in self.metrics["signature_families"].most_common(10):
            print(f"   {sig_family}: {count}")

        print("\n" + "="*80)


if __name__ == "__main__":
    # Test on Age 21
    compiler = CEOCompilerV2()

    # Load test elections
    with open("test_data/extracted/relius_aa_elections.json") as f:
        data = json.load(f)
        elections = data['aas']

    # Test on Age 21
    age_21 = [e for e in elections if e.get('question_number') == '1.03'][0]

    print("🧪 Testing CEO Compiler v2 on Relius Age 21")
    print("=" * 80)

    nodes, confidence, sig = compiler.compile(age_21)

    print(f"\n✅ Compiled {len(nodes)} canonical nodes:")
    for i, node in enumerate(nodes, 1):
        print(f"\nNode {i}:")
        print(json.dumps(node, indent=2))

    print(f"\n📊 Confidence: {confidence:.2f}")

    print("\n" + "="*80)

    # Test on full corpus
    print("\n🚀 Running full corpus compilation...")
    results = compiler.compile_batch(elections)  # All elections

    compiler.print_metrics()

    # Show successful elections for analysis
    print("\n\n✅ Successful Elections Analysis:")
    print("=" * 80)
    success_count = 0
    for i, (nodes, confidence, sig) in enumerate(results):
        if nodes:
            success_count += 1
            if success_count <= 15:  # Show first 15 successes
                election = elections[i]
                canonical = nodes[0]['canonical_field']
                print(f"\n✅ Success: {election.get('question_number')} - {election.get('question_text', '')[:60]}")
                print(f"   → {canonical} (confidence: {confidence:.2f})")
                print(f"   Shape: {sig.get('shape')}, Nodes: {len(nodes)}")

    # Show failed elections for analysis
    print("\n\n🔍 Failed Elections Analysis:")
    print("=" * 80)
    failed_count = 0
    for i, (nodes, confidence, sig) in enumerate(results):
        if not nodes:
            failed_count += 1
            if failed_count <= 10:  # Show first 10 failures
                election = elections[i]
                print(f"\n❌ Failed: {election.get('question_number')} - {election.get('question_text', '')[:80]}")
                print(f"   Shape: {sig.get('shape', 'unknown')}")
                print(f"   Dimensions: {sig.get('dimension_hits', {})}")
                print(f"   Domain inferred: {compiler._infer_domain(election, sig)}")
    print(f"\n   ... and {failed_count - 10} more failures" if failed_count > 10 else "")
