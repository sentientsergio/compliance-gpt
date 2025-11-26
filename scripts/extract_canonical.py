#!/usr/bin/env python3
"""
Draft canonical extractor: map provision chunks to canonical fields.
Heuristic layer with optional semantic ranking via OpenAI embeddings.

Targets (initial):
- eligibility.age (deferrals/match/profit_sharing)
- eligibility.service (years/hours where obvious)
- eligibility.entry_dates (provenance only)
- retirement.normal_age (age or age+service)
- compensation.base_definition (text/provenance)
- compensation.exclusions (provenance)
- vesting.schedule (provenance only)
- loans.enabled (boolean + provenance)
- distributions.hardship (provenance only)
- distributions.in_service (provenance + optional age threshold)

Inputs:
- Provision JSON from scripts/segment_provisions.py
Outputs:
- Canonical JSON with populated fields and provenance
- Match report (stdout) listing matched/unmatched nodes
"""

import argparse
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    import openai  # type: ignore
except Exception:
    openai = None

USE_EMB = False
EMB_MODEL = "text-embedding-3-small"

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Heuristic canonical extraction from provision JSON.")
    parser.add_argument("--provisions", required=True, help="Path to provisions JSON (from segment_provisions).")
    parser.add_argument("--out", required=True, help="Output path for canonical JSON.")
    parser.add_argument("--doc-id", help="Override doc_id for output (defaults to provisions doc).")
    parser.add_argument(
        "--use-openai-embeddings",
        action="store_true",
        help="Enable semantic ranking with OpenAI embeddings (requires OPENAI_API_KEY).",
    )
    parser.add_argument(
        "--openai-model",
        default="text-embedding-3-small",
        help="OpenAI embedding model to use when --use-openai-embeddings is set.",
    )
    return parser.parse_args()


def load_provisions(path: Path) -> Tuple[str, List[Dict[str, Any]]]:
    data = json.loads(path.read_text())
    provisions = data.get("provisions", [])
    doc_id = data.get("provisions", [{}])[0].get("doc_id") if provisions else data.get("source_layout", path.stem)
    return doc_id or path.stem, provisions


def text_blob(prov: Dict[str, Any]) -> str:
    parts = [prov.get("title") or ""]
    for blk in prov.get("blocks", []):
        parts.append(blk.get("text") or "")
    for tbl in prov.get("tables", []):
        for row in tbl.get("rows", []):
            for cell in row.get("cells", []):
                parts.append(cell.get("text") or "")
    return " ".join(parts).lower()


def clean_for_embedding(text: str) -> str:
    text = re.sub(r"^[0-9.\\-\\s]+", "", text)
    return text


def score_provision(prov: Dict[str, Any], keywords: List[str]) -> int:
    blob = text_blob(prov)
    return sum(blob.count(k.lower()) for k in keywords)


def embed_texts(texts: List[str], model: str) -> List[List[float]]:
    client = openai.OpenAI()
    res = client.embeddings.create(model=model, input=texts)
    return [item.embedding for item in res.data]


def cosine(a: List[float], b: List[float]) -> float:
    import math

    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb + 1e-9)


def semantic_best(
    provisions: List[Dict[str, Any]],
    query: str,
    keywords: Optional[List[str]],
    use_embeddings: bool,
    model: str,
    title_keywords: Optional[List[str]] = None,
    top_k: int = 50,
) -> Optional[Dict[str, Any]]:
    pool = provisions
    if keywords:
        pool = [p for p in pool if any(k.lower() in text_blob(p) for k in keywords)]
    if title_keywords:
        pool = [p for p in pool if any(k.lower() in (p.get("title") or "").lower() for k in title_keywords)]
    if not pool:
        return None
    if use_embeddings and openai:
        texts = [clean_for_embedding(text_blob(p)) for p in pool[:top_k]]
        embeddings = embed_texts([query] + texts, model)
        query_emb = embeddings[0]
        prov_embs = embeddings[1:]
        scores = [(cosine(query_emb, emb), prov) for emb, prov in zip(prov_embs, pool[:top_k])]
        scores.sort(key=lambda x: x[0], reverse=True)
        return scores[0][1] if scores else None
    # fallback: keyword score
    return best_match(pool, keywords or [])


def best_match(provisions: List[Dict[str, Any]], keywords: List[str]) -> Optional[Dict[str, Any]]:
    scored = [(score_provision(p, keywords), p) for p in provisions]
    scored = [pair for pair in scored if pair[0] > 0]
    if not scored:
        return None
    scored.sort(key=lambda x: x[0], reverse=True)
    return scored[0][1]


def extract_int_in_range(text: str, min_val: int, max_val: int) -> Optional[int]:
    for m in re.finditer(r"\b(\d{1,3})\b", text):
        val = int(m.group(1))
        if min_val <= val <= max_val:
            return val
    return None


def provenance_from(prov: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "doc_id": prov.get("doc_id"),
        "provision_id": prov.get("provision_id"),
        "title": prov.get("title"),
        "page_range": prov.get("page_range"),
    }


def extract_eligibility_age(provisions: List[Dict[str, Any]]) -> Tuple[Optional[int], Optional[Dict[str, Any]]]:
    prov = semantic_best(
        provisions,
        "eligibility age requirement for plan participation",
        ["eligibility", "age"],
        USE_EMB,
        EMB_MODEL,
        title_keywords=["eligibility"],
    )
    if not prov:
        return None, None
    blob = text_blob(prov)
    age = extract_int_in_range(blob, 15, 75)
    return age, provenance_from(prov)


def extract_eligibility_service(provisions: List[Dict[str, Any]]) -> Tuple[Optional[int], Optional[int], Optional[Dict[str, Any]]]:
    prov = semantic_best(
        provisions,
        "eligibility service requirement",
        ["eligibility", "service"],
        USE_EMB,
        EMB_MODEL,
        title_keywords=["eligibility"],
    )
    if not prov:
        return None, None, None
    blob = text_blob(prov)
    years = extract_int_in_range(blob, 0, 5)
    hours = extract_int_in_range(blob, 500, 2000)
    return years, hours, provenance_from(prov)


def extract_entry_dates(provisions: List[Dict[str, Any]]) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
    prov = semantic_best(
        provisions,
        "plan entry dates for participation",
        ["entry", "participation"],
        USE_EMB,
        EMB_MODEL,
        title_keywords=["entry", "participation"],
    )
    if not prov:
        return None, None
    # Heuristic: look for patterns like monthly, quarterly, first of month
    blob = text_blob(prov)
    pattern = None
    for key, label in [
        ("monthly", "monthly"),
        ("quarter", "quarterly"),
        ("semi", "semi_annual"),
        ("annual", "annual"),
        ("payroll", "per_payroll"),
        ("first day", "first_of_period"),
    ]:
        if key in blob:
            pattern = label
            break
    return pattern, provenance_from(prov)


def extract_normal_retirement_age(provisions: List[Dict[str, Any]]) -> Tuple[Optional[int], Optional[int], Optional[Dict[str, Any]]]:
    prov = semantic_best(
        provisions,
        "normal retirement age definition",
        ["retirement"],
        USE_EMB,
        EMB_MODEL,
        title_keywords=["normal retirement"],
    )
    if not prov:
        return None, None, None
    blob = text_blob(prov)
    age = extract_int_in_range(blob, 50, 80)
    svc = extract_int_in_range(blob, 0, 10)
    return age, svc, provenance_from(prov)


def extract_comp_base(provisions: List[Dict[str, Any]]) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
    prov = semantic_best(
        provisions,
        "compensation base definition",
        ["compensation"],
        USE_EMB,
        EMB_MODEL,
        title_keywords=["compensation"],
    )
    if not prov:
        return None, None
    blob = text_blob(prov)
    definition = None
    if "w-2" in blob:
        definition = "W2"
    elif "3401" in blob:
        definition = "3401"
    elif "415" in blob:
        definition = "415_safe_harbor"
    return definition, provenance_from(prov)


def extract_comp_exclusions(provisions: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    prov = semantic_best(
        provisions,
        "compensation exclusions",
        ["compensation", "exclusion"],
        USE_EMB,
        EMB_MODEL,
        title_keywords=["compensation"],
    )
    if not prov:
        return None
    return {"provenance": provenance_from(prov)}


def extract_loans(provisions: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    prov = semantic_best(
        provisions,
        "participant loans",
        ["loan"],
        USE_EMB,
        EMB_MODEL,
        title_keywords=["loan"],
    )
    if not prov:
        return None
    return {"enabled": True, "provenance": provenance_from(prov)}


def extract_in_service(provisions: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    prov = semantic_best(
        provisions,
        "in-service distribution",
        ["in-service", "in service"],
        USE_EMB,
        EMB_MODEL,
        title_keywords=["in-service", "in service"],
    )
    if not prov:
        return None
    blob = text_blob(prov)
    age = extract_int_in_range(blob, 50, 80)
    return {"age_threshold": age, "provenance": provenance_from(prov)}


def find_provenance_for_keywords(provisions: List[Dict[str, Any]], keywords: List[str]) -> Optional[Dict[str, Any]]:
    prov = semantic_best(provisions, " ".join(keywords), keywords, USE_EMB, EMB_MODEL)
    return provenance_from(prov) if prov else None


def build_canonical(doc_id: str, provisions: List[Dict[str, Any]]) -> Dict[str, Any]:
    report = {}
    plan: Dict[str, Any] = {
        "eligibility": {"age": {}, "service": {}, "entry_dates": {}},
        "retirement": {"normal_age": {}},
        "compensation": {"base_definition": {}, "exclusions": {}},
        "vesting": {"schedule": {}},
        "loans": {"enabled": None, "parameters": {}},
        "distributions": {"hardship": {}, "in_service": {}},
    }

    # eligibility.age
    age, age_prov = extract_eligibility_age(provisions)
    if age_prov:
        for src in ["deferrals", "match", "profit_sharing"]:
            plan["eligibility"]["age"][src] = {"value": age, "unit": "years", "provenance": age_prov}
    report["eligibility.age"] = "hit" if age_prov else "miss"

    # eligibility.service
    years, hours, serv_prov = extract_eligibility_service(provisions)
    if serv_prov:
        plan["eligibility"]["service"] = {
            "deferrals": {"years_required": years, "hours_required": hours, "provenance": serv_prov},
            "match": {"years_required": years, "hours_required": hours, "provenance": serv_prov},
            "profit_sharing": {"years_required": years, "hours_required": hours, "provenance": serv_prov},
        }
    report["eligibility.service"] = "hit" if serv_prov else "miss"

    # eligibility.entry_dates (provenance + pattern)
    entry_pattern, entry_prov = extract_entry_dates(provisions)
    if entry_prov:
        plan["eligibility"]["entry_dates"] = {
            "pattern": entry_pattern,
            "provenance": entry_prov,
        }
    report["eligibility.entry_dates"] = "hit" if entry_prov else "miss"

    # retirement.normal_age
    nra_age, nra_svc, nra_prov = extract_normal_retirement_age(provisions)
    if nra_prov:
        plan["retirement"]["normal_age"] = {"age": nra_age, "service_years": nra_svc, "provenance": nra_prov}
    report["retirement.normal_age"] = "hit" if nra_prov else "miss"

    # compensation.base_definition
    comp_def, comp_def_prov = extract_comp_base(provisions)
    if comp_def_prov:
        plan["compensation"]["base_definition"] = {"definition": comp_def, "provenance": comp_def_prov}
    report["compensation.base_definition"] = "hit" if comp_def_prov else "miss"

    # compensation.exclusions (provenance-only placeholder)
    comp_excl = extract_comp_exclusions(provisions)
    if comp_excl:
        plan["compensation"]["exclusions"] = comp_excl
    report["compensation.exclusions"] = "hit" if comp_excl else "miss"

    # vesting.schedule (provenance only for now)
    vest_prov = find_provenance_for_keywords(provisions, ["vesting"])
    if vest_prov:
        plan["vesting"]["schedule"] = {
            "match": {"provenance": vest_prov},
            "profit_sharing": {"provenance": vest_prov},
        }
    report["vesting.schedule"] = "hit" if vest_prov else "miss"

    # loans.enabled (provenance-only)
    loan_info = extract_loans(provisions)
    if loan_info:
        plan["loans"] = loan_info
    report["loans.enabled"] = "hit" if loan_info else "miss"

    # distributions.hardship (provenance only)
    hardship_prov = find_provenance_for_keywords(provisions, ["hardship"])
    if hardship_prov:
        plan["distributions"]["hardship"] = {
            "provenance": hardship_prov,
            "definition": None,
            "allowed_sources": None,
        }
    report["distributions.hardship"] = "hit" if hardship_prov else "miss"

    # distributions.in_service (provenance + optional age threshold)
    in_service = extract_in_service(provisions)
    if in_service:
        plan["distributions"]["in_service"] = in_service
    report["distributions.in_service"] = "hit" if in_service else "miss"

    return {"doc_id": doc_id, "plan": plan, "report": report}


def main():
    args = parse_args()
    provisions_path = Path(args.provisions)
    doc_id, provisions = load_provisions(provisions_path)
    if args.doc_id:
        doc_id = args.doc_id
    global USE_EMB, EMB_MODEL
    USE_EMB = args.use_openai_embeddings and openai is not None
    EMB_MODEL = args.openai_model
    if args.use_openai_embeddings and openai is None:
        print("WARNING: openai package not available; falling back to heuristic matching.")
    canonical = build_canonical(doc_id, provisions)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(canonical, indent=2))
    print(f"Wrote canonical draft to {out_path}")
    print("Report:", canonical.get("report"))


if __name__ == "__main__":
    main()
