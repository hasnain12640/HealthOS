"""
Biomarker parser — converts raw lab report text into structured biomarker records.

Architecture principle: this is entirely deterministic.
Status (normal/low/high/critical) is assigned here, never by AI.

Parsing strategy:
  Lines follow the pattern: TEST NAME  VALUE  UNIT  REFERENCE_RANGE  FLAG
  The parser works backwards from the end of the line (FLAG, then RANGE, then UNIT,
  then VALUE) because test names may contain spaces.
"""
import re
import uuid
from typing import Optional
from app.services.deterministic.health_calculations import assess_biomarker_status

BIOMARKER_CATALOG: dict[str, dict] = {
    "hemoglobin":            {"canonical": "Hemoglobin",            "category": "CBC"},
    "hgb":                   {"canonical": "Hemoglobin",            "category": "CBC"},
    "wbc count":             {"canonical": "WBC Count",             "category": "CBC"},
    "wbc":                   {"canonical": "WBC Count",             "category": "CBC"},
    "platelets":             {"canonical": "Platelets",             "category": "CBC"},
    "platelet count":        {"canonical": "Platelets",             "category": "CBC"},
    "hematocrit (pcv)":      {"canonical": "Hematocrit (PCV)",      "category": "CBC"},
    "hematocrit":            {"canonical": "Hematocrit (PCV)",      "category": "CBC"},
    "pcv":                   {"canonical": "Hematocrit (PCV)",      "category": "CBC"},
    "mcv":                   {"canonical": "MCV",                   "category": "CBC"},
    "mch":                   {"canonical": "MCH",                   "category": "CBC"},
    "fasting blood glucose": {"canonical": "Fasting Blood Glucose", "category": "metabolic"},
    "fasting glucose":       {"canonical": "Fasting Blood Glucose", "category": "metabolic"},
    "blood glucose":         {"canonical": "Fasting Blood Glucose", "category": "metabolic"},
    "glucose":               {"canonical": "Fasting Blood Glucose", "category": "metabolic"},
    "creatinine":            {"canonical": "Creatinine",            "category": "metabolic"},
    "urea (bun)":            {"canonical": "Urea (BUN)",            "category": "metabolic"},
    "urea":                  {"canonical": "Urea (BUN)",            "category": "metabolic"},
    "bun":                   {"canonical": "Urea (BUN)",            "category": "metabolic"},
    "uric acid":             {"canonical": "Uric Acid",             "category": "metabolic"},
    "sgpt (alt)":            {"canonical": "SGPT (ALT)",            "category": "metabolic"},
    "sgpt":                  {"canonical": "SGPT (ALT)",            "category": "metabolic"},
    "alt":                   {"canonical": "SGPT (ALT)",            "category": "metabolic"},
    "sgot (ast)":            {"canonical": "SGOT (AST)",            "category": "metabolic"},
    "sgot":                  {"canonical": "SGOT (AST)",            "category": "metabolic"},
    "ast":                   {"canonical": "SGOT (AST)",            "category": "metabolic"},
    "total cholesterol":     {"canonical": "Total Cholesterol",     "category": "lipid"},
    "cholesterol":           {"canonical": "Total Cholesterol",     "category": "lipid"},
    "hdl cholesterol":       {"canonical": "HDL Cholesterol",       "category": "lipid"},
    "hdl":                   {"canonical": "HDL Cholesterol",       "category": "lipid"},
    "ldl cholesterol":       {"canonical": "LDL Cholesterol",       "category": "lipid"},
    "ldl":                   {"canonical": "LDL Cholesterol",       "category": "lipid"},
    "triglycerides":         {"canonical": "Triglycerides",         "category": "lipid"},
    "tsh":                   {"canonical": "TSH",                   "category": "thyroid"},
    "vitamin d (25-oh)":     {"canonical": "Vitamin D (25-OH)",     "category": "vitamin"},
    "vitamin d":             {"canonical": "Vitamin D (25-OH)",     "category": "vitamin"},
    "25-oh":                 {"canonical": "Vitamin D (25-OH)",     "category": "vitamin"},
    "vitamin b12":           {"canonical": "Vitamin B12",           "category": "vitamin"},
    "b12":                   {"canonical": "Vitamin B12",           "category": "vitamin"},
    "ferritin":              {"canonical": "Ferritin",              "category": "vitamin"},
}

# Pattern parsed right-to-left from end of line:
# Captures: [everything before result]  result  unit  ref_range  [flag]
# ref_range forms: "13.0 - 17.0"  |  "< 200"  |  "> 40"  |  "0 - 40"
LINE_RE = re.compile(
    r"^(.+?)\s+"                                              # test name (greedy, trimmed below)
    r"([\d,]+\.?\d*)\s+"                                      # numeric result
    r"(\S+)\s+"                                               # unit (no spaces)
    r"(<\s*[\d.]+|>\s*[\d.]+|[\d.]+\s*-\s*[\d.]+)\s*"       # reference range
    r"([LHN])?\s*$",                                          # optional flag
    re.IGNORECASE,
)


def _parse_numeric(s: str) -> Optional[float]:
    try:
        return float(s.replace(",", ""))
    except (ValueError, TypeError):
        return None


def _parse_reference_range(s: str) -> tuple[Optional[float], Optional[float]]:
    s = s.strip()
    lt = re.match(r"<\s*([\d.]+)", s)
    if lt:
        return None, float(lt.group(1))
    gt = re.match(r">\s*([\d.]+)", s)
    if gt:
        return float(gt.group(1)), None
    rng = re.match(r"([\d.]+)\s*-\s*([\d.]+)", s)
    if rng:
        return float(rng.group(1)), float(rng.group(2))
    return None, None


def _flag_to_status(flag: str) -> str:
    return {"l": "low", "h": "high", "n": "normal"}.get(flag.lower(), "normal")


def _lookup(name: str) -> Optional[dict]:
    """Try exact match, then longest-prefix match against catalog keys."""
    key = name.lower().strip()
    if key in BIOMARKER_CATALOG:
        return BIOMARKER_CATALOG[key]
    # Longest matching prefix
    best = None
    best_len = 0
    for catalog_key in BIOMARKER_CATALOG:
        if key.startswith(catalog_key) and len(catalog_key) > best_len:
            best = BIOMARKER_CATALOG[catalog_key]
            best_len = len(catalog_key)
    return best


def parse_biomarkers(raw_text: str, report_id: str) -> list[dict]:
    seen: set[str] = set()
    biomarkers: list[dict] = []

    for line in raw_text.splitlines():
        line = line.strip()
        if not line or line.lower().startswith("test name"):
            continue

        m = LINE_RE.match(line)
        if not m:
            continue

        raw_name, raw_value, unit, ref_range_str, flag = m.groups()

        catalog = _lookup(raw_name)
        if not catalog:
            continue

        canonical = catalog["canonical"]
        if canonical in seen:
            continue
        seen.add(canonical)

        value = _parse_numeric(raw_value)
        if value is None:
            continue

        ref_low, ref_high = _parse_reference_range(ref_range_str)

        status = _flag_to_status(flag) if flag else assess_biomarker_status(value, ref_low, ref_high)

        biomarkers.append({
            "id": str(uuid.uuid4()),
            "report_id": report_id,
            "name": canonical,
            "value": value,
            "unit": unit,
            "reference_low": ref_low,
            "reference_high": ref_high,
            "status": status,
            "category": catalog["category"],
        })

    return biomarkers
