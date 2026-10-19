"""Bridge teammate focused-crawler keywords into company search.

Uses the same EN/DE medical + general vocabulary as ``navigator.focused.keywords``
so company scoring/priority aligns with what the research crawler tags.
"""

from __future__ import annotations

from typing import Any

from navigator.focused.keywords import (
    GENERAL,
    MEDICAL,
    extract_keywords,
    keyword_priority,
    normalize,
)

# Bern-facing early themes (subset of MEDICAL) — queue these first.
BERN_EARLY_MEDICAL = {
    "diabetes",
    "type 1 diabetes",
    "type 2 diabetes",
    "endocrinology",
    "hypoglycemia",
    "obesity",
    "metabolic disease",
    "glucose",
    "glucose monitoring",
    "continuous glucose monitoring",
    "insulin",
    "insulin delivery",
    "automated insulin delivery",
    "biosensors",
    "wearable devices",
    "digital health",
    "patient monitoring",
    "clinical trials",
    "clinical research",
    "clinical validation",
}

BERN_MID_MEDICAL = {
    "medical devices",
    "biomedical engineering",
    "implants",
    "medical imaging",
    "diagnostics",
    "biomarkers",
    "molecular diagnostics",
    "surgical robotics",
    "image-guided therapy",
    "precision medicine",
    "regenerative medicine",
    "immunology",
    "oncology",
    "cardiology",
    "neurology",
}


def tag_text(text: str, title: str = "") -> dict[str, Any]:
    """Extract focused keywords and a 0–100 teammate-alignment score."""
    blob = f"{title}\n{text}".strip()
    if not blob:
        return {
            "keywords": [],
            "medical": [],
            "general": [],
            "early": [],
            "mid": [],
            "late": [],
            "link_bonus": 0,
            "score": 0.0,
            "hits": [],
        }

    keywords = extract_keywords(blob, title=title)
    medical = [k for k in keywords if k in MEDICAL]
    general = [k for k in keywords if k in GENERAL]
    early = [k for k in medical if k in BERN_EARLY_MEDICAL]
    mid = [k for k in medical if k not in early]
    late = list(general)

    # Score: medical density + early Bern themes + crawler link bonus
    link_bonus = keyword_priority(blob)  # 0–8
    early_pts = min(40.0, len(early) * 12.0)
    medical_pts = min(35.0, len(medical) * 5.0)
    general_pts = min(10.0, len(general) * 2.5)
    bonus_pts = min(15.0, link_bonus * 1.875)
    score = round(min(100.0, early_pts + medical_pts + general_pts + bonus_pts), 1)

    hits = [
        {
            "term": k,
            "tier": (
                "early" if k in early else "mid" if k in mid else "late" if k in late else "medical"
            ),
            "medical": k in MEDICAL,
        }
        for k in keywords
    ]

    return {
        "keywords": keywords,
        "medical": medical,
        "general": general,
        "early": early,
        "mid": mid,
        "late": late,
        "link_bonus": link_bonus,
        "score": score,
        "hits": hits,
    }


def annotate_company(company: dict[str, Any]) -> dict[str, Any]:
    """Attach focused_* fields and merge canonical labels into company keywords."""
    text = " ".join(
        [
            str(company.get("source_text") or ""),
            str(company.get("description") or ""),
            str(company.get("what_they_do") or ""),
            str(company.get("meta_description") or ""),
            " ".join(company.get("keywords") or []),
            " ".join(company.get("needs") or []),
            " ".join(company.get("medical_keywords") or []),
        ]
    )
    title = str(company.get("meta_title") or company.get("name") or "")
    tagged = tag_text(text, title=title)

    company["focused_keywords"] = tagged["keywords"]
    company["focused_medical_keywords"] = tagged["medical"]
    company["focused_early_keywords"] = tagged["early"]
    company["focused_mid_keywords"] = tagged["mid"]
    company["focused_keyword_score"] = tagged["score"]
    company["focused_keyword_hits"] = tagged["hits"]

    # Merge teammate-canonical labels into the public keyword list (front).
    merged = list(
        dict.fromkeys([*tagged["early"], *tagged["medical"], *(company.get("keywords") or [])])
    )
    company["keywords"] = merged[:24]
    return company


def focused_score_ratio(company: dict[str, Any]) -> float:
    """0–1 ratio used by collaboration scoring."""
    raw = company.get("focused_keyword_score")
    if raw is None:
        tagged = tag_text(
            " ".join(
                [
                    str(company.get("description") or ""),
                    str(company.get("what_they_do") or ""),
                    " ".join(company.get("keywords") or []),
                ]
            ),
            title=str(company.get("name") or ""),
        )
        raw = tagged["score"]
        company.setdefault("focused_keywords", tagged["keywords"])
        company.setdefault("focused_medical_keywords", tagged["medical"])
        company.setdefault("focused_early_keywords", tagged["early"])
        company["focused_keyword_score"] = raw
    return min(1.0, float(raw) / 100.0)


def vocabulary_summary() -> dict[str, Any]:
    """Expose teammate keyword counts for UI / CLI."""
    return {
        "medical_labels": len(MEDICAL),
        "general_labels": len(GENERAL),
        "bern_early": sorted(BERN_EARLY_MEDICAL),
        "bern_mid_sample": sorted(BERN_MID_MEDICAL),
        "source": "navigator.focused.keywords",
    }


__all__ = [
    "BERN_EARLY_MEDICAL",
    "BERN_MID_MEDICAL",
    "annotate_company",
    "focused_score_ratio",
    "normalize",
    "tag_text",
    "vocabulary_summary",
]
