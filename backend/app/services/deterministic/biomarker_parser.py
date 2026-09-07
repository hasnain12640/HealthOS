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

# Canonical defaults exposed for manual entry auto-fill.
# Values are general adult reference ranges; labs may use their own.
BIOMARKER_DEFAULTS: dict[str, dict] = {
    "Hemoglobin":            {"category": "CBC",        "unit": "g/dL",   "reference_low": 13.0,  "reference_high": 17.0},
    "WBC Count":             {"category": "CBC",        "unit": "/µL",    "reference_low": 4000.0,"reference_high": 11000.0},
    "Platelets":             {"category": "CBC",        "unit": "/µL",    "reference_low": 150000.0,"reference_high": 400000.0},
    "Hematocrit (PCV)":      {"category": "CBC",        "unit": "%",      "reference_low": 38.0,  "reference_high": 50.0},
    "MCV":                   {"category": "CBC",        "unit": "fL",     "reference_low": 80.0,  "reference_high": 100.0},
    "MCH":                   {"category": "CBC",        "unit": "pg",     "reference_low": 27.0,  "reference_high": 33.0},
    "Fasting Blood Glucose": {"category": "metabolic",  "unit": "mg/dL",  "reference_low": 70.0,  "reference_high": 100.0},
    "Creatinine":            {"category": "metabolic",  "unit": "mg/dL",  "reference_low": 0.7,   "reference_high": 1.2},
    "Urea (BUN)":            {"category": "metabolic",  "unit": "mg/dL",  "reference_low": 7.0,   "reference_high": 20.0},
    "Uric Acid":             {"category": "metabolic",  "unit": "mg/dL",  "reference_low": 3.5,   "reference_high": 7.2},
    "SGPT (ALT)":            {"category": "metabolic",  "unit": "U/L",    "reference_low": 7.0,   "reference_high": 56.0},
    "SGOT (AST)":            {"category": "metabolic",  "unit": "U/L",    "reference_low": 10.0,  "reference_high": 40.0},
    "Total Cholesterol":     {"category": "lipid",      "unit": "mg/dL",  "reference_low": None,  "reference_high": 200.0},
    "HDL Cholesterol":       {"category": "lipid",      "unit": "mg/dL",  "reference_low": 40.0,  "reference_high": None},
    "LDL Cholesterol":       {"category": "lipid",      "unit": "mg/dL",  "reference_low": None,  "reference_high": 100.0},
    "Triglycerides":         {"category": "lipid",      "unit": "mg/dL",  "reference_low": None,  "reference_high": 150.0},
    "TSH":                   {"category": "thyroid",    "unit": "mIU/L",  "reference_low": 0.4,   "reference_high": 4.0},
    "Vitamin D (25-OH)":     {"category": "vitamin",    "unit": "ng/mL",  "reference_low": 30.0,  "reference_high": 100.0},
    "Vitamin B12":           {"category": "vitamin",    "unit": "pg/mL",  "reference_low": 200.0, "reference_high": 900.0},
    "Ferritin":              {"category": "vitamin",    "unit": "ng/mL",  "reference_low": 12.0,  "reference_high": 300.0},
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
