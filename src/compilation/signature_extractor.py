"""
Signature Extractor - Discovers structural patterns from elections

Replaces brittle lookup table with runtime pattern discovery.
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple
from collections import Counter

class SignatureExtractor:
    """Extracts structural signatures from AA elections."""

    def __init__(self, schema_dir: str = "schemas/ceo"):
        """Initialize with dimension lexicon."""
        self.schema_dir = Path(schema_dir)

        # Load dimension lexicon
        with open(self.schema_dir / "ceo.dimension_lexicon.json") as f:
            lexicon = json.load(f)
            self.contribution_type_lexicon = lexicon.get("contribution_type_lexicon", {})

        # Build reverse lookup (phrase → canonical type)
        self.contrib_phrase_to_type = {}
        for ctype, phrases in self.contribution_type_lexicon.items():
            for phrase in phrases:
                self.contrib_phrase_to_type[phrase.lower()] = ctype

    def extract_signature(self, election: Dict) -> Dict:
        """Extract structural signature from election.

        Args:
            election: v5.2 extraction JSON

        Returns:
            Structural signature matching schema
        """
        # 1) Controls
        controls = self._count_controls(election)

        # 2) Shape inference
        shape = self._infer_shape(election, controls)

        # 3) Dimension hits
        dimension_hits = {
            "contribution_type": self._detect_contribution_types(election),
            "participant_class": self._detect_participant_classes(election)
        }

        # 4) Value & unit hints
        value_hints, unit_hints, numeric_literals = self._detect_value_units_and_numbers(election)

        # 5) Constraints hints
        constraints_hints = self._detect_constraints_hints(election, numeric_literals)

        # 6) Dependencies
        dependency_hints = self._detect_dependencies(election)

        # 7) Hierarchy
        hierarchy = self._infer_hierarchy(election.get("section_path", ""))

        # 8) Label tokens for LabelSim
        label_tokens = self._normalize_tokens(election)

        return {
            "shape": shape,
            "controls": controls,
            "option_count": len(election.get("options", [])),
            "has_other_option": self._has_other_option(election),
            "has_any_fill_ins": self._has_any_fill_ins(election),
            "fill_in_kinds": self._infer_fill_in_kinds(election),
            "dimension_hits": dimension_hits,
            "value_hints": list(value_hints),
            "numeric_literals": numeric_literals,
            "unit_hints": list(unit_hints),
            "constraints_hints": constraints_hints,
            "dependency_hints": dependency_hints,
            "hierarchy": hierarchy,
            "label_tokens": label_tokens
        }

    def _count_controls(self, election: Dict) -> Dict[str, int]:
        """Count form elements by type."""
        form_elements = election.get("form_elements", [])
        counts = Counter(fe.get("element_type", "unknown") for fe in form_elements)
        return {
            "checkbox": counts.get("checkbox", 0),
            "text": counts.get("text", 0) + counts.get("textbox", 0),
            "radio": counts.get("radio", 0),
            "grid": counts.get("grid", 0)
        }

    def _infer_shape(self, election: Dict, controls: Dict) -> str:
        """Infer structural shape from election."""
        question_text = election.get("question_text", "").lower()
        options = election.get("options", [])
        kind = election.get("kind", "")

        # scalar_numeric (Age 21, not to exceed 1000, etc.) - check first
        if any(num_word in question_text for num_word in ["age 21", "age ___", "not to exceed", "not more than"]):
            # Check if options are contribution types (applies-to checkboxes)
            contrib_types = self._detect_contribution_types(election)
            if len(contrib_types) > 1 and len(options) > 0:
                return "scalar_numeric"  # Age 21 with applies-to checkboxes
            return "scalar_numeric"

        # text_block
        if not controls["checkbox"] and not controls["text"] and not controls["radio"] and not options:
            return "text_block"

        # scalar_boolean
        if (controls["checkbox"] == 1 or controls["radio"] == 2) and not options:
            return "scalar_boolean"
        if len(options) == 2 and any(opt.get("option_text", "").lower() in ["yes", "no"] for opt in options):
            return "scalar_boolean"

        # scalar_numeric (Age 21, not to exceed 1000, etc.)
        if any(num_word in question_text for num_word in ["age 21", "age ___", "not to exceed", "not more than"]):
            return "scalar_numeric"
        if controls["text"] == 1 and not options:
            return "scalar_numeric"

        # menu_plus_other
        if self._has_other_option(election):
            return "menu_plus_other"

        # array_by_dimension (per-type rows)
        contrib_types = self._detect_contribution_types(election)
        if len(contrib_types) > 1:
            # Check if each option has its own checkbox/text (array structure)
            if controls["checkbox"] >= len(contrib_types) or controls["text"] >= len(contrib_types):
                return "array_by_dimension"

        # toggle_plus_detail
        if "same for all" in question_text or "different" in question_text:
            return "toggle_plus_detail"

        # schedule_grid
        if "year" in question_text and ("percent" in question_text or "vesting" in question_text):
            return "schedule_grid"

        # checklist (multi-select)
        if election.get("kind") == "multi_select":
            return "checklist"

        # menu (single-select)
        if election.get("kind") == "single_select" or controls["radio"] > 0:
            return "menu"

        # Default fallback
        return "menu" if options else "text_block"

    def _detect_contribution_types(self, election: Dict) -> List[str]:
        """Detect contribution types mentioned in election."""
        # Collect all text from election
        text_sources = [
            election.get("question_text", ""),
            election.get("section_context", "")
        ]
        for opt in election.get("options", []):
            text_sources.append(opt.get("option_text", ""))

        combined_text = " ".join(text_sources).lower()

        # Match against lexicon
        detected = set()
        for phrase, ctype in self.contrib_phrase_to_type.items():
            if phrase in combined_text:
                detected.add(ctype)

        return sorted(detected)

    def _detect_participant_classes(self, election: Dict) -> List[str]:
        """Detect participant classes mentioned in election."""
        # Simple keyword matching for now
        text = " ".join([
            election.get("question_text", ""),
            election.get("section_context", ""),
            *[opt.get("option_text", "") for opt in election.get("options", [])]
        ]).lower()

        classes = []
        keywords = {
            "salaried": ["salaried"],
            "hourly": ["hourly"],
            "part_time": ["part time", "part-time"],
            "seasonal": ["seasonal"],
            "temporary": ["temporary"],
            "leased": ["leased"],
            "nonresident_alien": ["nonresident alien"],
            "collectively_bargained": ["collectively bargained", "union"],
            "highly_compensated": ["highly compensated", "hce"],
            "non_highly_compensated": ["non-highly compensated", "non hce", "nhce"]
        }

        for pclass, phrases in keywords.items():
            if any(phrase in text for phrase in phrases):
                classes.append(pclass)

        return classes

    def _detect_value_units_and_numbers(self, election: Dict) -> Tuple[Set[str], Set[str], List[float]]:
        """Detect value hints, unit hints, and extract numeric literals."""
        text = " ".join([
            election.get("question_text", ""),
            *[opt.get("option_text", "") for opt in election.get("options", [])]
        ]).lower()

        value_hints = set()
        unit_hints = set()
        numeric_literals = []

        # Value hints
        if "age" in text:
            value_hints.add("age_years")
            unit_hints.add("years")
        if "hour" in text:
            value_hints.add("hours")
            unit_hints.add("hours")
        if "%" in text or "percent" in text:
            value_hints.add("percent")
            unit_hints.add("percent")
        if "$" in text or "dollar" in text:
            value_hints.add("dollars")
            unit_hints.add("dollars")
        if "date" in text:
            value_hints.add("date")
        if "vesting" in text and "year" in text:
            value_hints.add("schedule")

        # Extract numeric literals
        numbers = re.findall(r'\b(\d+(?:,\d{3})*(?:\.\d+)?)\b', text)
        for num_str in numbers:
            try:
                num = float(num_str.replace(",", ""))
                numeric_literals.append(num)
            except:
                pass

        return value_hints, unit_hints, numeric_literals

    def _detect_constraints_hints(self, election: Dict, numeric_literals: List[float]) -> Dict:
        """Detect constraint hints from text."""
        text = " ".join([
            election.get("question_text", ""),
            *[opt.get("option_text", "") for opt in election.get("options", [])]
        ]).lower()

        constraints = {
            "max_implied": None,
            "min_implied": None,
            "not_to_exceed": None
        }

        # "not to exceed N" or "not more than N"
        match = re.search(r'not (?:to exceed|more than)\s+(\d+(?:,\d{3})*)', text)
        if match:
            constraints["not_to_exceed"] = float(match.group(1).replace(",", ""))
            constraints["max_implied"] = constraints["not_to_exceed"]

        # "Age 21" line implies max=21
        if "age 21" in text:
            constraints["max_implied"] = 21

        # Extract first number as implied max if only one number present
        if len(numeric_literals) == 1 and constraints["max_implied"] is None:
            constraints["max_implied"] = numeric_literals[0]

        return constraints

    def _detect_dependencies(self, election: Dict) -> Dict:
        """Detect dependency hints."""
        text = election.get("question_text", "").lower()

        return {
            "select_one": "select one" in text,
            "select_all_apply": "select all" in text or "all that apply" in text,
            "has_parent_toggle": "same for all" in text or "different" in text
        }

    def _infer_hierarchy(self, section_path: str) -> Dict:
        """Infer hierarchy from section path."""
        if not section_path:
            return {"depth": 0, "path_suffix_kind": "UNK"}

        # Count depth
        parts = section_path.split(".")
        depth = len(parts)

        # Detect numbering pattern
        if re.match(r'^\d+$', parts[-1]):
            path_suffix_kind = "numbered"
        elif re.match(r'^[a-z]$', parts[-1], re.IGNORECASE):
            path_suffix_kind = "lettered"
        else:
            path_suffix_kind = "UNK"

        return {"depth": depth, "path_suffix_kind": path_suffix_kind}

    def _normalize_tokens(self, election: Dict) -> List[str]:
        """Extract and normalize tokens for LabelSim."""
        text = " ".join([
            election.get("section_context", ""),
            election.get("question_text", ""),
            *[opt.get("option_text", "") for opt in election.get("options", [])]
        ])

        # Tokenize and normalize
        tokens = re.findall(r'\b[a-z]+\b', text.lower())

        # Remove stop words
        stop_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by"}
        tokens = [t for t in tokens if t not in stop_words and len(t) > 2]

        return tokens[:50]  # Limit to 50 tokens

    def _has_other_option(self, election: Dict) -> bool:
        """Check if election has 'Other' option."""
        options = election.get("options", [])
        return any("other" in opt.get("option_text", "").lower() for opt in options)

    def _has_any_fill_ins(self, election: Dict) -> bool:
        """Check if election has any fill-in fields."""
        options = election.get("options", [])
        return any(opt.get("fill_ins") for opt in options)

    def _infer_fill_in_kinds(self, election: Dict) -> List[str]:
        """Infer types of fill-in fields."""
        text = " ".join([
            election.get("question_text", ""),
            *[opt.get("option_text", "") for opt in election.get("options", [])]
        ]).lower()

        kinds = []
        if "$" in text or "dollar" in text:
            kinds.append("currency")
        if "%" in text or "percent" in text:
            kinds.append("percent")
        if "date" in text:
            kinds.append("date")
        if "___" in text or re.search(r'\d+', text):
            kinds.append("number")
        if not kinds:
            kinds.append("text")

        return kinds


if __name__ == "__main__":
    # Test on Relius Age 21
    import json

    extractor = SignatureExtractor()

    # Load test election
    with open("test_data/extracted/relius_aa_elections.json") as f:
        data = json.load(f)
        elections = data['aas']

    # Find Age 21
    age_21 = [e for e in elections if e.get('question_number') == '1.03'][0]

    print("🧪 Testing Signature Extractor on Relius Age 21")
    print("=" * 80)

    sig = extractor.extract_signature(age_21)

    print("\n✅ Extracted signature:")
    print(json.dumps(sig, indent=2))

    # Validate expected values
    assert sig['shape'] == 'scalar_numeric', f"Expected scalar_numeric, got {sig['shape']}"
    assert 'pretax' in sig['dimension_hits']['contribution_type'] or 'matching' in sig['dimension_hits']['contribution_type'], "Expected contribution types detected"
    assert 'age_years' in sig['value_hints'], "Expected age_years hint"
    assert sig['constraints_hints']['max_implied'] == 21, "Expected max=21"

    print("\n✅ All assertions passed!")
